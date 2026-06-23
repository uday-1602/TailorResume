"""
TailorResume — FastAPI Backend
Wraps the existing LangGraph recruitement_graph pipeline.

Run from TailorResume/ root:
    uvicorn backend.main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Make parent directory importable so we can import the graph modules and backend package
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import asyncio
import json
import os
import shutil
import threading
import uuid
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel
from backend.s3_storage import s3_storage

from recruitement_graph import agent, RecruiterGraphState  # noqa: E402


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="TailorResume API", version="1.0.0")

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins.extend([o.strip() for o in allowed_origins_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory job store  {job_id: JobRecord}
# ---------------------------------------------------------------------------
_JOBS: Dict[str, "JobRecord"] = {}
_JOBS_LOCK = threading.Lock()

JOBS_DIR = ROOT / ".jobs"
JOBS_DIR.mkdir(exist_ok=True)


class JobRecord:
    def __init__(self, job_id: str, resume_path: str, job_file: str, job_url: Optional[str] = None, template: str = "default"):
        self.job_id = job_id
        self.resume_path = resume_path
        self.job_file = job_file
        self.job_url = job_url
        self.template = template
        self.thread_config = {"configurable": {"thread_id": job_id}}

        self.events: list[dict] = []          # SSE event queue
        self.event_ready = asyncio.Event()     # signals new events
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self.interview_questions: list[str] = []
        self.answers_ready = threading.Event()
        self.user_answers: dict = {}

        self.pdf_path: Optional[str] = None
        self.s3_key: Optional[str] = None
        self.error: Optional[str] = None
        self.done = False

    # Called from background thread — safe because it schedules a coroutine
    def push_event(self, event: dict):
        self.events.append(event)
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self.event_ready.set)


# ---------------------------------------------------------------------------
# Background pipeline runner (runs in a thread so it doesn't block async loop)
# ---------------------------------------------------------------------------
def _run_pipeline(record: JobRecord):
    current_node = "job_scraper"
    try:
        initial_state: Dict[str, Any] = {
            "resume_path": record.resume_path,
            "job_url": record.job_url or "",
            "fallback_job_file": record.job_file,
            "template": record.template,
            "user_answers": {},
        }

        # --- Phase 1: run up to the human_input breakpoint ---
        record.push_event({"type": "node_start", "node": "profile_analyzer", "label": "Profile Analyzer"})
        record.push_event({"type": "node_start", "node": "job_scraper",       "label": "Job Scraper"})

        for event in agent.stream(initial_state, config=record.thread_config, stream_mode="values"):
            # Inspect what just completed
            snapshot = agent.get_state(record.thread_config)
            completed = set()
            for k, v in (event or {}).items():
                _ = k  # suppress unused warning

            # Derive completed nodes by checking state presence
            state_vals = snapshot.values
            if state_vals.get("candidate_profile") and _node_not_yet_reported(record, "profile_analyzer"):
                record.push_event({"type": "node_done", "node": "profile_analyzer"})
                record.push_event({"type": "node_done", "node": "job_scraper"})
                current_node = "gap_analyzer"
                record.push_event({"type": "node_start", "node": "gap_analyzer", "label": "Gap Analyzer"})

            if state_vals.get("gap_analysis_report") and _node_not_yet_reported(record, "gap_analyzer"):
                record.push_event({"type": "node_done", "node": "gap_analyzer"})
                current_node = "interviewer"
                record.push_event({"type": "node_start", "node": "interviewer", "label": "Generating Questions"})

            if state_vals.get("interview_questions") and _node_not_yet_reported(record, "interviewer"):
                questions = state_vals["interview_questions"]
                record.interview_questions = questions
                # Signal the UI to show chatbot — DON'T mark done yet
                record.push_event({
                    "type": "interview_questions",
                    "questions": questions,
                })

        # --- Phase 2: wait for user answers ---
        answered = record.answers_ready.wait(timeout=3600)  # 1-hour timeout
        if not answered:
            raise TimeoutError("Chatbot interview session timed out after 60 minutes.")

        # --- Phase 3: inject answers and resume ---
        record.push_event({"type": "node_done",  "node": "interviewer"})
        current_node = "resume_rewriter"
        record.push_event({"type": "node_start", "node": "resume_rewriter", "label": "Resume Rewriter"})

        agent.update_state(
            record.thread_config,
            {"user_answers": record.user_answers},
            as_node="human_input",
        )

        for _ in agent.stream(None, config=record.thread_config, stream_mode="values"):
            pass

        # --- Done ---
        snapshot = agent.get_state(record.thread_config)
        pdf_path = Path(record.resume_path).parent / "tailored_resume.pdf"
        if pdf_path.exists():
            if s3_storage.active:
                s3_key = f"guests/{record.job_id}.pdf"
                success = s3_storage.upload_file(str(pdf_path), s3_key)
                if success:
                    record.s3_key = s3_key
                    # Purge local workspace folder completely (with retries for Windows file locks)
                    import time
                    purged = False
                    for attempt in range(5):
                        try:
                            shutil.rmtree(os.path.dirname(record.resume_path))
                            purged = True
                            break
                        except Exception:
                            time.sleep(0.5)
                    if not purged:
                        print(f"[CLEANUP] Failed to purge local workspace folder after 5 attempts.")
                else:
                    # Fallback to local copy if upload fails
                    dest = JOBS_DIR / f"{record.job_id}.pdf"
                    shutil.copy(pdf_path, dest)
                    record.pdf_path = str(dest)
            else:
                dest = JOBS_DIR / f"{record.job_id}.pdf"
                shutil.copy(pdf_path, dest)
                record.pdf_path = str(dest)

        record.push_event({"type": "node_done", "node": "resume_rewriter"})
        record.push_event({"type": "complete"})
        record.done = True

    except Exception as exc:
        record.push_event({
            "type": "node_error",
            "node": current_node,
            "message": str(exc),
        })
        record.error = str(exc)
        record.done = True


def _node_not_yet_reported(record: JobRecord, node_id: str) -> bool:
    """Returns True if we haven't sent a node_done for this node yet."""
    for e in record.events:
        if e.get("type") == "node_done" and e.get("node") == node_id:
            return False
    return True


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

class AnswersPayload(BaseModel):
    answers: Dict[str, str]


@app.post("/api/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    resume: UploadFile = File(...),
    job_url: Optional[str] = Form(None),
    job_text: Optional[str] = Form(None),
    template: str = Form("default"),
):
    """Accept resume file + job description, kick off the LangGraph pipeline."""
    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Save resume
    resume_path = str(job_dir / resume.filename)
    with open(resume_path, "wb") as f:
        content = await resume.read()
        f.write(content)
    await resume.close()

    # Save job description
    job_file = str(job_dir / "job_description.txt")
    if job_text and len(job_text.strip()) > 10:
        with open(job_file, "w", encoding="utf-8") as f:
            f.write(job_text)
    elif job_url and len(job_url.strip()) > 5:
        # Write the URL — the scrape_job.py module will fetch it
        with open(job_file, "w", encoding="utf-8") as f:
            f.write(job_url.strip())
    else:
        raise HTTPException(status_code=400, detail="Provide either job_url or job_text")

    record = JobRecord(
        job_id=job_id,
        resume_path=resume_path,
        job_file=job_file,
        job_url=job_url.strip() if job_url else None,
        template=template,
    )

    with _JOBS_LOCK:
        _JOBS[job_id] = record

    # Run pipeline in a background thread (LangGraph is sync)
    loop = asyncio.get_event_loop()
    record._loop = loop
    thread = threading.Thread(target=_run_pipeline, args=(record,), daemon=True)
    thread.start()

    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def stream_status(job_id: str):
    """SSE stream — yields pipeline node events as they happen."""
    with _JOBS_LOCK:
        record = _JOBS.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")

    loop = asyncio.get_event_loop()
    record._loop = loop

    async def event_generator():
        sent_idx = 0
        while True:
            # Drain any buffered events
            while sent_idx < len(record.events):
                evt = record.events[sent_idx]
                sent_idx += 1
                yield f"data: {json.dumps(evt)}\n\n"

            if record.done and sent_idx >= len(record.events):
                break

            # Wait for new events
            record.event_ready.clear()
            try:
                await asyncio.wait_for(record.event_ready.wait(), timeout=30)
            except asyncio.TimeoutError:
                yield "data: {\"type\":\"ping\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/answers/{job_id}")
async def submit_answers(job_id: str, payload: AnswersPayload):
    """Receive chatbot answers, resume the pipeline from the breakpoint."""
    with _JOBS_LOCK:
        record = _JOBS.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")

    record.user_answers = payload.answers
    record.answers_ready.set()

    return {"status": "ok"}


@app.get("/api/download/{job_id}")
async def download_pdf(job_id: str, download: bool = False):
    """Serve the compiled tailored_resume.pdf for a given job."""
    with _JOBS_LOCK:
        record = _JOBS.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if getattr(record, "s3_key", None):
        try:
            # Stream directly from S3 to avoid CORS issues in the frontend PDF canvas viewer
            s3_client = s3_storage.client
            bucket = s3_storage.bucket_name
            obj = s3_client.get_object(Bucket=bucket, Key=record.s3_key)
            
            disposition = "attachment" if download else "inline"
            return StreamingResponse(
                obj["Body"],
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'{disposition}; filename="tailored_resume.pdf"'
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"S3 download failed: {e}")

    if not record.pdf_path or not os.path.exists(record.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not yet generated")

    disposition = "attachment" if download else "inline"
    return FileResponse(
        record.pdf_path,
        media_type="application/pdf",
        filename="tailored_resume.pdf",
        content_disposition_type=disposition,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "jobs": len(_JOBS)}

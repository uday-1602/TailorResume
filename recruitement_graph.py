import os
import re
import json
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import tarfile
import requests

#function import
from parse_profile import profile_extraction
from scrape_job import job_extraction
from analyze_gap import gap_analysis
from interactive_agent import generate_targeted_interview_questions
from rewrite_resume import execute_resume_rewrite

load_dotenv()

class RecruiterGraphState(TypedDict):
    """
    The central data channel for the graph. Every node receives a copy
    of this state and returns keys to update it values dynamically.
    """
    resume_path: str
    job_url: Optional[str]          # Live job posting URL; falls back to fallback_job_file if empty
    fallback_job_file: str
    template: str                   # "default" (LaTeX/classic) or "modern" (HTML/WeasyPrint)
    candidate_profile: Dict[str, Any]
    job_specifications: Dict[str, Any]
    gap_analysis_report: Dict[str, Any]
    alignment_score: int            # Surfaced from gap_analysis_report for clean observability
    interview_questions: List[str]
    user_answers: Dict[str, str]
    final_latex_source: str

def profile_analyzer_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> profile analyzer node processing...")
    profile_data = profile_extraction(state["resume_path"])
    return {"candidate_profile": profile_data}

def job_scraper_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> job scraper node processing...")
    live_url = state.get("job_url") or None
    job_data = job_extraction(url=live_url, fallback_file=state["fallback_job_file"])
    return {"job_specifications": job_data}

def gap_analyzer_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> gap analyzer node processing...")
    report_data = gap_analysis(
        state["candidate_profile"],
        state["job_specifications"]
    )
    score = report_data.get("alignment_score_percentage", 0)
    print(f"[GAP ANALYZER] Alignment score: {score}%")
    return {"gap_analysis_report": report_data, "alignment_score": score}

def interviewer_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> interviewer node processing...")
    raw_questions = generate_targeted_interview_questions(
        state["candidate_profile"],
        state["gap_analysis_report"]
    )

    questions_list = list(raw_questions)
    
    # Check for missing contact details
    profile = state.get("candidate_profile", {})
    github = (profile.get("github_handle") or "").strip()
    linkedin = (profile.get("linkedin_handle") or "").strip()
    
    extra_questions = []
    if not github or github.lower() in ("n/a", "none", ""):
        extra_questions.append(
            "Your GitHub profile link is missing. Would you like to provide it? (Optional - type 'skip' or leave blank to skip)"
        )
    if not linkedin or linkedin.lower() in ("n/a", "none", ""):
        extra_questions.append(
            "Your LinkedIn profile link is missing. Would you like to provide it? (Optional - type 'skip' or leave blank to skip)"
        )
        
    # Prepend optional contact questions so they run first
    questions_list = extra_questions + questions_list

    questions_list.append(
        "Do you have any relevant technical certifications, professional activities, or awards you want to include, or should I explicitly remove those placeholder sections?"
    )

    return {"interview_questions": questions_list}

def _calculate_page_limit(profile: Dict[str, Any], threshold_years: int = 5) -> int:
    """
    Estimates total professional experience from duration strings in the candidate profile.
    Returns page_limit=2 if total experience >= threshold_years, else page_limit=1.
    """
    experiences = profile.get("professional_experience", [])
    total_months = 0
    now = datetime.now()

    month_abbr = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    def _parse_date(s: str):
        s = s.strip().lower()
        if s in ("present", "current", "now", "ongoing", "till date", "to date"):
            return now
        m = re.match(r"([a-z]+)[\s.\-]+(\d{4})", s)
        if m:
            month = month_abbr.get(m.group(1)[:3])
            if month:
                return datetime(int(m.group(2)), month, 1)
        m = re.match(r"^(\d{4})$", s.strip())
        if m:
            return datetime(int(m.group(1)), 6, 1)  # assume mid-year
        return None

    for exp in experiences:
        duration = (exp.get("duration") or "").strip()
        if not duration:
            continue
        # Split on common range separators: –, —, -, or " to "
        parts = re.split(r"\s*[–—]\s*|\s+to\s+|\s*-\s*", duration, maxsplit=1)
        if len(parts) == 2:
            start = _parse_date(parts[0])
            end = _parse_date(parts[1])
            if start and end and end >= start:
                months = (end.year - start.year) * 12 + (end.month - start.month)
                total_months += months

    total_years = total_months / 12
    page_limit = 2 if total_years >= threshold_years else 1
    print(f"[PAGE BUDGET] Detected {total_years:.1f} years of experience -> page_limit={page_limit}")
    return page_limit


def human_input_node(state: RecruiterGraphState) -> Dict[str, Any]:
    """
    This node serves as the compilation anchor for our breakpoint.
    The graph stops IMMEDIATELY BEFORE this node fires. When we resume the thread,
    we inject the terminal text directly into the graph state.
    """
    print("\n[LANGGRAPH NODE] ---> human input node processing input payload context...")
    return {}

def resume_rewriter_node(state: RecruiterGraphState) -> Dict[str, Any]:
    template = state.get("template", "default")
    print(f"\n[LANGGRAPH NODE] ---> resume_rewriter_node | template={template}")
    print(f"[REWRITER] Working with alignment score: {state.get('alignment_score', 'N/A')}%")

    resume_dir = os.path.dirname(state["resume_path"])
    pdf_filename = os.path.join(resume_dir, "tailored_resume.pdf")

    # Remove any stale PDF from a prior run
    if os.path.exists(pdf_filename):
        try:
            os.remove(pdf_filename)
        except Exception:
            pass

    # Extract dynamic github/linkedin answers from user responses if they exist
    user_answers = state.get("user_answers", {})
    candidate_profile = dict(state.get("candidate_profile", {}))
    
    for q, ans in user_answers.items():
        ans_clean = ans.strip()
        if not ans_clean or ans_clean.lower() in ("skip", "n/a", "none", "omit parameter."):
            continue
        if "github" in q.lower():
            candidate_profile["github_handle"] = ans_clean
        elif "linkedin" in q.lower():
            candidate_profile["linkedin_handle"] = ans_clean

    # Calculate dynamic page limit based on total professional experience (5-year threshold)
    page_limit = _calculate_page_limit(candidate_profile)

    # ── Modern template: HTML → WeasyPrint PDF ────────────────────────────────
    if template == "modern":
        from backend.templates.modern import execute_resume_rewrite_modern
        content = execute_resume_rewrite_modern(
            original_profile=candidate_profile,
            job_spec=state["job_specifications"],
            gap_report=state["gap_analysis_report"],
            user_answers=state["user_answers"],
            output_pdf_path=pdf_filename,
            page_limit=page_limit,
        )
        return {"final_latex_source": content}

    # ── Classic template: LLM → LaTeX → latexonline.cc PDF ───────────────────
    latex_code = execute_resume_rewrite(
        original_profile=candidate_profile,
        job_spec=state["job_specifications"],
        gap_report=state["gap_analysis_report"],
        user_answers=state["user_answers"],
        page_limit=page_limit
    )

    tex_filename = os.path.join(resume_dir, "tailored_resume.tex")
    tar_filename = os.path.join(resume_dir, "payload.tar.bz2")

    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(latex_code)
    print(f"[FILE OUT] LaTeX source code written to: {os.path.abspath(tex_filename)}")

    print("\n[COMPILER] Packing LaTeX file into a compressed stream...")
    with tarfile.open(tar_filename, "w:bz2") as tar:
        tar.add(tex_filename, arcname="tailored_resume.tex")

    print("[COMPILER] Sending payload to the cloud compiler API (5-10 seconds)...")
    api_url = "https://latexonline.cc/data?target=tailored_resume.tex&command=pdflatex"

    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _compile_pdf():
        with open(tar_filename, "rb") as packed_file:
            resp = requests.post(api_url, files={"file": packed_file}, timeout=30)
            resp.raise_for_status()
            return resp

    try:
        response = _compile_pdf()
        with open(pdf_filename, "wb") as pdf_file:
            pdf_file.write(response.content)
        print(f"\nSUCCESS! 1-page PDF '{pdf_filename}' generated via cloud API!")
    except Exception as e:
        print(f"\nERROR: Cloud compilation failed: {str(e)}")
        raise e
    finally:
        if os.path.exists(tar_filename):
            os.remove(tar_filename)

    return {"final_latex_source": latex_code}

tailor = StateGraph(RecruiterGraphState)

tailor.add_node("profile_analyzer", profile_analyzer_node)
tailor.add_node("job_scraper", job_scraper_node)
tailor.add_node("gap_analyzer", gap_analyzer_node)
tailor.add_node("interviewer", interviewer_node)
tailor.add_node("human_input", human_input_node)
tailor.add_node("resume_rewriter", resume_rewriter_node)


tailor.add_edge(START, "profile_analyzer")
tailor.add_edge(START, "job_scraper")

tailor.add_edge("profile_analyzer", "gap_analyzer")
tailor.add_edge("job_scraper", "gap_analyzer")
tailor.add_edge("gap_analyzer", "interviewer")
tailor.add_edge("interviewer", "human_input")
tailor.add_edge("human_input", "resume_rewriter")
tailor.add_edge("resume_rewriter", END)

memory_saver = MemorySaver()

agent = tailor.compile(
    checkpointer=memory_saver,
    interrupt_before=["human_input"]
)

if __name__ == "__main__":
    THREAD_CONFIG = {"configurable": {"thread_id": "uday_final_one_page_session"}}

    # Set job_url to a live posting URL to enable live scraping.
    # Leave as empty string "" to fall back to job_description.txt.
    initial_state_inputs = {
        "resume_path": "resume.pdf",
        "job_url": "",
        "fallback_job_file": "job_description.txt",
        "template": "default",
        "user_answers": {}
    }

    print("[INIT] Launching parallel graph streams...")
    for event in agent.stream(initial_state_inputs, config=THREAD_CONFIG, stream_mode="values"):
        pass

    graph_snapshot = agent.get_state(THREAD_CONFIG)
    
    if "human_input" in graph_snapshot.next:
        print("\n" + "!" * 20 + " NATIVE LANGGRAPH BREAKPOINT REACHED " + "!" * 20)
        generated_questions = graph_snapshot.values.get("interview_questions", [])
        collected_responses = {}
        
        print("\nPlease address the discovery queries below to satisfy ATS conditions:")
        for idx, question in enumerate(generated_questions, 1):
            print(f"\n[{idx}/{len(generated_questions)}] {question}")
            user_input = input(">>> Your Answer: ").strip()
            if not user_input:
                user_input = "Omit parameter."
            collected_responses[question] = user_input
            
        print("\n" + "!" * 77)
        
        # Inject answers back into the state machine thread channel
        agent.update_state(
            THREAD_CONFIG,
            {"user_answers": collected_responses},
            as_node="human_input"
        )
        
        print("[STREAM] Resuming graph pipeline to build final document structures...")
        for event in agent.stream(None, config=THREAD_CONFIG, stream_mode="values"):
            pass
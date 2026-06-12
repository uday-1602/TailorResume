import os
import json
from typing import Dict, Any, List, TypedDict
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
    fallback_job_file: str
    candidate_profile: Dict[str, Any]
    job_specifications: Dict[str, Any]
    gap_analysis_report: Dict[str, Any]
    interview_questions: List[str]
    user_answers: Dict[str, str]
    final_latex_source: str

def profile_analyzer_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> profile analyzer node processing...")
    profile_data = profile_extraction(state["resume_path"])
    return {"candidate_profile": profile_data}

def job_scraper_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> job scraper node processing...")
    job_data = job_extraction(url=None, fallback_file=state["fallback_job_file"])
    return {"job_specifications": job_data}

def gap_analyzer_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> gap analyzer node processing...")
    report_data = gap_analysis(
        state["candidate_profile"],
        state["job_specifications"]
    )
    return {"gap_analysis_report": report_data}

def interviewer_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> interviewer node processing...")
    raw_questions = generate_targeted_interview_questions(
        state["candidate_profile"],
        state["gap_analysis_report"]
    )

    questions_list = list(raw_questions)
    questions_list.append(
        "Do you have any relevant technical certifications, professional activities, or awards you want to include, or should I explicitly remove those placeholder sections?"
    )

    return {"interview_questions": questions_list}

def human_input_node(state: RecruiterGraphState) -> Dict[str, Any]:
    """
    This node serves as the compilation anchor for our breakpoint.
    The graph stops IMMEDIATELY BEFORE this node fires. When we resume the thread,
    we inject the terminal text directly into the graph state.
    """
    print("\n[LANGGRAPH NODE] ---> human input node processing input payload context...")
    return {}

def resume_rewriter_node(state: RecruiterGraphState) -> Dict[str, Any]:
    print("\n[LANGGRAPH NODE] ---> resume_rewriter_node compiling 1-page LaTeX code...")
    
    latex_code = execute_resume_rewrite(
        original_profile=state["candidate_profile"],
        job_spec=state["job_specifications"],
        user_answers=state["user_answers"]
    )
    
    tex_filename = "tailored_resume.tex"
    tar_filename = "payload.tar.bz2"
    pdf_filename = "tailored_resume.pdf"
    
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(latex_code)
    print(f"[FILE OUT] LaTeX source code written to: {os.path.abspath(tex_filename)}")
   
    print("\n[COMPILER] Packing LaTeX file into a compressed stream...")
    with tarfile.open(tar_filename, "w:bz2") as tar:
        tar.add(tex_filename)

    print("[COMPILER] Sending payload to the cloud compiler API (5-10 seconds)...")
    api_url = f"https://latexonline.cc/data?target={tex_filename}&command=pdflatex"
    
    try:
        with open(tar_filename, "rb") as packed_file:
            response = requests.post(api_url, files={"file": packed_file})
            
        if response.status_code == 200:
            with open(pdf_filename, "wb") as pdf_file:
                pdf_file.write(response.content)
            print(f"\n🎉 SUCCESS! Ultra-dense 1-page '{pdf_filename}' has been generated via cloud API!")
        else:
            print(f"\n❌ Cloud compilation failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Network error during PDF compilation: {str(e)}")
        
    finally:
        # Automatically clean up the temporary workspace archive file
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
    initial_state_inputs = {
        "resume_path": "resume.pdf",
        "fallback_job_file": "job_description.txt",
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
            collected_responses[f"q{idx}"] = user_input
            
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
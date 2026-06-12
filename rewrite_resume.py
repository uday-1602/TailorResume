import os
from typing import Dict, Any, List
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import json

load_dotenv()

def execute_resume_rewrite(original_profile: Dict[str, Any], job_spec: Dict[str, Any], user_answers: Dict[str, str]) -> str:
    """
    Consumes candidate data, target job specifications, and conversational answers.
    Generates a flawless, high-density, strict 1-page LaTeX document using real contact data.
    """
    print("\n[NODE] ---> Executing 1-Page Calibrated LaTeX Engine...")

    llm = init_chat_model(
        model="openai/gpt-oss-120b",
        model_provider="groq",
        temperature=0.1
    )

    # Strict structural rules to enforce factual binding and 1-page layout tight scaling
    sys_instruction = (
        "You are an elite enterprise technical resume architect. Your mission is to rewrite the "
        "candidate's background into a highly polished, single-page optimized LaTeX document.\n\n"
        "STRICT CONTACT & FACTUAL BINDING RULES:\n"
        "1. Extract and use the ACTUAL full name, phone number, email, and GitHub/LinkedIn usernames from the "
        "   provided CANDIDATE PROFILE DATA. Do NOT use fake placeholders like 'example@example.com' or '123-456-7890'.\n"
        "2. You MUST include the candidate's Education details (University, Degree, Timeline) directly from the input data.\n"
        "3. If an experience block lacks a clear company name, do NOT write 'Not Specified'. Instead, use a professional, "
        "   clean descriptor like 'AI Research & Engineering Group' or 'Enterprise Technology Practicum'.\n"
        "4. Do not output floating years or empty separation rows without valid content blocks attached to them.\n\n"
        "STRICT ONE-PAGE BUDGET & FORMATTING RULES:\n"
        "1. Start directly with '\\documentclass[10pt,letterpaper]{article}' and terminate with '\\end{document}'. No markdown code blocks.\n"
        "2. Set narrow page geometry: use '\\usepackage[margin=0.45in]{geometry}' to maximize the usable surface area.\n"
        "3. Strip out list item separation spaces: always format bullet structures using "
        "   '\\begin{itemize}[noitemsep, topsep=0pt, parsep=0pt, partopsep=0pt]' to eliminate whitespace gaps.\n"
        "4. Format section headings cleanly with horizontal dividers: '\\section*{{Technical Skills}} \\vspace{{-2mm}} \\hrule'.\n"
        "5. Explicitly escape special LaTeX tokens: change all raw '&' to '\\&' and all '%' to '\\%'.\n\n"
        "TRANSFORMATION RULES:\n"
        "1. Interweave the target job's 'REQUIRED HARD SKILLS' naturally into the candidate's existing real experiences and projects "
        "   using strong action verbs. Highlight their true accomplishments with high-density technical depth."
    )

    prompt_payload = (
        f"CANDIDATE PROFILE DATA:\n{json.dumps(original_profile, indent=2)}\n\n"
        f"TARGET JOB REQUIRED HARD SKILLS:\n{json.dumps(job_spec.get('required_hard_skills', []), indent=2)}\n\n"
        f"USER CONVERSATIONAL CLARIFICATIONS:\n{json.dumps(user_answers, indent=2)}"
    )

    response = llm.invoke([
        ("system", sys_instruction),
        ("user", f"Generate Compact 1-Page Resume LaTeX Source Code:\n\n{prompt_payload}")
    ])

    return response.content

if __name__ == "__main__":
    print("LaTeX calibrated 1-page engine configured.")
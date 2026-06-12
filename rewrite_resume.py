import os
from typing import Dict, Any, List
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import json

load_dotenv()

def execute_resume_rewrite(original_profile: Dict[str, Any], job_spec: Dict[str, Any], user_answers: Dict[str, str]) -> str:
    """
    Consumes candidate data, target job specifications, and conversational answers.
    Generates a high-density, strictly 1-page LaTeX document dynamically mapping 
    all profile fields including contact details, experience, and education.
    """
    print("\n[NODE] ---> Executing Dynamic 1-Page LaTeX Engine...")

    llm = init_chat_model(
        model="openai/gpt-oss-120b",
        model_provider="groq",
        temperature=0.1
    )

    full_name = original_profile.get("full_name", "CANDIDATE NAME").strip()
    email = original_profile.get("email", "").strip()
    phone = original_profile.get("phone", "").strip()
    github = original_profile.get("github_handle", "").strip()

    github_username = github.split("/")[-1] if github else ""
    email_escaped = email.replace("_", "\\_") if email else ""
    github_escaped = github_username.replace("_", "\\_") if github_username else ""

    sys_instruction = (
        "You are an elite enterprise technical resume architect. Your sole mission is to populate the candidate's "
        "historical data strictly inside the provided LaTeX structural template to fit exactly on ONE PAGE.\n\n"
        
        "STRICT CONTENT CONDENSATION & LAYOUT RULES:\n"
        "1. MAXIMUM 3 BULLETS: For the Professional Experience block and EACH project, you MUST output exactly 3 high-impact bullet points (\\item). "
        "   Condense descriptions to 3 punchy, technically dense achievements that interweave the target job requirements.\n"
        "2. PROFESSIONAL SUMMARY: Synthesize a concise 2-sentence target introduction directly beneath the header contact links.\n"
        "3. DYNAMIC EDUCATION: Read the candidate's actual academic history from the provided data. Format it cleanly under the "
        "   Education section using standard LaTeX formatting (e.g., \\textbf{University Name} \\hfill Timeline \\\\ Degree Title).\n"
        "4. NO HALLUCINATIONS: Do not use or invent mock credentials, fake job entities, or unconfirmed placeholder strings.\n"
        "5. LATEX COMPLIANCE: Ensure all raw '&' are written as '\\&' and all '%' are written as '\\%'. Never leave trailing double-backslashes (\\\\) right before a section divider.\n"
        "6. Output ONLY raw LaTeX code starting with \\documentclass and ending with \\end{document}. Do not wrap it in markdown block fences.\n\n"
        
        "LATEX SKELETON TEMPLATE TO POPULATE:\n"
        "\\documentclass[10pt,letterpaper]{article}\n"
        "\\usepackage[margin=0.5in]{geometry}\n"
        "\\usepackage{hyperref}\n"
        "\\usepackage{enumitem}\n"
        "\\usepackage{titlesec}\n"
        "\\linespread{1.12}\n"
        "\\setlist[itemize]{topsep=2pt, itemsep=2pt, parsep=0pt, partopsep=0pt}\n"
        "\\titleformat{\\section}{\\large\\bfseries}{}{0em}{}[\\titlerule]\n"
        "\\titlespacing{\\section}{0pt}{6pt}{3pt}\n"
        "\\begin{document}\n"
        "\\begin{center}\n"
        f"    {{\\LARGE \\textbf{{{full_name}}}}}\\\\\n"
        "    \\vspace{1mm}\n"
        f"    Email: \\href{{mailto:{email_escaped}}}{{{email_escaped}}} \\quad Phone: {phone} \\quad GitHub: \\href{{https://github.com/{github_username}}}{{github.com/{github_escaped}}}\n"
        "\\end{center}\n"
        "\\vspace{-2mm}\n"
        "\\section*{Professional Summary}\n"
        "Populate the concise 2-sentence targeted introduction here.\\\\\n\n"
        "\\section*{Technical Skills}\n"
        "Populate skills here using clean bold subcategories.\\\\\n\n"
        "\\section*{Professional Experience}\n"
        "Populate the experience/internship block here with EXACTLY 3 high-impact bullets.\\\\\n\n"
        "\\section*{Selected Projects}\n"
        "Populate individual projects here. Every project must have EXACTLY 3 highly optimized bullets.\\\\\n\n"
        "\\section*{Certifications}\n"
        "Populate the true candidate credentials here using an itemize list environment.\n\n"
        "\\section*{Education}\n"
        "Populate the dynamic university name, real degree track, and true graduation timeline here directly from the profile data.\n\n"
        "\\end{document}"
    )

    prompt_payload = (
        f"CANDIDATE DATA SUBSET:\n{json.dumps(original_profile, indent=2)}\n\n"
        f"TARGET JOB REQUIRED HARD SKILLS:\n{json.dumps(job_spec.get('required_hard_skills', []), indent=2)}\n\n"
        f"USER CONVERSATIONAL CLARIFICATIONS:\n{json.dumps(user_answers, indent=2)}"
    )

    response = llm.invoke([
        ("system", sys_instruction),
        ("user", f"Populate the template layout dynamically using exact profile items:\n\n{prompt_payload}")
    ])

    return response.content
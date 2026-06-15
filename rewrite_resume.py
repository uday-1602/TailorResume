import os
from typing import Dict, Any, List
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import json

load_dotenv()

def execute_resume_rewrite(original_profile: Dict[str, Any], job_spec: Dict[str, Any], gap_report: Dict[str, Any], user_answers: Dict[str, str]) -> str:
    """
    Consumes candidate data, target job specifications, and conversational answers.
    Generates a high-density, strictly 1-page LaTeX document dynamically mapping
    all profile fields including contact details, experience, and education.
    """
    print("\n[NODE] ---> Executing Dynamic 1-Page LaTeX Engine...")

    llm = init_chat_model(
        model="openai/gpt-oss-120b",
        model_provider="groq",
        temperature=0.1,
        max_tokens=4096
    )

    full_name = original_profile.get("full_name", "CANDIDATE NAME").strip()
    email = original_profile.get("email", "").strip()
    phone = original_profile.get("phone", "").strip()
    github = original_profile.get("github_handle", "").strip()

    github_username = github.split("/")[-1] if github and github.lower() not in ("n/a", "", "none") else ""
    email_escaped = email.replace("_", "\\_") if email else ""
    github_escaped = github_username.replace("_", "\\_") if github_username else ""

    contact_items = []
    if email_escaped:
        contact_items.append(f"Email: \\href{{mailto:{email_escaped}}}{{{email_escaped}}}")
    if phone:
        contact_items.append(f"Phone: {phone}")
    if github_username:
        contact_items.append(f"GitHub: \\href{{https://github.com/{github_username}}}{{github.com/{github_escaped}}}")
    contact_line = " \\quad ".join(contact_items)

    # --- Fixed preamble block (hardcoded, must be output verbatim) ---
    preamble = (
        "\\documentclass[10pt,letterpaper]{article}\n"
        "\\usepackage[top=0.4in,bottom=0.4in,left=0.5in,right=0.5in]{geometry}\n"
        "\\usepackage[hidelinks]{hyperref}\n"
        "\\usepackage{enumitem}\n"
        "\\usepackage{titlesec}\n"
        "\\usepackage{parskip}\n"
        "\\setlength{\\parskip}{0pt}\n"
        "\\linespread{1.04}\n"
        "\\setlist[itemize]{topsep=1pt, itemsep=0pt, parsep=0pt, partopsep=0pt, leftmargin=1.2em}\n"
        "\\titleformat{\\section}{\\large\\bfseries}{}{0em}{}[\\titlerule]\n"
        "\\titlespacing{\\section}{0pt}{5pt}{2pt}\n"
        "\\begin{document}\n"
        "\\begin{center}\n"
        f"    {{\\LARGE \\textbf{{{full_name}}}}}\\\\\n"
        "    \\vspace{1mm}\n"
        f"    {contact_line}\n"
        "\\end{center}\n"
        "\\vspace{-3mm}"
    )

    sys_instruction = f"""You are an expert technical resume writer specializing in AI/ML engineering roles. \
Your task is to generate a COMPLETE, COMPILABLE, single-page LaTeX resume for the candidate using the provided data.

=====================================================================
PART 1 — OUTPUT FORMAT (MANDATORY, NON-NEGOTIABLE)
=====================================================================

Your output MUST:
- Start EXACTLY with the preamble block below (copy it verbatim, do not alter it).
- End EXACTLY with \\end{{document}} on the final line.
- Contain NO markdown fences (no ```latex), NO explanatory text, NO comments outside of the LaTeX.
- Be 100% compilable by pdflatex without errors.

MANDATORY PREAMBLE (copy verbatim, then continue from \\section*{{Professional Summary}}):
{preamble}

=====================================================================
PART 2 — CONTENT RULES
=====================================================================

RULE 1 — PROFESSIONAL SUMMARY (2 sentences, not generic):
  Write using this formula:
    Sentence 1: [Role identity] with [current role / internship and academic] experience in [core domain], specializing in [2-3 top technical areas from the job spec that the candidate genuinely has].
    Sentence 2: Proven ability to [key capability from experience highlights or projects], with hands-on exposure to [1-2 specific tools from job spec found in their profile or user answers].
  IMPORTANT:
    - Be specific to this candidate and this job. Do NOT write generic filler.
    - Check the candidate's actual graduation date and experience duration. Since this candidate is a B.Tech student (graduating in 2027) with less than a year of internship experience (Jan 2026 - Present), DO NOT state "1+ years of experience" or fabricate any years of professional experience. Instead, describe them using terms like "hands-on internship and academic experience" or as a "Project Trainee Intern".
  End the summary block with a single \\ (not \\\\).

RULE 2 — TECHNICAL SKILLS:
  Organize into 4-5 bold subcategories (e.g., \\textbf{{Languages:}}, \\textbf{{AI/ML:}}, \
\\textbf{{Cloud:}}, \\textbf{{Databases:}}, \\textbf{{Web \\& Tools:}}).
  Each subcategory on its own line ending with \\\\
  Pull skills from core_technical_skills AND weave in preferred_or_bonus_skills the candidate has exposure.

RULE 3 — PROFESSIONAL EXPERIENCE:
  Include 1 to 2 experience entries (most recent first). Omit least relevant if space is tight.
  Format EXACTLY as:
    \\textbf{{Organization}} \\hfill Start -- End\\\\
    \\textit{{Role Title}}
    \\begin{{itemize}}
      \\item bullet
      \\item bullet
    \\end{{itemize}}
  Use 2-3 bullets per entry. Each bullet must be under 20 words, action-verb first.
  Weave in required job skills ONLY where the candidate genuinely has exposure based on their highlights or user answers. Do NOT include skills (like FastAPI) that the candidate lacks.

RULE 4 — PROJECTS (2 to 3 entries, most relevant first):
  Select projects with the HIGHEST overlap to the target job's required skills. Omit unrelated ones.
  Format EXACTLY as:
    \\textbf{{Project Name}} $|$ \\textit{{Tech1, Tech2, Tech3}}
    \\begin{{itemize}}
      \\item bullet
      \\item bullet
    \\end{{itemize}}
  Use 2-3 bullets per project. Each bullet under 20 words, action-verb first.
  DO NOT fabricate metrics, percentages, star counts, or document volumes not present in the source data. \
Describe impact qualitatively instead (e.g., "enabling fast semantic retrieval", "streamlining knowledge access").

RULE 5 — CERTIFICATIONS:
  If certifications exist in the profile data OR were mentioned in user answers, include:
    \\section*{{Certifications}}
    \\begin{{itemize}}
      \\item Certification Name
    \\end{{itemize}}
  If none exist, OMIT this section entirely.

RULE 6 — EDUCATION:
  List ALL education entries from the profile data. Format EXACTLY as:
    \\textbf{{Institution Name}} \\hfill Timeline\\\\
    Degree -- CGPA: X/10   (or Degree -- Percentage: XX\\%)
  Separate entries with \\\\[3pt] between them. Do NOT use \\item or itemize here.
  Always include CGPA or percentage if present in the data.

RULE 7 — LATEX COMPLIANCE (CRITICAL):
  - Every & must be \\&
  - Every % must be \\%
  - Every section must open with \\section*{{...}} and contain valid LaTeX content.
  - Every \\begin{{itemize}} must have a matching \\end{{itemize}}.
  - The last line must be \\end{{document}} with nothing after it.
  - Do NOT use em-dashes (—), curly quotes (""), or any non-ASCII character directly. \
Use LaTeX equivalents: -- for en-dash, --- for em-dash, \\textquoteleft etc.

RULE 8 — ONE PAGE GUARANTEE:
  The entire document MUST fit on exactly one page when compiled.
  If you are running long: reduce bullets to 2 per block, trim bullet word count, drop the least \
relevant project, or shorten the skills section.

RULE 9 — TRUTHFULNESS & SKILL INTEGRITY (MANDATORY):
  - Do NOT assume, fabricate, or hallucinate skills that are not explicitly in the candidate's profile data or conversational answers.
  - Specifically: The candidate has NEVER used FastAPI and has not confirmed exposure to it. Therefore, you MUST NOT include FastAPI anywhere on the resume (not in the professional summary, skills list, experience, or projects). 
  - Instead, focus on the skills they actually possess, such as Python, Flask, LangGraph, AWS Bedrock, AWS S3, and Pinecone.

=====================================================================
PART 3 — SELF-VALIDATION CHECKLIST (run before outputting)
=====================================================================

Before outputting, verify:
[ ] Output starts with \\documentclass{{10pt,letterpaper}}{{article}}
[ ] Output ends with \\end{{document}} and nothing after
[ ] No markdown code fences present
[ ] Every \\begin{{itemize}} has a closing \\end{{itemize}}
[ ] No fabricated numeric metrics
[ ] Professional Summary is 2 specific sentences (not generic)
[ ] Education has CGPA/percentage appended
[ ] All & escaped as \\& and all % escaped as \\%
[ ] \\end{{document}} is the very last line
[ ] Absolutely NO mentions of FastAPI (since the candidate has never used or confirmed it)
[ ] Only skills and technologies present in the candidate profile or user answers are included (no fabrication)
"""

    high_severity_gaps = [
        g for g in gap_report.get("identified_gaps", [])
        if g.get("severity") == "HIGH"
    ]
    strategic_rec = gap_report.get("strategic_recommendation", "")

    prompt_payload = (
        f"CANDIDATE DATA SUBSET:\n{json.dumps(original_profile, indent=2)}\n\n"
        f"TARGET JOB TITLE: {job_spec.get('job_title', 'N/A')}\n\n"
        f"TARGET JOB REQUIRED HARD SKILLS:\n{json.dumps(job_spec.get('required_hard_skills', []), indent=2)}\n\n"
        f"TARGET JOB PREFERRED / BONUS SKILLS:\n{json.dumps(job_spec.get('preferred_or_bonus_skills', []), indent=2)}\n\n"
        f"HIGH-SEVERITY SKILL GAPS TO BRIDGE:\n{json.dumps(high_severity_gaps, indent=2)}\n\n"
        f"STRATEGIC RECOMMENDATION FROM GAP ANALYSIS:\n{strategic_rec}\n\n"
        f"USER CONVERSATIONAL CLARIFICATIONS:\n{json.dumps(user_answers, indent=2)}"
    )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _invoke_with_retry():
        return llm.invoke([
            ("system", sys_instruction),
            ("user", (
                "Generate the complete tailored LaTeX resume now.\n\n"
                "IMPORTANT: Your response must start with \\documentclass on the very first character "
                "and end with \\end{document} on the very last line. "
                "Do not include any text, explanation, or markdown before or after the LaTeX.\n\n"
                f"DATA TO USE:\n\n{prompt_payload}"
            ))
        ])

    response = _invoke_with_retry()

    # Strip any accidental markdown fences the model may output
    content = response.content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        # Drop first and last fence lines
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return content

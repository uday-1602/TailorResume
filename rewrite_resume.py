import os
from typing import Dict, Any, List
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import json

load_dotenv()

# Map standard AWS credentials for Bedrock/boto3 integration
if os.getenv("AWS_ACCESS_KEY") and not os.getenv("AWS_ACCESS_KEY_ID"):
    os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY")
if os.getenv("AWS_SECRET_KEY") and not os.getenv("AWS_SECRET_ACCESS_KEY"):
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_KEY")

def execute_resume_rewrite(original_profile: Dict[str, Any], job_spec: Dict[str, Any], gap_report: Dict[str, Any], user_answers: Dict[str, str]) -> str:
    """
    Consumes candidate data, target job specifications, and conversational answers.
    Generates a high-density, strictly 1-page LaTeX document dynamically mapping
    all profile fields including contact details, experience, and education.
    """
    print("\n[NODE] ---> Executing Dynamic 1-Page LaTeX Engine...")

    model_id = os.getenv("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")

    llm = init_chat_model(
        model=model_id,
        model_provider="bedrock",
        temperature=0.1,
        max_tokens=4096,
        region_name=region
    )

    full_name = (original_profile.get("full_name") or "CANDIDATE NAME").strip()
    email = (original_profile.get("email") or "").strip()
    phone = (original_profile.get("phone") or "").strip()
    github = (original_profile.get("github_handle") or "").strip()

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
    - Check the candidate's actual graduation date and experience duration. DO NOT state experience duration (e.g. "X+ years of experience") or fabricate any years of professional experience that is not supported by the candidate's profile data. Instead, describe their experience level accurately using terms like "hands-on internship and academic experience" or their actual roles.
  End the summary block with a single \\ (not \\\\).

RULE 2 — TECHNICAL SKILLS:
  Organize into 4-5 bold subcategories (e.g., \\textbf{{Languages:}}, \\textbf{{AI/ML:}}, \\textbf{{Cloud:}}, \\textbf{{Databases:}}, \\textbf{{Web \\& Tools:}}).
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
  Weave in required job skills ONLY where the candidate genuinely has exposure based on their highlights or user answers. Do NOT include skills that the candidate lacks.

RULE 4 — PROJECTS (2 to 3 entries, most relevant first):
  Select projects with the HIGHEST overlap to the target job's required skills. Omit unrelated ones.
  Format EXACTLY as:
    \\textbf{{Project Name}} $|$ \\textit{{Tech1, Tech2, Tech3}}
    \\begin{{itemize}}
      \\item bullet
      \\item bullet
    \\end{{itemize}}
  Use 2-3 bullets per project. Each bullet under 20 words, action-verb first.
  DO NOT fabricate metrics, percentages, star counts, or document volumes not present in the source data. Describe impact qualitatively instead (e.g., "enabling fast semantic retrieval", "streamlining knowledge access").

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
    Degree -- CGPA: X/10\\\\   (or Degree -- Percentage: XX\\%\\\\)
  CRITICAL FORMATTING:
  - Separate entries with \\vspace{{3pt}} (no blank line before or after this command).
  - The \\vspace{{3pt}} line must be IMMEDIATELY followed by \\textbf on the next line — NO blank lines.
  - Every degree/grade line MUST end with \\\\ (double backslash).
  - Do NOT use \\item or itemize here.
  - Do NOT leave ANY blank lines inside the Education section.
  Always include CGPA or percentage if present in the data.
  Example of CORRECT Education formatting:
    \\section*{{Education}}
    \\textbf{{University Name}} \\hfill 2020 -- 2024\\\\
    B.Tech in Computer Science -- CGPA: 8.5/10\\\\
    \\vspace{{3pt}}
    \\textbf{{School Name}} \\hfill Completed 2020\\\\
    HSC -- Percentage: 85\\%\\\\

RULE 7 — LATEX COMPLIANCE (CRITICAL):
  - Every & must be \\&
  - Every % must be \\%
  - Every section must open with \\section*{{...}} and contain valid LaTeX content.
  - Every \\begin{{itemize}} must have a matching \\end{{itemize}}.
  - The last line must be \\end{{document}} with nothing after it.
  - Do NOT use em-dashes (—), curly quotes (""), or any non-ASCII character directly. Use LaTeX equivalents: -- for en-dash, --- for em-dash, \\textquoteleft etc.

RULE 8 — ONE PAGE GUARANTEE:
  The entire document MUST fit on exactly one page when compiled.
  If you are running long: reduce bullets to 2 per block, trim bullet word count, drop the least relevant project, or shorten the skills section.

RULE 9 — TRUTHFULNESS & SKILL INTEGRITY (MANDATORY):
  - Do NOT assume, fabricate, or hallucinate skills that are not explicitly in the candidate's profile data or conversational answers.
  - You MUST NOT include any skills or technologies anywhere on the resume (not in the professional summary, skills list, experience, or projects) if they are missing from the candidate's profile or have not been confirmed in the conversational answers.
  - Instead, focus exclusively on the skills they actually possess or have confirmed exposure to.

RULE 10 — VOCABULARY DIVERSITY (MANDATORY):
  Never repeat the same action verbs (such as 'implemented', 'designed', 'developed', 'led') more than twice across the entire resume. Use a rich and diverse set of action verbs (e.g., 'architected', 'engineered', 'streamlined', 'orchestrated', 'executed', 'formulated', 'spearheaded', 'pioneered', 'optimized', 'modernized').

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
[ ] Absolutely NO mentions of skills or technologies not present in the candidate profile or user answers
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

    content = _fix_latex(content)
    return content


def _fix_latex(source: str) -> str:
    """
    Post-process the LLM-generated LaTeX to fix common formatting mistakes:
    1. Remove blank lines inside the \\section*{Education} block (blank lines break spacing).
    2. Ensure every non-empty, non-command line inside Education ends with \\\\ if it doesn't already.
    3. Ensure the last Technical Skills subcategory line ends with \\\\ (LLM often omits it).
    4. Remove blank lines immediately after \\vspace{...} commands.
    """
    import re

    lines = source.splitlines()
    result = []
    in_education = False
    in_skills = False
    skills_lines = []          # buffer for skills lines
    skills_start_idx = None    # index in result[] where skills content starts

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Detect section boundaries ──────────────────────────────────────
        if re.match(r'\\section\*\{Education\}', stripped):
            in_education = True
            in_skills = False
            result.append(line)
            i += 1
            continue

        if re.match(r'\\section\*\{Technical Skills\}', stripped, re.IGNORECASE) or \
           re.match(r'\\section\*\{Skills\}', stripped, re.IGNORECASE):
            in_skills = True
            in_education = False
            skills_lines = []
            skills_start_idx = len(result)
            result.append(line)
            i += 1
            continue

        # Leaving education / skills on any new \section
        if stripped.startswith('\\section') and in_education:
            in_education = False
        if stripped.startswith('\\section') and in_skills:
            # Flush skills: ensure last non-empty skills line ends with \\
            _flush_skills(result, skills_lines)
            skills_lines = []
            in_skills = False

        # ── Education block: no blank lines, degree lines end with \\ ───────
        if in_education:
            # Skip blank lines entirely inside education
            if stripped == '':
                i += 1
                continue

            # Ensure \vspace lines are not followed by blank line (handled by skipping blanks above)
            # Ensure degree/grade lines end with \\
            if not stripped.startswith('\\') or stripped.startswith('\\textbf') or stripped.startswith('\\textit'):
                # It's a content line (institution or degree). Ensure \\ at end.
                if not stripped.endswith('\\\\') and not stripped.endswith('\\\\%'):
                    line = line.rstrip() + '\\\\'

            result.append(line)
            i += 1
            continue

        # ── Skills block: buffer lines for post-processing ─────────────────
        if in_skills:
            skills_lines.append(line)
            result.append(line)
            i += 1
            continue

        # ── Global: remove blank lines immediately after \vspace{...} ───────
        result.append(line)
        if re.match(r'\\vspace\{', stripped):
            # Skip any following blank lines
            while i + 1 < len(lines) and lines[i + 1].strip() == '':
                i += 1
        i += 1

    # If document ended while still in skills, flush
    if in_skills and skills_lines:
        _flush_skills(result, skills_lines)

    return '\n'.join(result)


def _flush_skills(result: list, skills_lines: list):
    """
    Ensure the last non-empty, non-section-boundary skills line ends with \\.
    Mutates `result` in-place by patching the last skills line if needed.
    """
    import re
    # Find the last non-empty skills content line index in result
    for j in range(len(result) - 1, -1, -1):
        s = result[j].strip()
        if s and not s.startswith('\\section'):
            if not s.endswith('\\\\'):
                result[j] = result[j].rstrip() + '\\\\'
            break

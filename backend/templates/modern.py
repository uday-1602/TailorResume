"""
Modern Resume Template — HTML + WeasyPrint renderer
====================================================
Uses the same LLM (Bedrock Claude Haiku) as the classic LaTeX template,
but asks it to output structured JSON instead of LaTeX.
Python then builds a styled two-column HTML document and
WeasyPrint renders it to a print-ready PDF.
"""

import os
import json
import re
from typing import Dict, Any, List

from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

# Map custom env var names → boto3/Bedrock standard names
if os.getenv("AWS_ACCESS_KEY") and not os.getenv("AWS_ACCESS_KEY_ID"):
    os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY")
if os.getenv("AWS_SECRET_KEY") and not os.getenv("AWS_SECRET_ACCESS_KEY"):
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_KEY")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def execute_resume_rewrite_modern(
    original_profile: Dict[str, Any],
    job_spec: Dict[str, Any],
    gap_report: Dict[str, Any],
    user_answers: Dict[str, str],
    output_pdf_path: str,
) -> str:
    """
    Generate a modern two-column resume PDF using HTML + Playwright (headless Chromium).

    Args:
        original_profile: Parsed candidate data from profile_analyzer.
        job_spec:         Parsed job requirements from job_scraper.
        gap_report:       Gap analysis output.
        user_answers:     Chatbot Q&A from the interview step.
        output_pdf_path:  Absolute path where the final PDF should be written.

    Returns:
        JSON string of the generated resume content
        (stored in final_latex_source for graph state compatibility).
    """
    print("\n[NODE] ---> Executing Modern HTML Resume Engine...")

    # Step 1 — LLM generates structured resume content as JSON
    resume_data = _generate_resume_json(original_profile, job_spec, gap_report, user_answers)

    # Step 2 — Build a standalone HTML document
    html_content = _build_html(resume_data, original_profile)

    # Step 3 — Render HTML → PDF via Playwright (headless Chromium, works on Windows without GTK)
    _html_to_pdf(html_content, output_pdf_path)
    print(f"[MODERN] PDF successfully written to: {output_pdf_path}")

    return json.dumps(resume_data, indent=2)


def _html_to_pdf(html_content: str, output_pdf_path: str) -> None:
    """Render an HTML string to a PDF file using Playwright's headless Chromium."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright is required for the Modern template. "
            "Install it with: pip install playwright && playwright install chromium"
        )

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(
            path=output_pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()


# ---------------------------------------------------------------------------
# LLM: Generate structured JSON resume content
# ---------------------------------------------------------------------------

def _generate_resume_json(
    original_profile: Dict[str, Any],
    job_spec: Dict[str, Any],
    gap_report: Dict[str, Any],
    user_answers: Dict[str, str],
) -> Dict[str, Any]:
    """Call Bedrock Claude to generate resume content as a structured JSON object."""

    model_id = os.getenv("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")

    llm = init_chat_model(
        model=model_id,
        model_provider="bedrock",
        temperature=0.1,
        max_tokens=4096,
        region_name=region,
    )

    high_severity_gaps = [
        g for g in gap_report.get("identified_gaps", [])
        if g.get("severity") == "HIGH"
    ]
    strategic_rec = gap_report.get("strategic_recommendation", "")

    sys_instruction = """\
You are an expert technical resume writer. Your task is to generate tailored resume content \
as a SINGLE valid JSON object — no markdown, no code fences, no explanation.

=======================================================================
OUTPUT FORMAT — STRICTLY VALID JSON, NOTHING ELSE
=======================================================================

Return ONLY this JSON structure (all keys required):

{
  "current_role_title": "<most recent role title or student designation, e.g. 'Management Lead'>",
  "summary": "<exactly 2 sentences, see RULE 1 below>",
  "skills": [
    {"category": "<Category Name>", "items": ["<Skill1>", "<Skill2>", ...]},
    ...
  ],
  "experience": [
    {
      "organization": "<Organization Name>",
      "role": "<Role Title>",
      "period": "<e.g. Sep 2025 – Present>",
      "bullets": ["<action-verb bullet>", ...]
    },
    ...
  ],
  "projects": [
    {
      "name": "<Project Name>",
      "tech": ["<Tech1>", "<Tech2>", ...],
      "bullets": ["<action-verb bullet>", ...]
    },
    ...
  ],
  "education": [
    {
      "institution": "<Institution Name>",
      "degree": "<Degree / Course Name>",
      "period": "<e.g. Expected Jun 2027>",
      "score": "<e.g. CGPA: 8.68/10 or Percentage: 85%>"
    },
    ...
  ],
  "certifications": ["<Cert Name>", ...]
}

=======================================================================
CONTENT RULES
=======================================================================

RULE 1 — SUMMARY (2 specific sentences):
  Sentence 1: [Role identity] with [current role/experience/academic] experience in [core domain], \
specializing in [2-3 top technical areas the candidate genuinely has].
  Sentence 2: Proven ability to [key capability from experience/projects], with hands-on exposure to \
[1-2 specific tools from the job spec that appear in the candidate's profile or user answers].
  IMPORTANT: If the candidate's original resume/profile explicitly mentions their years of experience (e.g. "3+ years") or important industry domains (e.g. "for one of the biggest NBFC companies"), you MUST preserve these details in your summary. Otherwise, do NOT state years of professional experience and use terms like "hands-on academic experience" instead. Do NOT fabricate years of experience.

RULE 2 — SKILLS (4-5 categories):
  Pull skills ONLY from core_technical_skills AND skills the candidate confirmed in their answers.
  DO NOT include any skill not present in the candidate profile or user answers.

RULE 3 — EXPERIENCE (1-2 most recent entries):
  3-5 bullets per entry. Do NOT arbitrarily truncate or delete bullets if the candidate has them in their original profile; preserve their detailed achievements (up to 5 bullets per role) so the page is fully and professionally utilized. Each bullet: action-verb first, under 20 words.
  Weave in required job skills ONLY where the candidate genuinely has exposure.

RULE 4 — PROJECTS (2-3 most relevant):
  Select projects with highest overlap to target job required skills.
  2-3 bullets per project. Action-verb first, under 20 words.
  DO NOT fabricate metrics, percentages, or counts not in the source data.

RULE 5 — EDUCATION: List ALL entries from the profile. Include CGPA or percentage if present.

RULE 6 — CERTIFICATIONS: Include if in profile or user answers. Empty array [] if none.

RULE 7 — TRUTHFULNESS (MANDATORY):
  NEVER include skills, technologies, or achievements not explicitly in the candidate's profile \
or confirmed via user answers. Every skill chip that appears must be genuinely owned by the candidate.

RULE 8 — SENIOR / EXPERIENCED PROFILES (CRITICAL):
  If the candidate is highly experienced (e.g. 5+ years of experience), focus heavily on professional \
experience and projects rather than academic items. Bullet descriptions must be extremely concise, \
impactful, and brief (under 18 words) so they can fit on a single page without spilling over.

RULE 9 — VOCABULARY DIVERSITY (MANDATORY):
  Never repeat the same action verbs (such as 'implemented', 'designed', 'developed', 'led') more than twice across the entire resume. Use a rich and diverse set of action verbs (e.g., 'architected', 'engineered', 'streamlined', 'orchestrated', 'executed', 'formulated', 'spearheaded', 'pioneered', 'optimized', 'modernized').
"""

    prompt_payload = (
        f"CANDIDATE DATA:\n{json.dumps(original_profile, indent=2)}\n\n"
        f"TARGET JOB TITLE: {job_spec.get('job_title', 'N/A')}\n\n"
        f"REQUIRED HARD SKILLS:\n{json.dumps(job_spec.get('required_hard_skills', []), indent=2)}\n\n"
        f"PREFERRED / BONUS SKILLS:\n{json.dumps(job_spec.get('preferred_or_bonus_skills', []), indent=2)}\n\n"
        f"HIGH-SEVERITY GAPS TO BRIDGE:\n{json.dumps(high_severity_gaps, indent=2)}\n\n"
        f"STRATEGIC RECOMMENDATION:\n{strategic_rec}\n\n"
        f"USER CONVERSATIONAL ANSWERS:\n{json.dumps(user_answers, indent=2)}"
    )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _invoke():
        return llm.invoke([
            ("system", sys_instruction),
            ("user", (
                "Generate the tailored resume JSON now.\n"
                "IMPORTANT: Your response must be ONLY the JSON object — "
                "first character must be '{' and last character must be '}'.\n\n"
                f"DATA:\n{prompt_payload}"
            )),
        ])

    response = _invoke()
    content = response.content.strip()

    # Strip accidental markdown fences
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    # Parse JSON with fallback regex extraction
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise ValueError(f"LLM did not return valid JSON. Response snippet: {content[:300]}")

    return data


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """Escape HTML special characters in user-generated strings."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_html(data: Dict[str, Any], profile: Dict[str, Any]) -> str:
    """
    Construct a complete, self-contained HTML document styled as a
    modern two-column resume. WeasyPrint will render this to A4 PDF.
    """
    # Calculate total text density to dynamically choose standard vs compact layout
    exp_count = len(data.get("experience", []))
    proj_count = len(data.get("projects", []))
    edu_count = len(data.get("education", []))
    cert_count = len(data.get("certifications", []))
    exp_bullets = sum(len(exp.get("bullets", [])) for exp in data.get("experience", []))
    proj_bullets = sum(len(proj.get("bullets", [])) for proj in data.get("projects", []))
    
    total_blocks = exp_count + proj_count + edu_count + (1 if cert_count > 0 else 0) + exp_bullets + proj_bullets
    is_compact = total_blocks >= 26

    # --- Contact info comes from raw profile (not LLM) to prevent hallucination ---
    full_name = (profile.get("full_name") or "CANDIDATE NAME").upper()
    email = (profile.get("email") or "").strip()
    phone = (profile.get("phone") or "").strip()
    github_raw = (profile.get("github_handle") or "").strip()
    github_user = github_raw.split("/")[-1] if github_raw and github_raw.lower() not in ("n/a", "none", "") else ""
    linkedin_raw = (profile.get("linkedin_handle") or "").strip()
    linkedin_user = linkedin_raw.split("/")[-1] if linkedin_raw and linkedin_raw.lower() not in ("n/a", "none", "") else ""

    role_title = _esc(data.get("current_role_title") or "")
    summary_text = _esc(data.get("summary") or "")

    # --- Contacts row ---
    contact_parts: List[str] = []
    if phone:
        contact_parts.append(f"&#9742;&nbsp;{_esc(phone)}")
    if email:
        contact_parts.append(f"&#9993;&nbsp;{_esc(email)}")
    if github_user:
        contact_parts.append(f"&#128279;&nbsp;github.com/{_esc(github_user)}")
    if linkedin_user:
        contact_parts.append(f"&#128279;&nbsp;linkedin.com/in/{_esc(linkedin_user)}")
    contacts_html = " &nbsp;&bull;&nbsp; ".join(contact_parts)

    # --- Skills (right column) ---
    skills_html = ""
    for cat in data.get("skills", []):
        cat_name = _esc(cat.get("category") or "")
        chips = "".join(
            f'<span class="chip">{_esc(item)}</span>'
            for item in cat.get("items", [])
            if item
        )
        if cat_name and chips:
            skills_html += f"""
            <div class="skill-category">
                <div class="skill-cat-label">{cat_name}</div>
                <div class="skill-chips">{chips}</div>
            </div>"""

    # --- Experience (left column) ---
    experience_html = ""
    for exp in data.get("experience", []):
        org = _esc(exp.get("organization") or "")
        role = _esc(exp.get("role") or "")
        period = _esc(exp.get("period") or "")
        bullet_items = "".join(
            f"<li>{_esc(b)}</li>" for b in exp.get("bullets", []) if b
        )
        if org:
            experience_html += f"""
            <div class="exp-entry">
                <div class="exp-header">
                    <span class="exp-org">{org}</span>
                    <span class="exp-period">{period}</span>
                </div>
                <div class="exp-role-wrap">
                    <div class="exp-role">{role}</div>
                </div>
                {"<ul class='bullets'>" + bullet_items + "</ul>" if bullet_items else ""}
            </div>"""

    # --- Projects (right column) ---
    projects_html = ""
    for proj in data.get("projects", []):
        name = _esc(proj.get("name") or "")
        tech_tags = "".join(
            f'<span class="tech-tag">{_esc(t)}</span>'
            for t in proj.get("tech", []) if t
        )
        bullet_items = "".join(
            f"<li>{_esc(b)}</li>" for b in proj.get("bullets", []) if b
        )
        if name:
            projects_html += f"""
            <div class="project-entry">
                <div class="project-name">{name}</div>
                {"<div class='project-tech'>" + tech_tags + "</div>" if tech_tags else ""}
                {"<ul class='bullets'>" + bullet_items + "</ul>" if bullet_items else ""}
            </div>"""

    # --- Education (left column) ---
    education_html = ""
    for edu in data.get("education", []):
        institution = _esc(edu.get("institution") or "")
        degree = _esc(edu.get("degree") or "")
        period = _esc(edu.get("period") or "")
        score = _esc(edu.get("score") or "")
        if institution:
            education_html += f"""
            <div class="edu-entry">
                <div class="edu-institution">{institution}</div>
                {"<div class='edu-degree'>" + degree + "</div>" if degree else ""}
                <div class="edu-meta">
                    <span class="edu-period">{period}</span>
                    {"<span class='edu-score'>" + score + "</span>" if score else ""}
                </div>
            </div>"""

    # --- Certifications (left column, optional) ---
    certs = [c for c in data.get("certifications", []) if c]
    certs_section = ""
    if certs:
        cert_items = "".join(f"<li>{_esc(c)}</li>" for c in certs)
        certs_section = f"""
        <div class="section">
            <div class="section-title">Certifications</div>
            <ul class="cert-list">{cert_items}</ul>
        </div>"""

    # --- Assemble sections conditionally ---
    experience_section = (
        f"<div class='section'><div class='section-title'>Experience</div>{experience_html}</div>"
        if experience_html else ""
    )
    education_section = (
        f"<div class='section'><div class='section-title'>Education</div>{education_html}</div>"
        if education_html else ""
    )
    skills_section = (
        f"<div class='section'><div class='section-title'>Skills</div>{skills_html}</div>"
        if skills_html else ""
    )
    projects_section = (
        f"<div class='section'><div class='section-title'>Projects</div>{projects_html}</div>"
        if projects_html else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>

/* ── Page setup ── */
@page {{
    size: A4;
    margin: 0;
}}

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: Arial, 'DejaVu Sans', Helvetica, sans-serif;
    font-size: 9.5pt;
    color: #1a1a1a;
    background: white;
    line-height: 1.4;
}}

/* ── Two-column page ── */
.page {{
    width: 210mm;
    min-height: 297mm;
    background: white;
    overflow: hidden;
}}

.left-col {{
    float: left;
    width: 59%;
    padding: 30px 18px 30px 30px;
    min-height: 297mm;
    border-right: 1.5px solid #e0e0e0;
}}

.right-col {{
    float: left;
    width: 41%;
    padding: 30px 30px 30px 18px;
    min-height: 297mm;
    background: #f7f8f9;
}}

.clearfix::after {{
    content: '';
    display: table;
    clear: both;
}}

/* ── Header ── */
.header {{
    margin-bottom: 18px;
    padding-bottom: 12px;
    border-bottom: 2.5px solid #0d9488;
}}

.candidate-name {{
    font-size: 21pt;
    font-weight: bold;
    color: #0f172a;
    letter-spacing: 0.5px;
    line-height: 1.1;
}}

.candidate-role {{
    font-size: 10.5pt;
    color: #0d9488;
    font-weight: bold;
    margin-top: 4px;
    margin-bottom: 8px;
}}

.contacts {{
    font-size: 8.5pt;
    color: #4b5563;
    line-height: 1.8;
}}

/* ── Section layout ── */
.section {{
    margin-bottom: 20px;
}}

.section-title {{
    font-size: 9.5pt;
    font-weight: bold;
    color: #0f172a;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding-bottom: 4px;
    border-bottom: 1.5px solid #0d9488;
    margin-bottom: 10px;
}}

/* ── Summary ── */
.summary-text {{
    font-size: 9pt;
    color: #374151;
    line-height: 1.5;
}}

/* ── Experience ── */
.exp-entry {{
    margin-bottom: 14px;
}}

.exp-header {{
    overflow: hidden;
}}

.exp-org {{
    font-size: 9.5pt;
    font-weight: bold;
    color: #0d9488;
    float: left;
}}

.exp-period {{
    font-size: 8pt;
    color: #6b7280;
    float: right;
}}

.exp-role-wrap {{
    clear: both;
    padding-top: 1px;
}}

.exp-role {{
    font-size: 9pt;
    font-weight: bold;
    color: #374151;
    margin-bottom: 4px;
}}

.bullets {{
    padding-left: 14px;
    margin-top: 3px;
}}

.bullets li {{
    font-size: 8.5pt;
    color: #4b5563;
    margin-bottom: 3.5px;
    line-height: 1.45;
}}

/* ── Education ── */
.edu-entry {{
    margin-bottom: 12px;
}}

.edu-institution {{
    font-size: 9pt;
    font-weight: bold;
    color: #0d9488;
}}

.edu-degree {{
    font-size: 8.5pt;
    color: #374151;
    margin-top: 1.5px;
}}

.edu-meta {{
    overflow: hidden;
    font-size: 8.5pt;
    color: #6b7280;
    margin-top: 2.5px;
}}

.edu-period {{
    float: left;
}}

.edu-score {{
    float: right;
    font-weight: bold;
    color: #0d9488;
}}

/* ── Certifications ── */
.cert-list {{
    padding-left: 14px;
}}

.cert-list li {{
    font-size: 8.5pt;
    color: #4b5563;
    margin-bottom: 3.5px;
}}

/* ── Skills (right col) ── */
.skill-category {{
    margin-bottom: 15px;
}}

.skill-cat-label {{
    font-size: 8.5pt;
    font-weight: bold;
    color: #0d9488;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1.2px solid #0d9488;
    padding-bottom: 3px;
    margin-bottom: 8px;
    display: block;
}}

.skill-chips {{
    line-height: 2.1;
}}

.chip {{
    display: inline-block;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 2px 9px;
    font-size: 8pt;
    color: #374151;
    background: white;
    margin: 2px 3px;
}}

/* ── Projects (right col) ── */
.project-entry {{
    margin-bottom: 15px;
}}

.project-name {{
    font-size: 9pt;
    font-weight: bold;
    color: #0f172a;
}}

.project-tech {{
    margin: 4px 0;
    line-height: 1.8;
}}

.tech-tag {{
    display: inline-block;
    font-size: 7.5pt;
    color: #0d9488;
    background: #f0fdfa;
    border: 1px solid #99f6e4;
    padding: 1px 7px;
    border-radius: 8px;
    margin: 2px 3px;
}}

/* ── Compact layout overrides ── */
.page.compact {{
    font-size: 9pt;
    line-height: 1.32;
}}
.page.compact .left-col {{
    float: left;
    width: 59%;
    padding: 22px 14px 22px 22px;
}}
.page.compact .right-col {{
    float: left;
    width: 41%;
    padding: 22px 22px 22px 14px;
}}
.page.compact .header {{
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom-width: 2px;
}}
.page.compact .candidate-name {{
    font-size: 19pt;
}}
.page.compact .candidate-role {{
    font-size: 9.5pt;
    margin-top: 2px;
    margin-bottom: 6px;
}}
.page.compact .contacts {{
    font-size: 8pt;
    line-height: 1.6;
}}
.page.compact .section {{
    margin-bottom: 12px;
}}
.page.compact .section-title {{
    font-size: 8.5pt;
    margin-bottom: 6px;
    padding-bottom: 2px;
    border-bottom-width: 1px;
}}
.page.compact .summary-text {{
    font-size: 8.5pt;
}}
.page.compact .exp-entry {{
    margin-bottom: 8px;
}}
.page.compact .exp-org {{
    font-size: 8.5pt;
}}
.page.compact .exp-period {{
    font-size: 7.5pt;
    margin-top: 1px;
}}
.page.compact .exp-role {{
    font-size: 8pt;
    margin-bottom: 2px;
}}
.page.compact .bullets {{
    padding-left: 12px;
    margin-top: 2px;
}}
.page.compact .bullets li {{
    font-size: 8pt;
    margin-bottom: 1.5px;
    line-height: 1.35;
}}
.page.compact .edu-entry {{
    margin-bottom: 8px;
}}
.page.compact .edu-institution {{
    font-size: 8.5pt;
}}
.page.compact .edu-degree {{
    font-size: 8pt;
}}
.page.compact .edu-meta {{
    font-size: 7.5pt;
    margin-top: 1.5px;
}}
.page.compact .cert-list {{
    padding-left: 12px;
}}
.page.compact .cert-list li {{
    font-size: 8pt;
    margin-bottom: 2px;
}}
.page.compact .skill-category {{
    margin-bottom: 10px;
}}
.page.compact .skill-cat-label {{
    font-size: 8pt;
    margin-bottom: 5px;
    padding-bottom: 2px;
    border-bottom-width: 1px;
}}
.page.compact .chip {{
    padding: 1.5px 7px;
    font-size: 7.5pt;
    margin: 1.5px 2px;
}}
.page.compact .project-entry {{
    margin-bottom: 10px;
}}
.page.compact .project-name {{
    font-size: 8.5pt;
}}
.page.compact .tech-tag {{
    font-size: 7pt;
    padding: 0.5px 5px;
    margin: 1.5px 2px;
}}

</style>
</head>
<body>
<div class="page clearfix {"compact" if is_compact else ""}">

    <!-- ═══ LEFT COLUMN ═══ -->
    <div class="left-col">

        <!-- Header -->
        <div class="header">
            <div class="candidate-name">{_esc(full_name)}</div>
            {f'<div class="candidate-role">{role_title}</div>' if role_title else ''}
            <div class="contacts">{contacts_html}</div>
        </div>

        <!-- Summary -->
        <div class="section">
            <div class="section-title">Summary</div>
            <div class="summary-text">{summary_text}</div>
        </div>

        <!-- Experience -->
        {experience_section}

        <!-- Projects -->
        {projects_section}

    </div>

    <!-- ═══ RIGHT COLUMN ═══ -->
    <div class="right-col">

        <!-- Skills -->
        {skills_section}

        <!-- Education -->
        {education_section}

        <!-- Certifications -->
        {certs_section}

    </div>

</div>
</body>
</html>"""

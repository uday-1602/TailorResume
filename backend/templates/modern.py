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
from datetime import datetime

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
    page_limit: int = 1,
) -> str:
    """
    Generate a modern two-column resume PDF using HTML + Playwright (headless Chromium).

    Args:
        original_profile: Parsed candidate data from profile_analyzer.
        job_spec:         Parsed job requirements from job_scraper.
        gap_report:       Gap analysis output.
        user_answers:     Chatbot Q&A from the interview step.
        output_pdf_path:  Absolute path where the final PDF should be written.
        page_limit:       1 for junior/mid (< 5 years), 2 for senior (>= 5 years).

    Returns:
        JSON string of the generated resume content
        (stored in final_latex_source for graph state compatibility).
    """
    print(f"\n[NODE] ---> Executing Modern HTML Resume Engine (page_limit={page_limit})...")

    # Step 1 — LLM generates structured resume content as JSON
    resume_data = _generate_resume_json(original_profile, job_spec, gap_report, user_answers, page_limit)

    # Step 2 — Build a standalone HTML document
    html_content = _build_html(resume_data, original_profile, page_limit)

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
    page_limit: int = 1,
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

    page_label = "single-page" if page_limit == 1 else "two-page"
    exp_count_rule = "strictly 1-2 most recent entries (select the most relevant, omit others)" if page_limit == 1 else "2-4 most recent entries (you have 2 pages, do NOT truncate)"
    exp_bullets_rule = "max 3 bullets per entry" if page_limit == 1 else "4-5 bullets"
    proj_count_rule = "strictly 1-2 most relevant projects (omit others)" if page_limit == 1 else "strictly 3-4 most relevant projects (omit others)"
    proj_bullets_rule = "max 2 bullets per project" if page_limit == 1 else "2-3 bullets"
    page_budget_rule = (
        "RULE 8 — SINGLE PAGE: Keep all content extremely concise. Under 18 words per bullet. Omit less relevant entries. Everything MUST fit on exactly one page."
        if page_limit == 1 else
        "RULE 8 — TWO PAGES: You have a 2-page budget. Fill it with substantial professional content, but strictly limit to 3-4 projects and 2-4 experiences. Each project bullet under 18 words."
    )

    sys_instruction = f"""\
You are an expert technical resume writer. Your task is to generate tailored resume content \
as a SINGLE valid JSON object — no markdown, no code fences, no explanation.

=======================================================================
OUTPUT FORMAT — STRICTLY VALID JSON, NOTHING ELSE
=======================================================================

Return ONLY this JSON structure (all keys required):

{{
  "current_role_title": "<most recent role title, e.g. 'Senior Data Engineer'>",
  "summary": "<2-3 sentences, see RULE 1 below>",
  "skills": [
    {{"category": "<Category Name>", "items": ["<Skill1>", "<Skill2>", ...]}},
    ...
  ],
  "experience": [
    {{
      "organization": "<Organization Name>",
      "role": "<Role Title>",
      "period": "<e.g. Sep 2025 – Present>",
      "bullets": ["<action-verb bullet>", ...]
    }},
    ...
  ],
  "projects": [
    {{
      "name": "<Project Name>",
      "tech": ["<Tech1>", "<Tech2>", ...],
      "bullets": ["<action-verb bullet>", ...]
    }},
    ...
  ],
  "education": [
    {{
      "institution": "<Institution Name>",
      "degree": "<Degree / Course Name>",
      "period": "<e.g. Expected Jun 2027>",
      "score": "<e.g. CGPA: 8.68/10 or Percentage: 85%>"
    }},
    ...
  ],
  "certifications": ["<Cert Name>", ...]
}}

=======================================================================
CONTENT RULES (generating a {page_label} resume)
=======================================================================

RULE 1 — SUMMARY (2-3 sentences, highly tailored to the target job description):
  Create a highly compelling, custom professional summary that immediately frames the candidate as the ideal fit for the target job.
  Guidelines:
  - Address Target Value Proposition: Directly connect the candidate's background to the core themes and critical keywords of the target job description.
  - Position Identity & Seniority: Frame the candidate's role title and identity to match the scope and expectations of the target position.
  - Industry Verticals: If the candidate has worked in specific industry sectors (e.g. "NBFC", "banking", "fintech", "healthcare", "manufacturing"), explicitly name those sectors in the summary. This is a key signal recruiters look for.
  - Preserve Original Highlights: If their original resume/profile explicitly mentions years of experience (e.g. "3+ years", "16+ years") or important industry domains, you MUST preserve these details.
  - Keep it Truthful: Do NOT fabricate experiences or technical tools they do not possess.

RULE 2 — SKILLS (4-5 categories):
  Pull skills ONLY from core_technical_skills AND skills the candidate confirmed in their answers.
  DO NOT include any skill not present in the candidate profile or user answers.

RULE 3 — EXPERIENCE ({exp_count_rule}):
  Use {exp_bullets_rule} per entry. Do NOT arbitrarily truncate or delete bullets from the original profile. Each bullet: action-verb first, under 20 words.
  Weave in required job skills and keywords from the job description ONLY where the candidate has genuine technical exposure.
  Career Progression Framing (IMPORTANT for recruiters):
  - Frame bullets to show growth trajectory and increasing scope over time.
  - Where truthfully present: mention team sizes, direct reports, cross-functional reach (e.g. "Led a 5-member data engineering team").
  - Use increasingly senior action verbs for more recent roles: "Implemented" -> "Architected" -> "Spearheaded".
  - Highlight business scale (users, transactions, data volumes) ONLY if mentioned in the source profile. Do NOT fabricate metrics.

RULE 4 — PROJECTS ({proj_count_rule}):
  Select projects with the HIGHEST overlap to the target job's required skills. Omit unrelated ones.
  Use {proj_bullets_rule} per project. Each bullet under 18 words, action-verb first.
  Actively map and frame the project details using the target job's vocabulary.
  DO NOT fabricate metrics, percentages, or counts not in the source data. Describe impact qualitatively instead.

RULE 5 — EDUCATION: List ALL entries from the profile. Include CGPA or percentage if present.

RULE 6 — CERTIFICATIONS: Include ALL certifications from profile or user answers. \
Recruiters scan for certs early — do not omit them. Empty array [] only if truly none exist.

RULE 7 — TRUTHFULNESS (MANDATORY):
  NEVER include skills, technologies, or achievements not explicitly in the candidate's profile \
or confirmed via user answers. Every skill chip that appears must be genuinely owned by the candidate.

{page_budget_rule}

RULE 9 — VOCABULARY DIVERSITY (MANDATORY):
  Never repeat the same action verbs (such as 'implemented', 'designed', 'developed', 'led') more than twice across the entire resume. Use a rich and diverse set of action verbs (e.g., 'architected', 'engineered', 'streamlined', 'orchestrated', 'executed', 'formulated', 'spearheaded', 'pioneered', 'optimized', 'modernized').
"""

    prompt_payload = (
        f"CANDIDATE DATA:\n{json.dumps(original_profile, indent=2)}\n\n"
        f"CURRENT DATE/YEAR (for calculating experience duration): {datetime.now().strftime('%B %Y')}\n\n"
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


def _build_html(data: Dict[str, Any], profile: Dict[str, Any], page_limit: int = 1) -> str:
    """
    Construct a complete, self-contained HTML document styled as a
    modern two-column resume. Playwright renders this to A4 PDF.
    For page_limit=2, two explicit A4-height page divs are emitted.
    """
    # Compact layout only applies on page_limit=1 when content is dense
    exp_count = len(data.get("experience", []))
    proj_count = len(data.get("projects", []))
    edu_count = len(data.get("education", []))
    cert_count = len(data.get("certifications", []))
    exp_bullets = sum(len(exp.get("bullets", [])) for exp in data.get("experience", []))
    proj_bullets = sum(len(proj.get("bullets", [])) for proj in data.get("projects", []))
    
    total_blocks = exp_count + proj_count + edu_count + (1 if cert_count > 0 else 0) + exp_bullets + proj_bullets
    is_compact = (total_blocks >= 26) if page_limit == 1 else False

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

    # --- Certifications (right column, optional) ---
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
    height: 297mm;
    max-height: 297mm;
    background: linear-gradient(to right, white 0%, white 59%, #e0e0e0 59%, #e0e0e0 calc(59% + 1px), #f7f8f9 calc(59% + 1px), #f7f8f9 100%);
    overflow: hidden;
    position: relative;
}}

.page.page-single {{
    background: white;
}}

.left-col {{
    float: left;
    width: 59%;
    padding: 20px 18px 20px 30px;
}}

.right-col {{
    float: left;
    width: 41%;
    padding: 20px 30px 20px 18px;
}}

.full-width-col {{
    width: 100%;
    padding: 0 30px 30px 30px;
}}

.clearfix::after {{
    content: '';
    display: table;
    clear: both;
}}

/* ── Header ── */
.header-full {{
    width: 100%;
    padding: 25px 30px 15px 30px;
    border-bottom: 2.5px solid #0d9488;
    background: white;
    position: relative;
    z-index: 10;
}}

.header-p2 {{
    width: 100%;
    padding: 15px 30px;
    border-bottom: 1px solid #e0e0e0;
    margin-bottom: 20px;
    font-size: 8.5pt;
    color: #6b7280;
    overflow: hidden;
}}

.header-p2-name {{
    float: left;
    font-weight: bold;
}}

.header-p2-page {{
    float: right;
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

/* ── Prevent entries splitting across pages ── */
.exp-entry, .project-entry, .edu-entry, .skill-category {{
    break-inside: avoid;
    page-break-inside: avoid;
}}

/* ── 2-page: page break between page divs ── */
.page, .page-single {{
    page-break-after: always;
    break-after: page;
}}
.page:last-child, .page-single:last-child {{
    page-break-after: avoid;
    break-after: avoid;
}}

/* ── Compact layout overrides ── */
.page.compact, .page-single.compact {{
    font-size: 9pt;
    line-height: 1.32;
}}
.page.compact .left-col {{
    float: left;
    width: 59%;
    padding: 15px 14px 15px 22px;
}}
.page.compact .right-col {{
    float: left;
    width: 41%;
    padding: 15px 22px 15px 14px;
}}
.page.compact .full-width-col {{
    padding: 0 22px 22px 22px;
}}
.page.compact .header-full {{
    padding: 15px 22px 10px 22px;
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
{_build_page_html(
    page_limit, is_compact,
    full_name, role_title, contacts_html, summary_text,
    data, skills_section, certs_section, education_section,
    experience_html, projects_section,
    _esc
)}
</body>
</html>"""


def _build_page_html(
    page_limit, is_compact,
    full_name, role_title, contacts_html, summary_text,
    data, skills_section, certs_section, education_section,
    experience_html, projects_section,
    esc_fn,
) -> str:
    """Build the page body HTML based on page_limit."""
    compact_class = "compact" if is_compact else ""

    if page_limit == 1:
        # ── Single page: right col = Skills → Certs → Education ──────────────
        return f"""
<div class="page clearfix {compact_class}">

    <!-- Header -->
    <div class="header-full">
        <div class="candidate-name">{esc_fn(full_name)}</div>
        {f'<div class="candidate-role">{role_title}</div>' if role_title else ''}
        <div class="contacts">{contacts_html}</div>
    </div>

    <!-- ═══ LEFT COLUMN ═══ -->
    <div class="left-col">

        <!-- Summary -->
        <div class="section">
            <div class="section-title">Summary</div>
            <div class="summary-text">{summary_text}</div>
        </div>

        <!-- Experience -->
        <div class="section"><div class="section-title">Experience</div>{experience_html}</div>

        <!-- Projects -->
        {projects_section}

    </div>

    <!-- ═══ RIGHT COLUMN ═══ -->
    <div class="right-col">

        <!-- Skills -->
        {skills_section}

        <!-- Certifications (before Education per recruiter priority) -->
        {certs_section}

        <!-- Education -->
        {education_section}

    </div>

</div>"""

    else:
        # ── Two pages: split experience 1-2 on page 1, rest + projects on page 2 ──
        all_exp = data.get("experience", [])
        exp_p1 = all_exp[:2]
        exp_p2 = all_exp[2:]

        def _exp_html(entries):
            html = ""
            for exp in entries:
                org = esc_fn(exp.get("organization") or "")
                role = esc_fn(exp.get("role") or "")
                period = esc_fn(exp.get("period") or "")
                bullets = "".join(f"<li>{esc_fn(b)}</li>" for b in exp.get("bullets", []) if b)
                if org:
                    html += f"""
            <div class="exp-entry">
                <div class="exp-header">
                    <span class="exp-org">{org}</span>
                    <span class="exp-period">{period}</span>
                </div>
                <div class="exp-role-wrap">
                    <div class="exp-role">{role}</div>
                </div>
                {"<ul class='bullets'>" + bullets + "</ul>" if bullets else ""}
            </div>"""
            return html

        exp_p1_html = _exp_html(exp_p1)
        exp_p2_html = _exp_html(exp_p2)
        exp_p2_section = (
            f'<div class="section"><div class="section-title">Experience (cont.)</div>{exp_p2_html}</div>'
            if exp_p2_html else ""
        )

        return f"""
<div class="page clearfix {compact_class}">

    <!-- Header -->
    <div class="header-full">
        <div class="candidate-name">{esc_fn(full_name)}</div>
        {f'<div class="candidate-role">{role_title}</div>' if role_title else ''}
        <div class="contacts">{contacts_html}</div>
    </div>

    <!-- ═══ PAGE 1 LEFT ═══ -->
    <div class="left-col">

        <!-- Summary -->
        <div class="section">
            <div class="section-title">Summary</div>
            <div class="summary-text">{summary_text}</div>
        </div>

        <!-- Experience (first 2 entries) -->
        <div class="section"><div class="section-title">Experience</div>{exp_p1_html}</div>

    </div>

    <!-- ═══ PAGE 1 RIGHT ═══ -->
    <div class="right-col">

        <!-- Skills -->
        {skills_section}

        <!-- Certifications -->
        {certs_section}

    </div>

</div>

<!-- ═══ PAGE 2 (Single column full width layout) ═══ -->
<div class="page page-single clearfix {compact_class}">

    <div class="header-p2">
        <span class="header-p2-name">{esc_fn(full_name)}</span>
        <span class="header-p2-page">Page 2 of 2</span>
    </div>

    <div class="full-width-col">

        <!-- Experience continuation (if any) -->
        {exp_p2_section}

        <!-- Projects -->
        {projects_section}

        <!-- Education -->
        {education_section}

    </div>

</div>"""


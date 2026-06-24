import os
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
import requests
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

class JobSpecificationSchema(BaseModel):
    role_title: str = Field(description="The formal title of the job position.")
    company_name: Optional[str] = Field(None, description="The name of the hiring organization if explicitly mentioned.")
    required_hard_skills: List[str] = Field(description="Explicit programming languages, frameworks, developer tools, cloud services, or technical methodologies required.")
    preferred_or_bonus_skills: List[str] = Field(description="Nice-to-have technical skills, specialized domains, secondary frameworks, or optional certifications.")
    experience_ceilings: str = Field(description="The required years of experience, degree benchmarks, or seniority expectations specified.")
    core_responsibilities: List[str] = Field(description="Clean, summarized bullet points detailing the daily operations, system expectations, or deliverables of the role.")

# extraction logic via json mode
def scrape_raw_html_from_url(url: str) -> str:
    """
    Ingests a target job link, performs professional web requests handling,
    and returns stripped, clean text elements using BeautifulSoup.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_with_retry():
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp

    response = _fetch_with_retry()
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script, style, and navigation tags to eliminate markup noise
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.extract()

    text = soup.get_text(separator="\n", strip=True)
    lowered = text.lower()
    
    # Common bot-detection or redirection keywords
    blocked_signatures = [
        "please click here if you are not redirected",
        "enablejs",
        "captcha",
        "robot check",
        "hcaptcha",
        "recaptcha",
        "checking your browser",
        "access denied",
        "security checkpoint",
        "pardon our interruption"
    ]
    is_blocked = any(sig in lowered for sig in blocked_signatures)
    
    if len(text) < 400 or is_blocked:
        raise ValueError(
            "Live URL returned a redirect, noscript, or anti-bot challenge page instead of job details."
        )
        
    return text

def job_extraction(url: Optional[str] = None, fallback_file: str = "job_description.txt") -> Dict[str, Any]:
    """
    Independent execution layer for Phase 2.
    Scrapes a live URL or reads a local pasted file, enforcing JSON schema output validation.
    """
    raw_job_text = ""
    if url:
        try:
            print(f"\n[1/3] Attempting live network request to: {url}...")
            raw_job_text = scrape_raw_html_from_url(url)
            print("[SUCCESS] Live HTML content retrieved and cleaned successfully.")
        except Exception as e:
            print(f"[WARNING] Live scraping failed due to anti-bot blocks or network error: {str(e)}")
            print(f"Falling back to checking local file footprint: '{fallback_file}'...")

    if not raw_job_text:
        if not os.path.exists(fallback_file):
            with open(fallback_file, "w", encoding = "utf-8") as f:
                f.write("PASTE YOUR PROTECTED LINKEDIN/INDEED/CORPORATE JOB TEXT HERE")
            raise FileNotFoundError(
                f"\n[CRITICAL] No data available. Live scrape failed, and '{fallback_file}' was empty or not found.\n"
                f"Action Required: A placeholder file has been generated. Paste the raw text of the job description into it and run again."
            )
        
        print(f"\n[1/3] Reading manually staged text data from: {fallback_file}...")
        with open(fallback_file, "r", encoding = "utf-8") as f:
            content = f.read().strip()
            
        # Check if the fallback content is just a URL itself
        if content.startswith(("http://", "https://")) or (len(content.split()) == 1 and "." in content):
            raise ValueError(
                "Live URL scraping failed due to redirection/anti-bot protection, "
                "and no fallback job description was provided. Please copy and paste the job description text manually."
            )
        raw_job_text = content
        
    truncated_text = raw_job_text[:12000]

    print(f"[2/3] Initializing AI model with strict structured output mapping...")
    # Map custom AWS env vars to standard boto3/botocore vars
    if os.getenv("AWS_ACCESS_KEY") and not os.getenv("AWS_ACCESS_KEY_ID"):
        os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY")
    if os.getenv("AWS_SECRET_KEY") and not os.getenv("AWS_SECRET_ACCESS_KEY"):
        os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_KEY")

    model_id = os.getenv("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")

    llm = init_chat_model(
        model=model_id,
        model_provider="bedrock",
        temperature=0,
        max_tokens=4096,
        region_name=region
    )
    
    structured_llm = llm.with_structured_output(JobSpecificationSchema)

    sys_instruction = (
        "You are an elite enterprise technical sourcing engine. Analyze the provided text of a job posting.\n\n"
        "Pay meticulous attention to technical items—including specific cloud-native architectures, "
        "AI orchestration frameworks, specialized databases, development stacks, and systems tooling. "
        "Do not leave raw, unparsed paragraphs inside list fields. Isolate distinct technologies "
        "cleanly into separate, searchable strings to prepare for a semantic matrix matching process."
    )

    print("[3/3] Sending payload to model and applying Pydantic constraints...")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _invoke_with_retry():
        return structured_llm.invoke([
            ("system", sys_instruction),
            ("user", f"Raw Scraped Job Content:\n\n{truncated_text}")
        ])

    response = _invoke_with_retry()
    return response.model_dump()

if __name__ == "__main__":
    TARGET_URL = "https://www.naukri.com/job-listings-senior-artificial-intelligence-machine-learning-engineer-ciklum-pune-chennai-5-to-9-years-090626016861?src=sharedjd&utmCampaign=pwajd&utmSource=share"

    print("=" * 70)
    print("STARTING PHASE 2: COMPONENT VERIFICATION (JOB SPEC SCRAPER)")
    print("=" * 70)

    try:
        job_json = job_extraction(url = TARGET_URL)
        print("\n" + "=" * 30 + " EXTRACTION SUCCESSFUL " + "=" * 30)
        print(json.dumps(job_json, indent=2))
        print("=" * 80)
        print("\nVerification Complete! Job requirements cleanly separated into arrays.")

    except Exception as e:
        print(f"\n[EXCEPTION DETECTED] Lifecycle halted: {str(e)}")
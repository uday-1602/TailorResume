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

    return soup.get_text(separator="\n", strip=True)

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
            raw_job_text = f.read()
        
    truncated_text = raw_job_text[:12000]

    print(f"[2/3] Initializing AI model with explicit native JSON Mode formatting...")
    llm = init_chat_model(
        model="openai/gpt-oss-120b",
        model_provider="groq",
        temperature=0,
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    parser = PydanticOutputParser(pydantic_object = JobSpecificationSchema)

    sys_instruction = (
        "You are an elite enterprise technical sourcing engine. Analyze the provided text of a job posting.\n\n"
        "Your task is to parse this information into a structured JSON string that aligns perfectly with the formatting instructions below.\n"
        f"{parser.get_format_instructions()}\n\n"
        "Pay meticulous attention to technical items—including specific cloud-native architectures, "
        "AI orchestration frameworks, specialized databases, development stacks, and systems tooling. "
        "Do not leave raw, unparsed paragraphs inside list fields. Isolate distinct technologies "
        "cleanly into separate, searchable strings to prepare for a semantic matrix matching process."
    )

    print("[3/3] Emitting payload to Groq gateway and executing schema parsing...")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _invoke_with_retry():
        return llm.invoke([
            ("system", sys_instruction),
            ("user", f"Raw Scraped Job Content:\n\n{truncated_text}")
        ])

    response = _invoke_with_retry()
    parsed_output = parser.parse(response.content)
    return parsed_output.model_dump()

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
import os
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pypdf import PdfReader
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

class ProjectSchema(BaseModel):
    title: str = Field(description = "The name of the project.")
    technologies: List[str] = Field(description = "List of specific technologies, frameworks, libraries, microcontrollers, or SDKs used.")
    key_achievements: List[str] = Field(description = "Bullet points describing what was built, features implemented, or technical challenges resolved.")

class ExperienceSchema(BaseModel):
    role: str = Field(description = "The professional job title, internship position, or trainee role.")
    organization: str = Field(description = "The company, institution, university group, or organization name.")
    duration: Optional[str] = Field(None, description = "The timeline, date range, or duration of the experience.")
    highlights: List[str] = Field(description = "Key responsibilities, technical tools leveraged, and direct outcomes.")

class EducationDetail(BaseModel):
    institution: str
    degree: str
    timeline: str
    cgpa: Optional[str] = Field(None, description = "The candidate's CGPA or GPA if mentioned.")
    percentage: Optional[str] = Field(None, description = "The candidate's percentage score if mentioned.")

class CandidateProfileSchema(BaseModel):
    full_name: str = Field(description = "The candidate's full legal name.")
    email: Optional[str] = Field(None, description = "The candidate's email.")
    phone: Optional[str] = Field(None, description = "The candidate's phone number.")
    github_handle: Optional[str] = Field(None, description = "The candidate's github handle.")
    linkedin_handle: Optional[str] = Field(None, description = "The candidate's linkedin profile URL or username.")
    core_technical_skills: List[str] = Field(default_factory=list, description="A comprehensive, clean list of programming languages, tools, frameworks, databases, and cloud services explicitly mentioned.")
    professional_experience: List[ExperienceSchema] = Field(default_factory=list, description="List of internships, trainee positions, or formal engineering roles.")
    engineered_projects: List[ProjectSchema] = Field(default_factory=list, description="List of software applications, extensions, hardware integrations, or AI systems developed.")
    education: List[EducationDetail] = Field(default_factory=list, description="List of education details.")
    certifications: Optional[List[str]] = Field(default_factory=list, description="List of professional certifications, licenses, or courses completed.")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Ingests a local PDF and extracts raw text data page by page."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Target document asset not found at: {pdf_path}")
    
    combined_text = ""
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                combined_text += text

    return combined_text

def profile_extraction(pdf_path: str) -> Dict[str, Any]:
    """
    Independent execution layer for Phase 1 leveraging explicit JSON Mode 
    and native Pydantic string parsing to eliminate tool-calling exceptions.
    """
    print(f"\n[1/3] Reading target file: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)

    print(f"Initializing AI model with strict structured output mapping...")
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
    
    structured_llm = llm.with_structured_output(CandidateProfileSchema)

    sys_instruction = (
        "You are an elite enterprise technical recruiting engine. Process the raw text of the candidate's resume.\n\n"
        "Pay meticulous attention to technical items—including specific cloud-native architectures, "
        "AI orchestration frameworks, specialized databases, development stacks, and systems tooling. "
        "Do not bundle separate systems into a single generic item. Isolate distinct technologies "
        "cleanly into separate, searchable strings to ensure accurate downstream semantic matching."
    )

    print("[3/3] Sending payload to model and applying Pydantic constraints...")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _invoke_with_retry():
        return structured_llm.invoke([
            ("system", sys_instruction),
            ("user", f"Raw Resume Text Data:\n\n{raw_text}")
        ])

    response = _invoke_with_retry()
    return response.model_dump()

if __name__ == "__main__":
    
    TARGET_RESUME = "resume.pdf"

    print("=" * 70)
    print("Starting phase 1: Component Verfication")
    print("=" * 70)

    try:
        profile_json = profile_extraction(TARGET_RESUME)
        print(json.dumps(profile_json, indent = 2))
        print("=" * 80)
        print("\nVerification Complete! Check the output above to ensure all your core projects and skills parsed perfectly.")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Extraction failed: {str(e)}")

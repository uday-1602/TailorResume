import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

class TechnicalInterviewQuestions(BaseModel):
    clarification_questions: List[str] = Field(
        description="A list of exactly 3 highly targeted, strategic questions designed to uncover hidden candidate skills matching identified technical gaps."
    )

def generate_targeted_interview_questions(candidate_profile: Dict[str, Any], gap_report: Dict[str, Any]) -> List[str]:
    """
    Analyzes the structural candidate profile and the gap analysis report,
    generating personalized, conversational questions to extract relevant tech domain metrics.
    """
    print("\n[NODE] ---> Executing Targeted Interview Interviewer Node...")

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
        temperature=0.4,
        max_tokens=4096,
        region_name=region
    )
    
    structured_llm = llm.with_structured_output(TechnicalInterviewQuestions)

    sys_instruction = (
        "You are an elite, professional executive tech career coach. Review the candidate's profile "
        "alongside their structured gap analysis report.\n\n"
        "Your task is to identify the most critical high-severity technical gaps (e.g., missing frameworks, architecture tools). "
        "Generate a structured response containing EXACTLY 3 professional, direct, and conversational questions. "
        "You MUST return exactly 3 questions in the list — no more, no less.\n\n"
        "Address the candidate by their first name if available. Ask them if they have relevant unlisted experience, "
        "academic project exposure, or specific variations of work that can be contextualized to fill the job requirements. "
        "Keep each question concise and direct — one focused question per gap."
    )

    evaluation_payload = {
        "candidate_name": candidate_profile.get("full_name", "Candidate"),
        "identified_gaps": gap_report.get("identified_gaps", [])
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _invoke_with_retry():
        return structured_llm.invoke([
            ("system", sys_instruction),
            ("user", f"Target Interview Context Variables:\n\n{json.dumps(evaluation_payload, indent=2)}")
        ])

    response = _invoke_with_retry()
    return response.clarification_questions

if __name__ == "__main__":
    print("=" * 70)
    print("STARTING RE-ALIGNED INTERACTIVE NODE VERIFICATION")
    print("=" * 70)
    
    # Passing your real structured profile generated in Phase 1
    CANDIDATE_DATA = {
        "full_name": "UDAY SALATHIA",
        "core_technical_skills": ["Python", "AWS Bedrock", "AWS S3", "Retrieval-Augmented Generation (RAG) systems"]
    }
    
    # Passing your real gap analysis data generated in Phase 3
    GAP_ANALYSIS_DATA = {
        "identified_gaps": [
            {"missing_skill": "LangGraph orchestrations and state-management", "severity": "HIGH"},
            {"missing_skill": "FastAPI for production-tier REST endpoints", "severity": "HIGH"},
            {"missing_skill": "Pinecone vector database design", "severity": "HIGH"}
        ]
    }
    
    try:
        questions = generate_targeted_interview_questions(CANDIDATE_DATA, GAP_ANALYSIS_DATA)
        print("\n" + "=" * 25 + " AGENT INTERVIEW DISCOVERY QUESTIONS " + "=" * 25)
        for idx, question in enumerate(questions, 1):
            print(f"\n{idx}. {question}")
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Interview Node Execution Failed: {str(e)}")

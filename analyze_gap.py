import os
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv

load_dotenv()

class SkillMatchSchema(BaseModel):
    skill_name: str = Field(description="The name of the technology, tool, or framework.")
    match_status: str = Field(description="Must be exactly 'FULL_MATCH' or 'PARTIAL_MATCH'.")
    context: str = Field(description="Brief analysis explaining where it appears in the candidate's history vs what the job requires.")

class TechnicalGapSchema(BaseModel):
    missing_skill: str = Field(description="The core technology, library, framework, or methodology requested by the job that the candidate lacks.")
    severity: str = Field(description="Must be 'HIGH' (critical requirement) or 'LOW' (preferred/nice-to-have bonus skill).")
    justification: str = Field(description="Explain why this gap is critical based on the job's core responsibilities.")

class GapAnalysisReportSchema(BaseModel):
    alignment_score_percentage: int = Field(description="An overall fit percentage estimate (0-100) based on hard requirements.")
    identified_matches: List[SkillMatchSchema] = Field(description="List of technologies that match fully or partially.")
    identified_gaps: List[TechnicalGapSchema] = Field(description="List of critical technologies missing from the candidate's profile.")
    strategic_recommendation: str = Field(description="A high-level directive on how the candidate should tailor their resume to clear automated screening filters.")

def gap_analysis(candidate_profile: Dict[str, Any], job_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Independent execution layer for Phase 3.
    Compares the candidate JSON and job specification JSON using strict JSON Mode.
    """
    print(f"[1/2] Initializing Gap Analyzer with explicit native JSON Mode formatting...")
    llm = init_chat_model(
        model="openai/gpt-oss-120b",
        model_provider="groq",
        temperature=0,
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    parser = PydanticOutputParser(pydantic_object=GapAnalysisReportSchema)

    sys_instruction = (
        "You are an elite enterprise technical assessment engine. Your task is to perform a granular matrix "
        "comparison between a candidate's structured profile and a target job specification.\n\n"
        "Generate a structured JSON response matching the formatting guidelines below:\n"
        f"{parser.get_format_instructions()}\n\n"
        "Evaluate the technologies with nuance. Match technologies based on core capability rather than exact string equivalence. "
        "For example, if a job demands a specialized feature set or integration pattern (e.g., 'AWS Bedrock Knowledge Bases and vector indexing') "
        "and the candidate lists foundational expertise with it (e.g., 'AWS Bedrock', 'AWS S3', 'RAG systems'), classify it intelligently "
        "as a partial match. Clearly outline what specific sub-tools or framing the candidate lacks to bridge semantic gaps."
    )

    user_payload = {
        "candidate_data" : candidate_profile,
        "target_job_specification" : job_spec
    }

    print("[2/2] Emitting comparison matrix payload to Groq gateway...")
    response = llm.invoke([
        ("system", sys_instruction),
        ("user", f"Matrix Evlauation Target: \n\n{json.dumps(user_payload, indent = 2)}")
    ])

    parsed_output = parser.parse(response.content)
    return parsed_output.model_dump()

if __name__ == "__main__":
    print("=" * 70)
    print("STARTING PHASE 3: COMPONENT VERIFICATION (GAP ANALYZER)")
    print("=" * 70)

    ACTUAL_CANDIDATE_PROFILE = {
        "full_name": "UDAY SALATHIA",
        "core_technical_skills": [
            "C", "C++", "Python", "Pandas", "NumPy", "boto3", "SQL", "Java", "JavaScript",
            "AWS Bedrock", "AWS S3", "Retrieval-Augmented Generation (RAG) systems",
            "Qiskit", "Large Language Model (LLM) integration", "Git", "GitHub", "Unity",
            "Next.js", "Node.js", "Supabase", "Flask", "Arduino", "RFID"
        ],
        "professional_experience": [
            {
                "role": "Project Trainee Intern",
                "organization": "Nihilent Limited",
                "duration": "Jan 2026 - present",
                "highlights": [
                    "Implemented and tested Generative AI features using AWS Bedrock to solve real-world enterprise problems",
                    "Contributed to project management and technical documentation",
                    "Partnered with cross functional teams to ensure technical builds address client pain points"
                ]
            }
        ],
        "engineered_projects": [
            {
                "title": "CarAI – RAG-based Analysis System",
                "technologies": ["AWS S3", "AWS Bedrock", "Retrieval-Augmented Generation (RAG)", "Generative AI"],
                "key_achievements": [
                    "Developed a Retrieval-Augmented Generation system that enables users to chat with car datasheets for instant technical detail retrieval",
                    "Integrated AWS S3 with AWS Bedrock's retrieve API to create a searchable knowledge base"
                ]
            }
        ]
    }

    ACTUAL_JOB_SPECIFICATION = {
        "role_title": "Senior AI & Platform Engineer",
        "company_name": "CloudScale Solutions",
        "required_hard_skills": [
            "Advanced Python systems development",
            "LangGraph orchestrations and state-management",
            "AWS Bedrock Knowledge Bases and vector indexing",
            "FastAPI for production-tier REST endpoints",
            "PostgreSQL relational database design",
            "Pinecone vector database design"
        ],
        "preferred_or_bonus_skills": [],
        "experience_ceilings": "Not specified",
        "core_responsibilities": [
            "Transition legacy multi-step prompts into robust, state-based Multi-Agent pipelines",
            "Build automated document indexing structures using cloud native object storage",
            "Optimize semantic search routing strategies to reduce LLM latency and token bloat"
        ]
    }

    try:
        analysis_json = gap_analysis(ACTUAL_CANDIDATE_PROFILE, ACTUAL_JOB_SPECIFICATION)
        print("\n" + "=" * 30 + " GAP ANALYSIS COMPLETE " + "=" * 30)
        print(json.dumps(analysis_json, indent=2))
        print("=" * 83)
        print("\nVerification Complete! Match matrices and structural gaps cleanly generated.")
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Gap Analysis execution failed: {str(e)}")
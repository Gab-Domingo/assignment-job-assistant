from models import UserProfile, ScrapedJobData, ResumeAnalysisResult
from typing import Optional, Dict, Any
import json
from datetime import datetime

def serialize_for_prompt(obj: Any) -> Any:
    """Helper function to serialize objects for prompt generation"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'model_dump'):
        return obj.model_dump(mode='json')  # Use Pydantic's json mode
    return obj

def _format_experience(work_history: list) -> str:
    """Format work history for prompt"""
    return "\n".join([
        f"- {exp.title} at {exp.company} ({exp.start_date} to {exp.end_date}): {exp.description}"
        for exp in work_history
    ])

def _format_education(education: list) -> str:
    """Format education for prompt"""
    return "\n".join([
        f"- {edu.degree} in {edu.field_of_study} from {edu.institution} ({edu.graduation_date})"
        for edu in education
    ])


def get_resume_analysis_prompt(profile: UserProfile, job_data: ScrapedJobData) -> str:
    """
    Generate prompt for overall resume analysis
    """
    # Handle both Pydantic models and dictionaries
    profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else profile
    job_data_dict = job_data.model_dump() if hasattr(job_data, 'model_dump') else job_data
    
    profile_json = json.dumps(profile_data, indent=2)
    job_data_json = json.dumps(job_data_dict, indent=2)
    
    return f"""You are an expert resume analyzer. Analyze this candidate's profile against the job requirements.

    CANDIDATE PROFILE:
    {profile_json}

    JOB DETAILS:
    {job_data_json}

    IMPORTANT: Respond ONLY with a JSON object in the following format, with no additional text, thoughts, or explanations:
    {{
        "match_score": number between 0-100,
        "suggestions": [list of specific, actionable suggestions],
        "key_matches": [list of main areas where candidate matches requirements],
        "gaps": [list of specific gaps between profile and requirements]
    }}"""

def get_section_analysis_prompt(
    profile: UserProfile,
    job_data: ScrapedJobData,
    overall_match: int
) -> str:
    
    # Handle both Pydantic models and dictionaries
    profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else profile
    job_data_dict = job_data.model_dump() if hasattr(job_data, 'model_dump') else job_data
    
    profile_json = json.dumps(profile_data, indent=2)
    job_data_json = json.dumps(job_data_dict, indent=2)
    
    
    """
    Generate prompt for section-specific analysis
    """
    return f"""Given the overall match score of {overall_match}, analyze each section of the resume
    against the job requirements in detail.

    CANDIDATE PROFILE:
    {profile_json}

    JOB DETAILS:
    {job_data_json}

    Provide your analysis in the following JSON format:
    {{
        "section_scores": {{
            "experience": 0-100,
            "skills": 0-100,
            "education": 0-100,
            "projects": 0-100
        }},
        "skills_matched": [list of matched skills],
        "skill_gaps": [list of missing skills],
        "relevant_experience": [list of most relevant experiences],
        "key_achievements": [list of achievements that match job needs],
        "improvement_priority": [ordered list of sections to improve],
        "suggestions": [section-specific improvement suggestions]
    }}
    """



def get_improvement_plan_prompt(analysis_result: ResumeAnalysisResult) -> str:
    
    # Handle both Pydantic models and dictionaries
    analysis_result_data = analysis_result.model_dump() if hasattr(analysis_result, 'model_dump') else analysis_result
    
    analysis_result_json = json.dumps(analysis_result_data, indent=2)
    
    
    """
    Generate prompt for creating improvement plan
    """
    return f"""Based on the resume analysis results, create a detailed improvement plan.

    ANALYSIS RESULTS:
    {analysis_result_json}

    Provide your plan in the following JSON format:
    {{
        "immediate_actions": [specific actions to take now],
        "short_term_goals": [goals for next 1-3 months],
        "long_term_goals": [goals for 3+ months],
        "skill_development": {{
            "technical_skills": [skills to learn/improve],
            "soft_skills": [skills to develop]
        }},
        "section_improvements": {{
            "experience": [specific improvements],
            "skills": [specific improvements],
            "education": [specific improvements],
            "projects": [specific improvements]
        }}
    }}
    """







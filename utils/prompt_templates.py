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
    
    return f"""You are an expert resume analyzer. Analyze this candidate's profile against the job requirements and provide a comprehensive breakdown for quick judgment.

    CANDIDATE PROFILE:
    {profile_json}

    JOB DETAILS:
    {job_data_json}

    IMPORTANT: Respond ONLY with a JSON object in the following format, with no additional text, thoughts, or explanations:
    {{
        "match_score": number between 0-100 (overall match score),
        "candidate_overview": "A concise 2-3 sentence summary of the candidate's fit for this role, highlighting key strengths and overall assessment",
        "section_scores": {{
            "experience": number 0-100 (how well experience matches requirements),
            "skills": number 0-100 (how well skills match must-haves and preferred),
            "education": number 0-100 (how well education matches requirements),
            "overall_fit": number 0-100 (overall cultural and role fit)
        }},
        "key_matches": [list of 3-5 main areas where candidate strongly matches requirements - be specific],
        "gaps": [list of 3-5 specific gaps or missing requirements - prioritize critical gaps first],
        "suggestions": [list of 3-5 specific, actionable suggestions for improvement],
        "quick_judgment": {{
            "strength_1": "Top strength for this role (one short phrase)",
            "strength_2": "Second strength (one short phrase)",
            "concern_1": "Top concern or gap (one short phrase)",
            "concern_2": "Second concern (one short phrase)",
            "recommendation": "shortlist" | "maybe" | "reject" (based on match score and critical requirements)
        }}
    }}
    
    Guidelines for scoring:
    - match_score: Weighted average considering all factors, prioritize must-have skills and experience
    - section_scores: Rate each section independently 0-100
    - candidate_overview: Focus on fit, not just listing qualifications
    - quick_judgment: Help recruiters make fast decisions
    - recommendation: "shortlist" for 70+, "maybe" for 50-69, "reject" for <50, but adjust based on critical gaps"""

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







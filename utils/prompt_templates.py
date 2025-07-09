from models import UserProfile, ScrapedJobData, ResumeAnalysisResult, ApplicationQuestion, GeneratedAnswer
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
# Add to utils/prompt_templates.py

def get_profile_validation_prompt(profile: UserProfile) -> str:
    
    
    # Handle both Pydantic models and dictionaries
    profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else profile
    
    
    profile_json = json.dumps(profile_data, indent=2)
    
    
    
    """
    Generate prompt for profile content validation
    """
    return f"""Please validate the following user profile for completeness, professionalism, and effectiveness.
    Analyze each section and provide feedback on the content quality.

    Profile to validate:
    {profile_json}

    Provide your analysis in the following JSON format:
    {{
        "is_valid": boolean,
        "issues": [list of specific issues found],
        "suggestions": [list of improvement suggestions],
        "score": 0-100,
    }}


    """

# Add to utils/prompt_templates.py

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


# Add to improvement_agent.py
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





# TODO: fix prompt to use resume analysis result

def get_answer_generation_prompt(
    profile: UserProfile,
    question: ApplicationQuestion,
    resume_analysis_result: ResumeAnalysisResult,
    user_answer: Optional[GeneratedAnswer] = None
) -> str:
    """
    Generate prompt for initial answer generation
    Args:
        profile: User profile data
        question: Application question
        resume_analysis_result: Results from resume analysis
        user_answer: Optional user provided answer
    Returns:
        str: Formatted prompt
    """
    # Convert to JSON-safe dictionaries using the serialize_for_prompt helper
    profile_data = serialize_for_prompt(profile)
    resume_analysis_result_data = serialize_for_prompt(resume_analysis_result)
    
    # Create and serialize job data properly
    job_data = ScrapedJobData(
        job_title=resume_analysis_result.metadata.get('job_title', ''),
        job_description=resume_analysis_result.metadata.get('job_description', '')
    )
    job_data_dict = serialize_for_prompt(job_data)  # Use the helper function
    
    # Convert to JSON strings
    profile_json = json.dumps(profile_data, indent=2)
    job_data_json = json.dumps(job_data_dict, indent=2)  # Now this should work
    resume_analysis_result_json = json.dumps(resume_analysis_result_data, indent=2)
    
    user_answer_text = f"\nUSER'S ANSWER:\n{user_answer.text}" if user_answer else ""
    
    return f"""You are an expert at crafting compelling job application answers that highlight a candidate's relevant experience and skills.
    Generate a detailed, personalized answer to the application question using the provided information.

    QUESTION:
    {question.question_text}

    USER'S ANSWER:
    {user_answer_text}

    RESUME ANALYSIS INSIGHTS:
    {resume_analysis_result_json}

    CANDIDATE PROFILE:
    {profile_json}

    JOB DETAILS:
    {job_data_json}

    INSTRUCTIONS:
    1. Focus on matching the candidate's experience with job requirements
    2. Use specific, quantifiable achievements from the profile
    3. Address the question directly and completely
    4. Maintain a professional yet engaging tone
    5. Stay within {question.max_length if question.max_length else 'a reasonable'} word limit
    6. If a user answer is provided, use it as inspiration while improving upon it

    Strictly follow the JSON format below, no additional text:
    {{
        "answer": "Your complete, polished answer",
        "key_points": [
            "List of 3-5 main points addressed in the answer"
        ],
        "profile_elements_used": [
            "Specific skills, experiences, or achievements referenced"
        ],
        "job_requirements_addressed": [
            "Key job requirements that the answer addresses"
        ],
        "reasoning": [
            "Brief explanations of why certain elements were included"
        ]
    }}
    """

def get_answer_validation_prompt(
    profile: UserProfile,
    resume_analysis_result: ResumeAnalysisResult,
    answer: GeneratedAnswer,
    question: ApplicationQuestion
) -> str:
    """
    Generate prompt for answer validation and improvement
    Args:
        profile: User profile data
        resume_analysis_result: Results from resume analysis
        answer: Initial generated answer
        question: Application question
    Returns:
        str: Formatted prompt
    """
    # Convert to JSON-safe dictionaries
    profile_data = serialize_for_prompt(profile)
    resume_analysis_result_data = serialize_for_prompt(resume_analysis_result)
    
    profile_json = json.dumps(profile_data, indent=2)
    resume_analysis_result_json = json.dumps(resume_analysis_result_data, indent=2)

    return f"""You are an expert reviewer of job application answers. Your task is to validate and improve the provided answer
    ensuring it effectively showcases the candidate's qualifications and addresses the job requirements.

    INITIAL ANSWER:
    {answer.text}

    QUESTION:
    {question.question_text}

    RESUME ANALYSIS INSIGHTS:
    {resume_analysis_result_json}

    CANDIDATE PROFILE:
    {profile_json}

    EVALUATION CRITERIA:
    1. Relevance: Does the answer directly address the question?
    2. Completeness: Are all aspects of the question addressed?
    3. Evidence: Are specific examples from the profile used effectively?
    4. Alignment: Does it address key job requirements?
    5. Clarity: Is the answer clear and well-structured?
    6. Length: Is it within the {question.max_length if question.max_length else 'appropriate'} word limit?
    7. Impact: Does it effectively communicate the candidate's value?

    Provide your analysis and improvements in the following JSON format:
    {{
        "final_answer": "The improved answer text",
        "key_points": [
            "List of main points in the improved answer"
        ],
        "skills_referenced": [
            "Specific skills mentioned and how they're relevant"
        ],
        "experience_referenced": [
            "Work experiences used and their relevance"
        ],
        "achievements_referenced": [
            "Specific achievements highlighted"
        ],
        "improvements_made": [
            "List of specific improvements from the original"
        ],
        "effectiveness_score": "Score from 0-100",
        "validation_notes": [
            "Notes on how the answer meets each evaluation criterion"
        ]
    }}
    """
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from models.user_profile import (
    UserProfile, JobSearchParams, ApplicationQuestion,
    GeneratedAnswer, ResumeAnalysisResult
)
from agents.resume_agent import ResumeAnalyzer
from agents.answer_generator import AnswerGenerator
from agents.fill_agent import UserProfileManager

app = FastAPI(
    title="AI Resume Analyzer & Answer Generator",
    description="API for analyzing resumes and generating application answers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
def get_resume_analyzer():
    return ResumeAnalyzer()

def get_answer_generator():
    return AnswerGenerator()

def get_profile_manager():
    return UserProfileManager()

@app.post("/analyze", response_model=ResumeAnalysisResult)
async def analyze_resume(
    user_profile: UserProfile,
    job_params: JobSearchParams,
    application_question: Optional[ApplicationQuestion] = None,
    resume_analyzer: ResumeAnalyzer = Depends(get_resume_analyzer)
):
    """
    Analyze a resume against job requirements.
    
    Args:
        user_profile: User's profile and resume information
        job_params: Job search parameters and requirements
        application_question: Optional application question to analyze
        
    Returns:
        ResumeAnalysisResult: Analysis results including match score and suggestions
    """
    try:
        result = await resume_analyzer.analyze_resume_and_jd(
            user_profile=user_profile,
            job_params=job_params,
            application_question=application_question
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_answer", response_model=GeneratedAnswer)
async def generate_answer(
    user_profile: UserProfile,
    job_params: JobSearchParams,
    application_question: ApplicationQuestion,
    user_answer: Optional[GeneratedAnswer] = None,
    answer_generator: AnswerGenerator = Depends(get_answer_generator)
):
    """
    Generate an optimized answer for a job application question.
    
    Args:
        user_profile: User's profile and resume information
        job_params: Job search parameters and requirements
        application_question: The question to answer
        user_answer: Optional existing answer to improve
        
    Returns:
        GeneratedAnswer: Generated or improved answer with analysis
    """
    try:
        result = await answer_generator.generate_answer(
            user_profile,
            job_params,
            application_question,
            user_answer
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

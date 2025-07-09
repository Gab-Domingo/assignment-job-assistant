from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class PersonalInfo(BaseModel):
    full_name: str
    email: str
    location: str
    professional_summary: str

class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str
    description: str
    achievements: List[str]

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    graduation_date: str
    gpa: Optional[float] = None
    relevant_coursework: Optional[List[str]] = None

class Certification(BaseModel):
    name: str
    issuer: str
    date: str
    expires: Optional[str] = None

class Skills(BaseModel):
    technical: List[str]
    soft: List[str]
    certifications: List[Certification]

class Project(BaseModel):
    name: str
    description: str
    technologies: List[str] 
    url: Optional[str] = None

class UserProfile(BaseModel):
    personal_info: PersonalInfo
    work_history: Optional[List[WorkExperience]] = None
    education: List[Education]
    skills: Skills
    projects: List[Project]

class ApplicationQuestion(BaseModel):
    question_id: str
    question_text: str
    question_type: str
    max_length: Optional[int] = None
    context: Optional[str] = None

class TailoredElements(BaseModel):
    skills_mentioned: List[str]
    experience_highlighted: List[str]
    achievements_referenced: List[str]

class AnswerMetadata(BaseModel):
    generation_timestamp: datetime
    question_id: str
    job_id: Optional[str] = None

class GeneratedAnswer(BaseModel):
    text: str
    word_count: int
    key_points_addressed: List[str]
    tailored_elements: TailoredElements
    metadata: AnswerMetadata

class JobPosting(BaseModel):
    url: str
    
class ScrapedJobData(BaseModel):
    job_title: str
    job_description: str

class ResumeAnalysisResult(BaseModel):
    match_score: int
    suggestions: List[str]
    gaps: List[str]
    key_matches: List[str]
    metadata: Dict = {}

class JobSearchParams(BaseModel):
    job_title: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None

    # Validation to ensure either URL or both job_title and location are provided
    def validate_search_params(self):
        if not any([self.url, (self.job_title and self.location)]):
            raise ValueError("Either URL or both job_title and location must be provided")

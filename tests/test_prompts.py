# tests/test_prompts.py
import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio
# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.resume_agent import ResumeAnalyzer
from utils.prompt_templates import get_resume_analysis_prompt
from models import UserProfile, JobSearchParams, GeneratedAnswer, TailoredElements, AnswerMetadata, ApplicationQuestion
from agents.answer_generator import AnswerGenerator
# Your test data
test_profile = UserProfile(
    personal_info={
        "full_name": "Gabriel Domingo",
        "email": "gabriel.domingo@gmail.com",
        "location": "Manila, Philippines",
        "professional_summary": "I am a software engineer with a passion for building scalable and efficient systems. I have experience in Python, JavaScript, and React."
    },
    work_history=[
        {
            "company": "Microsoft",
            "title": "Software Engineer",
            "start_date": "2020-01",
            "end_date": "2023-01",
            "description": "Developed and maintained software applications using Python, JavaScript, and React.",
            "achievements": ["Achievement 1", "Achievement 2"]
        }
    ],
    education=[
        {
            "institution": "University of the Philippines",
            "degree": "Bachelor of Science in Computer Science",
            "field_of_study": "Computer Science",
            "graduation_date": "2020",
            "gpa": 3.5,
            "relevant_coursework": ["Course 1", "Course 2"]
        }
    ],
    skills={
        "technical": ["Python", "JavaScript", "React", "Node.js", "SQL", "NoSQL"],
        "soft": ["Teamwork", "Communication", "Problem Solving", "Time Management", "Adaptability", "Leadership"],
        "certifications": []
    },
    projects=[
        {
            "name": "Project 1",
            "description": "Developed and maintained software applications using Python, JavaScript, and React.",
            "technologies": ["Python", "JavaScript", "React", "Node.js", "SQL", "NoSQL"],
            "url": "https://github.com/gabrieldomingo/project1"
        }
    ]
)

test_job_data = JobSearchParams(
    job_title="Software Engineer",
    location="Makati, Philippines"
)

test_application_question = ApplicationQuestion(
    question_id="1",
    question_text="What problems did you encounter in your previous role and how did you solve them?",
    question_type="text",
    max_length=500
)
test_generated_answer = GeneratedAnswer(
    text="I had to redesign the system which was a challenge but I was able to do it by having a well-defined plan and a team that was able to work together to achieve the goal.",
    word_count=100,
    key_points_addressed=["Redesign", "Plan", "Teamwork"],
    tailored_elements=TailoredElements(
        skills_mentioned=["Python", "JavaScript", "React", "Node.js", "SQL", "NoSQL"],
        experience_highlighted=["Software Engineer", "Microsoft"],
        achievements_referenced=["Hackathon Champion", "Best Employee of the Month"]
    ),
    metadata=AnswerMetadata(
        generation_timestamp=datetime.now(),
        question_id="1",
        job_id="1"
    )
)

def test_resume_analysis_prompt():
    """Test the resume analysis prompt generation"""
    prompt = get_resume_analysis_prompt(test_profile, test_job_data)
    print("\n=== Generated Prompt ===")
    print(prompt)
    print("=== End of Prompt ===\n")
    
    # Assertions
    assert isinstance(prompt, str)
    assert "Gabriel Domingo" in prompt
    assert "Software Engineer" in prompt
    assert "Developed and maintained software applications using Python, JavaScript, and React." in prompt

async def test_analyze_resume_and_jd():
    """Test the analyze resume and job description function"""
    resume_analyzer = ResumeAnalyzer()
    result = await resume_analyzer.analyze_resume_and_jd(test_profile, test_job_data)
    print("\n=== Analyzed Result ===")
    print(result)
    print("=== End of Result ===\n")

async def test_answer_generator():
    """Test the fill agent"""
    answer_generator = AnswerGenerator()
    result = await answer_generator.generate_answer(test_profile, test_job_data, test_application_question, test_generated_answer)
    print("\n=== Generated Answer ===")
    print(result)
    print("=== End of Generated Answer ===\n")

def test_all_prompts():
    """Test all prompt generation functions"""
    # Add more test functions here as we add more prompt templates
    # Run async tests using asyncio
    asyncio.run(test_answer_generator())
    #test_resume_analysis_prompt()
    print("All prompt tests passed!")

if __name__ == "__main__":
    test_all_prompts()
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
from models.user_profile import UserProfile, JobSearchParams, GeneratedAnswer, TailoredElements, AnswerMetadata, ApplicationQuestion
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
    """Test the analyze resume and job description function (includes Apify scraper)"""
    print("\n" + "="*60)
    print("TEST 1: Testing Apify Scraper + Gemini Analysis")
    print("="*60)
    
    try:
        resume_analyzer = ResumeAnalyzer()
        print(f"\n✓ ResumeAnalyzer initialized")
        print(f"  - Model: {resume_analyzer.model_name}")
        print(f"  - Job Title: {test_job_data.job_title}")
        print(f"  - Location: {test_job_data.location}")
        
        print("\n⏳ Starting job scraping (this may take 30-60 seconds)...")
        result = await resume_analyzer.analyze_resume_and_jd(test_profile, test_job_data)
        
        print("\n" + "="*60)
        print("✓ SCRAPER + ANALYSIS TEST PASSED")
        print("="*60)
        print(f"\nResult Summary:")
        print(f"  - Match Score: {result.match_score}/100")
        print(f"  - Key Matches: {len(result.key_matches)}")
        print(f"  - Gaps Identified: {len(result.gaps)}")
        print(f"  - Suggestions: {len(result.suggestions)}")
        print(f"\nFull Result:")
        print(result)
        print("\n" + "="*60 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR in scraper + analysis test: {str(e)}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())
        raise

async def test_answer_generator():
    """Test the answer generator with Gemini AI"""
    print("\n" + "="*60)
    print("TEST 2: Testing Gemini Answer Generation")
    print("="*60)
    
    try:
        answer_generator = AnswerGenerator()
        print(f"\n✓ AnswerGenerator initialized")
        print(f"  - Model: {answer_generator.model_name}")
        print(f"  - Question: {test_application_question.question_text}")
        
        print("\n⏳ Generating optimized answer (this may take 30-60 seconds)...")
        result = await answer_generator.generate_answer(
            test_profile, 
            test_job_data, 
            test_application_question, 
            test_generated_answer
        )
        
        print("\n" + "="*60)
        print("✓ ANSWER GENERATION TEST PASSED")
        print("="*60)
        
        if "final_answer" in result:
            final = result["final_answer"]
            print(f"\nGenerated Answer:")
            print(f"  - Text: {final.text[:200]}..." if len(final.text) > 200 else f"  - Text: {final.text}")
            print(f"  - Word Count: {final.word_count}")
            print(f"  - Key Points: {len(final.key_points_addressed)}")
            print(f"  - Skills Mentioned: {len(final.tailored_elements.skills_mentioned)}")
        else:
            print(f"\nFull Result:")
            print(result)
        
        print("\n" + "="*60 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR in answer generation test: {str(e)}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())
        raise

async def test_all_prompts():
    """Test all workflows including scraper and AI generation"""
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUITE")
    print("="*60)
    print("\nThis will test:")
    print("  1. Apify scraper integration + Gemini resume analysis")
    print("  2. Gemini AI answer generation")
    print("\nMake sure you have:")
    print("  - GEMINI_API_KEY in .env")
    print("  - APIFY_TOKEN in .env")
    print("\n" + "="*60)
    
    results = {}
    
    # Test 1: Scraper + Analysis
    try:
        results["scraper_analysis"] = await test_analyze_resume_and_jd()
        print("✅ TEST 1 PASSED: Scraper + Analysis\n")
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {str(e)}\n")
        results["scraper_analysis"] = None
    
    # Test 2: Answer Generation
    try:
        results["answer_generation"] = await test_answer_generator()
        print("✅ TEST 2 PASSED: Answer Generation\n")
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {str(e)}\n")
        results["answer_generation"] = None
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Scraper + Analysis: {'✅ PASSED' if results.get('scraper_analysis') else '❌ FAILED'}")
    print(f"Answer Generation: {'✅ PASSED' if results.get('answer_generation') else '❌ FAILED'}")
    print("="*60 + "\n")
    
    if all(results.values()):
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(test_all_prompts())
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.user_profile import (
    UserProfile, JobSearchParams, ApplicationQuestion,
    GeneratedAnswer, TailoredElements, AnswerMetadata
)

async def test_workflow_components():
    """Test each component of the workflow separately"""
    print("\n🔍 Testing Agent Workflow Components")
    print("==================================")

    results = {
        "environment": False,
        "data_loading": False,
        "agent_init": False,
        "scraping": False,
        "llm": False,
        "full_workflow": False
    }

    # 1. Test environment
    print("\n1. Testing Environment Setup...")
    try:
        required_env = ["AZURE_KEY", "AZURE_ENDPOINT", "model_name"]
        missing_env = [var for var in required_env if not os.getenv(var)]
        
        if missing_env:
            print(f"❌ Missing environment variables: {', '.join(missing_env)}")
            print("Please ensure you have a .env file with the required variables")
        else:
            print("✅ All required environment variables found")
            results["environment"] = True
    except Exception as e:
        print(f"❌ Environment check failed: {str(e)}")

    # 2. Test data loading
    print("\n2. Testing Data Loading...")
    try:
        # Load test data
        with open('data/user_profile.json', 'r') as f:
            user_profile_data = json.load(f)
            user_profile = UserProfile(**user_profile_data)
            print("✅ User profile loaded successfully")

        with open('data/job_description.json', 'r') as f:
            job_params_data = json.load(f)
            job_params = JobSearchParams(**job_params_data)
            print("✅ Job parameters loaded successfully")

        with open('data/application_question.json', 'r') as f:
            question_data = json.load(f)
            application_question = ApplicationQuestion(**question_data)
            print("✅ Application question loaded successfully")

        results["data_loading"] = True
    except Exception as e:
        print(f"❌ Data loading failed: {str(e)}")
        return results

    # 3. Test Agent Initialization
    print("\n3. Testing Agent Initialization...")
    try:
        from agents.answer_generator import ResumeAnalyzer
        analyzer = ResumeAnalyzer()
        print("✅ Resume Analyzer initialized successfully")
        results["agent_init"] = True
    except Exception as e:
        print(f"❌ Agent initialization failed: {str(e)}")
        return results

    # 4. Test Full Workflow
    if all([results["environment"], results["data_loading"], results["agent_init"]]):
        print("\n4. Testing Complete Workflow...")
        try:
            result = await analyzer.analyze_resume_and_jd(
                user_profile=user_profile,
                job_params=job_params,
                application_question=application_question.question_text
            )

            if isinstance(result, GeneratedAnswer):
                print("✅ Workflow completed successfully")
                print("\nResults Summary:")
                print(f"- Answer length: {result.word_count} words")
                print(f"- Key points addressed: {len(result.key_points_addressed)}")
                print(f"- Skills mentioned: {len(result.tailored_elements.skills_mentioned)}")
                
                # Save results
                output_path = Path('data/test_output.json')
                with open(output_path, 'w') as f:
                    json.dump(result.dict(), f, indent=2, default=str)
                print(f"\n💾 Results saved to {output_path}")
                
                results["full_workflow"] = True
            else:
                print("❌ Invalid result format")
        except Exception as e:
            print(f"❌ Workflow test failed: {str(e)}")
            import traceback
            print("\nTraceback:")
            print(traceback.format_exc())

    return results

def print_test_summary(results):
    """Print a summary of all test results"""
    print("\n📊 Test Summary")
    print("=============")
    for component, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {component.replace('_', ' ').title()}")

if __name__ == "__main__":
    results = asyncio.run(test_workflow_components())
    print_test_summary(results)

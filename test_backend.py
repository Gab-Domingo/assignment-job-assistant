"""
Backend API Testing Script
Tests all endpoints to ensure they're working correctly
"""
import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_server_running():
    """Test if server is running"""
    print("🔍 Testing server connection...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running:")
        print("   uvicorn app:app --reload")
        return False

def test_health_check():
    """Test root endpoint"""
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_list_candidates():
    """Test listing candidates (should be empty initially)"""
    print("\n🔍 Testing GET /api/candidates...")
    try:
        response = requests.get(f"{BASE_URL}/api/candidates")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ List candidates: {len(data)} candidates found")
            return True, data
        else:
            print(f"❌ Status {response.status_code}: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_upload_resume(file_path):
    """Test uploading a resume"""
    print(f"\n🔍 Testing POST /api/candidates/upload...")
    if not os.path.exists(file_path):
        print(f"⚠️  Resume file not found: {file_path}")
        print("   Skipping upload test. You can test this manually with a resume file.")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/api/candidates/upload", files=files)
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            print(f"✅ Upload successful!")
            print(f"   Candidate ID: {data.get('id')}")
            print(f"   Name: {data.get('profile_data', {}).get('personal_info', {}).get('full_name', 'N/A')}")
            return data.get('id')
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_analyze_candidate(candidate_id, job_title="Software Engineer", job_location="San Francisco, CA"):
    """Test analyzing a candidate"""
    print(f"\n🔍 Testing POST /api/candidates/{candidate_id}/analyze...")
    if not candidate_id:
        print("⚠️  No candidate ID available. Skipping analysis test.")
        return None
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/candidates/{candidate_id}/analyze",
            params={
                "job_title": job_title,
                "job_location": job_location
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis successful!")
            print(f"   Match Score: {data.get('match_score')}/100")
            print(f"   Key Matches: {len(data.get('key_matches', []))}")
            print(f"   Gaps: {len(data.get('gaps', []))}")
            return data.get('id')
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_analytics_comparison(candidate_ids):
    """Test candidate comparison"""
    print(f"\n🔍 Testing GET /api/analytics/comparison...")
    if len(candidate_ids) < 2:
        print("⚠️  Need at least 2 candidates for comparison. Skipping.")
        return False
    
    try:
        ids_str = ",".join(candidate_ids[:2])  # Compare first 2
        response = requests.get(
            f"{BASE_URL}/api/analytics/comparison",
            params={"candidate_ids": ids_str}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Comparison successful!")
            print(f"   Candidates compared: {len(data.get('candidates', []))}")
            print(f"   Skills in comparison: {len(data.get('skills_comparison', {}))}")
            return True
        else:
            print(f"❌ Comparison failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_skills_gap():
    """Test skills gap analysis"""
    print(f"\n🔍 Testing GET /api/analytics/skills-gap...")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/skills-gap")
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                print(f"⚠️  {data['message']}")
            else:
                print(f"✅ Skills gap analysis successful!")
                print(f"   Total candidates: {data.get('total_candidates', 0)}")
                print(f"   Unique skills: {data.get('unique_skills', 0)}")
            return True
        else:
            print(f"❌ Skills gap failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_statistics():
    """Test statistics endpoint"""
    print(f"\n🔍 Testing GET /api/analytics/statistics...")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/statistics")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistics retrieved!")
            print(f"   Total candidates: {data.get('total_candidates', 0)}")
            print(f"   Total analyses: {data.get('total_analyses', 0)}")
            print(f"   Avg match score: {data.get('average_match_score', 0)}")
            return True
        else:
            print(f"❌ Statistics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_market_intelligence():
    """Test market intelligence endpoints"""
    print(f"\n🔍 Testing GET /api/market-intelligence/insights...")
    try:
        response = requests.get(f"{BASE_URL}/api/market-intelligence/insights")
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                print(f"⚠️  {data['message']}")
            else:
                print(f"✅ Market insights retrieved!")
                print(f"   Total candidates: {data.get('total_candidates', 0)}")
                print(f"   Skills diversity: {data.get('skills_diversity', 0)}")
            return True
        else:
            print(f"❌ Market intelligence failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_skill_benchmarks():
    """Test skill benchmarks"""
    print(f"\n🔍 Testing GET /api/market-intelligence/skill-benchmarks...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/market-intelligence/skill-benchmarks",
            params={"job_title": "Software Engineer"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                print(f"⚠️  {data['message']}")
            else:
                print(f"✅ Benchmarks retrieved!")
                print(f"   Job title: {data.get('job_title')}")
                print(f"   Sample size: {data.get('sample_size', 0)}")
            return True
        else:
            print(f"❌ Benchmarks failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Backend API Testing")
    print("=" * 60)
    
    # Test 1: Server running
    if not test_server_running():
        return
    
    # Test 2: Health check
    test_health_check()
    
    # Test 3: List candidates (empty initially)
    success, candidates = test_list_candidates()
    candidate_ids = []
    
    # Test 4: Upload resume (if file exists)
    # Look for common resume file names
    resume_files = [
        "resume.pdf",
        "test_resume.pdf",
        "sample_resume.pdf",
        "resume.pdf",
        "../resume.pdf"
    ]
    
    resume_file = None
    for f in resume_files:
        if os.path.exists(f):
            resume_file = f
            break
    
    candidate_id = test_upload_resume(resume_file) if resume_file else None
    if candidate_id:
        candidate_ids.append(candidate_id)
    
    # Test 5: Analyze candidate
    analysis_id = test_analyze_candidate(candidate_id) if candidate_id else None
    
    # Test 6: Analytics endpoints
    test_skills_gap()
    test_statistics()
    
    # Test 7: Comparison (if we have candidates)
    if len(candidate_ids) >= 2:
        test_analytics_comparison(candidate_ids)
    
    # Test 8: Market intelligence
    test_market_intelligence()
    test_skill_benchmarks()
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("=" * 60)
    print("\n💡 Tips:")
    print("   - Use http://localhost:8000/docs for interactive API testing")
    print("   - Upload resumes via the /api/candidates/upload endpoint")
    print("   - All endpoints are working if you see ✅ above")
    print("\n")

if __name__ == "__main__":
    main()

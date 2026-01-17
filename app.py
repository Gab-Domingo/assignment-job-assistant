from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Optional
from agents.resume_extractor import ResumeExtractor
from agents.resume_agent import ResumeAnalyzer
from models.user_profile import UserProfile, JobSearchParams
from services.rag_service import RAGService
from pydantic import BaseModel
import json
import uuid
from datetime import datetime

app = FastAPI(
    title="Talent Intelligence Platform",
    description="AI-powered candidate analytics and market intelligence showcase",
    version="2.0.0"
)

# In-memory storage for showcase
candidates_store = {}
analyses_store = {}

# Mount static files
static_path = Path(__file__).parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CandidateResponse(BaseModel):
    id: str
    profile_data: dict
    resume_filename: Optional[str] = None
    ocr_confidence: Optional[float] = None
    created_at: str

class AnalysisResponse(BaseModel):
    id: str
    candidate_id: str
    match_score: int
    key_matches: List[str]
    gaps: List[str]
    suggestions: List[str]
    job_title: Optional[str] = None
    created_at: str

# Serve frontend
@app.get("/")
async def read_root():
    """Serve the main frontend interface"""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Frontend not found. API is running at /docs"}

# ===== Candidate Management =====

@app.post("/api/candidates/upload", response_model=CandidateResponse)
async def upload_candidate_resume(file: UploadFile = File(...)):
    """Upload a resume and extract profile data"""
    # Validate file type
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    file_extension = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        file_content = await file.read()
        resume_extractor = ResumeExtractor()
        profile = await resume_extractor.extract_from_bytes(
            file_bytes=file_content,
            file_type=file_extension.lstrip('.')
        )
        
        candidate_id = str(uuid.uuid4())
        candidate = CandidateResponse(
            id=candidate_id,
            profile_data=profile.model_dump(),
            resume_filename=file.filename,
            ocr_confidence=getattr(resume_extractor, 'last_confidence', None),
            created_at=datetime.now().isoformat()
        )
        
        candidates_store[candidate_id] = candidate.model_dump()
        return candidate
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")

@app.post("/api/candidates/batch-upload")
async def batch_upload_resumes(files: List[UploadFile] = File(...)):
    """Upload multiple resumes at once"""
    successful = []
    failed = 0
    
    for file in files:
        try:
            file_extension = Path(file.filename).suffix.lower() if file.filename else ''
            if f'.{file_extension}' not in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                failed += 1
                continue
            
            file_content = await file.read()
            resume_extractor = ResumeExtractor()
            profile = await resume_extractor.extract_from_bytes(
                file_bytes=file_content,
                file_type=file_extension.lstrip('.')
            )
            
            candidate_id = str(uuid.uuid4())
            candidate = CandidateResponse(
                id=candidate_id,
                profile_data=profile.model_dump(),
                resume_filename=file.filename,
                created_at=datetime.now().isoformat()
            )
            
            candidates_store[candidate_id] = candidate.model_dump()
            successful.append(candidate)
            
        except Exception:
            failed += 1
    
    return {
        "successful": len(successful),
        "failed": failed,
        "candidates": successful
    }

@app.get("/api/candidates", response_model=List[CandidateResponse])
async def list_candidates():
    """List all candidates"""
    return [CandidateResponse(**c) for c in candidates_store.values()]

@app.get("/api/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str):
    """Get a specific candidate"""
    if candidate_id not in candidates_store:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return CandidateResponse(**candidates_store[candidate_id])

@app.post("/api/candidates/{candidate_id}/analyze", response_model=AnalysisResponse)
async def analyze_candidate(
    candidate_id: str,
    job_title: str,
    job_location: Optional[str] = None,
    job_url: Optional[str] = None,
    use_rag: bool = True
):
    """Analyze a candidate against a job using RAG"""
    if candidate_id not in candidates_store:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate_data = candidates_store[candidate_id]
    profile = UserProfile(**candidate_data['profile_data'])
    
    job_params = JobSearchParams(
        job_title=job_title,
        location=job_location or "",
        url=job_url
    )
    
    try:
        resume_analyzer = ResumeAnalyzer()
        analysis_result = await resume_analyzer.analyze_resume_and_jd(
            user_profile=profile,
            job_params=job_params,
            use_rag=use_rag
        )
        
        analysis_id = str(uuid.uuid4())
        analysis = AnalysisResponse(
            id=analysis_id,
            candidate_id=candidate_id,
            match_score=analysis_result.match_score,
            key_matches=analysis_result.key_matches,
            gaps=analysis_result.gaps,
            suggestions=analysis_result.suggestions,
            job_title=analysis_result.metadata.get('job_title') if analysis_result.metadata else None,
            created_at=datetime.now().isoformat()
        )
        
        analyses_store[analysis_id] = analysis.model_dump()
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ===== Ideal Candidate Profiles (RAG) =====

@app.get("/api/ideal-profiles")
async def list_ideal_profiles():
    """List all ideal candidate profiles in ChromaDB"""
    try:
        rag_service = RAGService()
        profiles = await rag_service.get_all_profiles()
        stats = rag_service.get_collection_stats()
        return {
            "profiles": profiles,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ideal-profiles/search")
async def search_ideal_profiles(
    query: str,
    job_title: Optional[str] = None,
    n_results: int = 3
):
    """Search ideal candidate profiles using RAG"""
    try:
        rag_service = RAGService()
        results = await rag_service.search_ideal_profiles(query, job_title, n_results)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ideal-profiles/stats")
async def get_ideal_profiles_stats():
    """Get statistics about ideal candidate profiles collection"""
    try:
        rag_service = RAGService()
        stats = rag_service.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Analytics =====

@app.get("/api/analytics/comparison")
async def compare_candidates(candidate_ids: str):
    """Compare multiple candidates"""
    candidate_id_list = [id.strip() for id in candidate_ids.split(",")]
    if len(candidate_id_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 candidate IDs required")
    
    # Get candidates
    candidates = []
    for cid in candidate_id_list:
        if cid not in candidates_store:
            raise HTTPException(status_code=404, detail=f"Candidate {cid} not found")
        candidates.append(CandidateResponse(**candidates_store[cid]))
    
    # Simple comparison logic
    all_skills = set()
    candidate_profiles = []
    
    for candidate in candidates:
        profile = UserProfile(**candidate.profile_data)
        candidate_profiles.append(profile)
        if profile.skills and profile.skills.technical:
            all_skills.update(profile.skills.technical)
    
    comparison = {
        "candidates": [
            {
                "id": c.id,
                "name": UserProfile(**c.profile_data).personal_info.full_name,
                "skills_count": len(UserProfile(**c.profile_data).skills.technical) if UserProfile(**c.profile_data).skills else 0
            }
            for c in candidates
        ],
        "skills_comparison": {
            skill: {
                candidate.id: skill in (UserProfile(**candidates_store[candidate.id]).profile_data.get('skills', {}).get('technical', []))
                for candidate in candidates
            }
            for skill in all_skills
        }
    }
    
    return comparison

@app.get("/api/analytics/skills-gap")
async def get_skills_gap_analysis():
    """Analyze skills gaps across all candidates"""
    if not candidates_store:
        return {"message": "No candidates found"}
    
    all_skills = {}
    for candidate_data in candidates_store.values():
        profile = UserProfile(**candidate_data['profile_data'])
        if profile.skills and profile.skills.technical:
            for skill in profile.skills.technical:
                all_skills[skill] = all_skills.get(skill, 0) + 1
    
    total = len(candidates_store)
    skill_coverage = {
        skill: {
            "count": count,
            "percentage": (count / total) * 100
        }
        for skill, count in all_skills.items()
    }
    
    return {
        "total_candidates": total,
        "unique_skills": len(all_skills),
        "skill_coverage": skill_coverage
    }

@app.get("/api/analytics/statistics")
async def get_statistics():
    """Get overall statistics"""
    if not candidates_store:
        return {"total_candidates": 0}
    
    # Get average match score from analyses
    if analyses_store:
        avg_score = sum(a['match_score'] for a in analyses_store.values()) / len(analyses_store)
    else:
        avg_score = 0
    
    # Top skills
    all_skills = {}
    for candidate_data in candidates_store.values():
        profile = UserProfile(**candidate_data['profile_data'])
        if profile.skills and profile.skills.technical:
            for skill in profile.skills.technical:
                all_skills[skill] = all_skills.get(skill, 0) + 1
    
    top_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_candidates": len(candidates_store),
        "total_analyses": len(analyses_store),
        "average_match_score": round(avg_score, 1),
        "top_skills": [{"skill": skill, "count": count} for skill, count in top_skills]
    }

# ===== Market Intelligence =====

@app.get("/api/market-intelligence/skill-benchmarks")
async def get_skill_benchmarks(job_title: str):
    """Get skill benchmarks for a job title"""
    # Simple benchmark based on existing analyses
    relevant_analyses = [
        a for a in analyses_store.values()
        if a.get('job_title') == job_title
    ]
    
    if not relevant_analyses:
        return {
            "message": "Insufficient data for benchmarks",
            "job_title": job_title,
            "sample_size": 0
        }
    
    scores = [a['match_score'] for a in relevant_analyses]
    sorted_scores = sorted(scores)
    
    return {
        "job_title": job_title,
        "sample_size": len(relevant_analyses),
        "benchmarks": {
            "p50": sorted_scores[len(sorted_scores) // 2] if sorted_scores else 0,
            "p75": sorted_scores[int(len(sorted_scores) * 0.75)] if sorted_scores else 0,
            "p90": sorted_scores[int(len(sorted_scores) * 0.9)] if sorted_scores else 0,
            "mean": sum(scores) / len(scores) if scores else 0
        }
    }

@app.get("/api/market-intelligence/insights")
async def get_market_insights():
    """Get aggregated market insights"""
    if not candidates_store:
        return {"message": "No candidates found"}
    
    # Aggregate data
    all_skills = {}
    for candidate_data in candidates_store.values():
        profile = UserProfile(**candidate_data['profile_data'])
        if profile.skills and profile.skills.technical:
            for skill in profile.skills.technical:
                all_skills[skill] = all_skills.get(skill, 0) + 1
    
    avg_match = sum(a['match_score'] for a in analyses_store.values()) / len(analyses_store) if analyses_store else 0
    
    return {
        "total_candidates": len(candidates_store),
        "total_analyses": len(analyses_store),
        "average_match_score": round(avg_match, 1),
        "top_skills": sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10],
        "skills_diversity": len(all_skills)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

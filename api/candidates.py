"""
Candidate management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database.base import get_db
from database.models import Candidate, User, ResumeAnalysis, JobPosting
from auth.security import get_current_active_user, require_role
from auth.schemas import UserResponse
from agents.resume_extractor import ResumeExtractor
from agents.resume_agent import ResumeAnalyzer
from models.user_profile import UserProfile, JobSearchParams
from pydantic import BaseModel
from datetime import datetime
import hashlib

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


class CandidateResponse(BaseModel):
    id: str
    profile_data: dict
    resume_filename: Optional[str]
    ocr_confidence: Optional[float]
    status: str
    notes: Optional[str]
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class CandidateListResponse(BaseModel):
    candidates: List[CandidateResponse]
    total: int
    page: int
    page_size: int


class BatchUploadResponse(BaseModel):
    successful: int
    failed: int
    candidates: List[CandidateResponse]


@router.post("/upload", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def upload_candidate_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a resume and create a candidate record
    """
    # Validate file type
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if f'.{file_extension}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check for duplicates
        existing = db.query(Candidate).filter(
            Candidate.organization_id == current_user.organization_id,
            Candidate.resume_file_hash == file_hash
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="This resume has already been uploaded")
        
        # Extract profile using OCR
        resume_extractor = ResumeExtractor()
        profile = await resume_extractor.extract_from_bytes(
            file_bytes=file_content,
            file_type=file_extension
        )
        
        # Create candidate record
        candidate = Candidate(
            organization_id=current_user.organization_id,
            created_by=current_user.id,
            profile_data=profile.model_dump(),
            resume_filename=file.filename,
            resume_file_hash=file_hash,
            ocr_confidence=getattr(resume_extractor, 'last_confidence', None),
            status="new"
        )
        
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        return CandidateResponse.model_validate(candidate)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")


@router.post("/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_resumes(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_role(["admin", "recruiter"])),
    db: Session = Depends(get_db)
):
    """
    Upload multiple resumes at once (admin/recruiter only)
    """
    successful = []
    failed = 0
    
    for file in files:
        try:
            # Validate file type
            file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            if f'.{file_extension}' not in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                failed += 1
                continue
            
            file_content = await file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check for duplicates
            existing = db.query(Candidate).filter(
                Candidate.organization_id == current_user.organization_id,
                Candidate.resume_file_hash == file_hash
            ).first()
            
            if existing:
                failed += 1
                continue
            
            # Extract profile
            resume_extractor = ResumeExtractor()
            profile = await resume_extractor.extract_from_bytes(
                file_bytes=file_content,
                file_type=file_extension
            )
            
            # Create candidate
            candidate = Candidate(
                organization_id=current_user.organization_id,
                created_by=current_user.id,
                profile_data=profile.model_dump(),
                resume_filename=file.filename,
                resume_file_hash=file_hash,
                status="new"
            )
            
            db.add(candidate)
            successful.append(candidate)
            
        except Exception:
            failed += 1
    
    db.commit()
    
    # Refresh all successful candidates
    for candidate in successful:
        db.refresh(candidate)
    
    return BatchUploadResponse(
        successful=len(successful),
        failed=failed,
        candidates=[CandidateResponse.model_validate(c) for c in successful]
    )


@router.get("/", response_model=CandidateListResponse)
async def list_candidates(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all candidates in the organization
    """
    query = db.query(Candidate).filter(
        Candidate.organization_id == current_user.organization_id
    )
    
    if status_filter:
        query = query.filter(Candidate.status == status_filter)
    
    total = query.count()
    candidates = query.order_by(Candidate.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return CandidateListResponse(
        candidates=[CandidateResponse.model_validate(c) for c in candidates],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific candidate
    """
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == current_user.organization_id
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return CandidateResponse.model_validate(candidate)


@router.post("/{candidate_id}/analyze", response_model=dict)
async def analyze_candidate(
    candidate_id: str,
    job_posting_id: Optional[str] = None,
    job_title: Optional[str] = None,
    job_location: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a candidate against a job posting
    """
    # Get candidate
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == current_user.organization_id
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get job posting or create search params
    job_posting = None
    job_params = None
    
    if job_posting_id:
        job_posting = db.query(JobPosting).filter(
            JobPosting.id == job_posting_id,
            JobPosting.organization_id == current_user.organization_id
        ).first()
        
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")
        
        job_params = JobSearchParams(
            job_title=job_posting.job_title,
            location=job_posting.location or "",
            url=job_posting.url
        )
    elif job_title and job_location:
        job_params = JobSearchParams(
            job_title=job_title,
            location=job_location
        )
    else:
        raise HTTPException(status_code=400, detail="Either job_posting_id or job_title+job_location required")
    
    try:
        # Convert profile data to UserProfile
        profile = UserProfile(**candidate.profile_data)
        
        # Run analysis
        resume_analyzer = ResumeAnalyzer()
        analysis_result = await resume_analyzer.analyze_resume_and_jd(
            user_profile=profile,
            job_params=job_params
        )
        
        # Store analysis
        analysis = ResumeAnalysis(
            candidate_id=candidate.id,
            job_posting_id=job_posting.id if job_posting else None,
            match_score=analysis_result.match_score,
            key_matches=analysis_result.key_matches,
            gaps=analysis_result.gaps,
            suggestions=analysis_result.suggestions,
            section_scores={},  # Can be enhanced later
            skills_matched=[],
            skill_gaps=[],
            analysis_metadata=analysis_result.metadata
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return {
            "analysis_id": analysis.id,
            "match_score": analysis.match_score,
            "key_matches": analysis.key_matches,
            "gaps": analysis.gaps,
            "suggestions": analysis.suggestions,
            "metadata": analysis.analysis_metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

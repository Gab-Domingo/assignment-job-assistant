"""
Analytics API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.base import get_db
from database.models import User
from auth.security import get_current_active_user
from services.analytics import CandidateAnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/comparison")
async def compare_candidates(
    candidate_ids: str = Query(..., description="Comma-separated candidate IDs"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Compare multiple candidates side by side
    """
    candidate_id_list = [id.strip() for id in candidate_ids.split(",")]
    
    if len(candidate_id_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 candidate IDs required")
    
    if len(candidate_id_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 candidates can be compared at once")
    
    service = CandidateAnalyticsService(db)
    try:
        comparison = service.get_candidate_comparison(
            organization_id=current_user.organization_id,
            candidate_ids=candidate_id_list
        )
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/skills-gap")
async def get_skills_gap_analysis(
    job_title: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze skills gaps across candidates
    """
    service = CandidateAnalyticsService(db)
    analysis = service.get_skills_gap_analysis(
        organization_id=current_user.organization_id,
        job_title=job_title
    )
    return analysis


@router.get("/statistics")
async def get_candidate_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get overall candidate statistics for the organization
    """
    service = CandidateAnalyticsService(db)
    stats = service.get_candidate_statistics(
        organization_id=current_user.organization_id
    )
    return stats

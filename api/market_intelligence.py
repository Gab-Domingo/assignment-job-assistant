"""
Market Intelligence API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database.base import get_db
from database.models import User
from auth.security import get_current_active_user
from services.market_intelligence import MarketIntelligenceService

router = APIRouter(prefix="/api/market-intelligence", tags=["market-intelligence"])


@router.get("/skill-benchmarks")
async def get_skill_benchmarks(
    job_title: str = Query(..., description="Job title to benchmark"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get skill benchmarks for a specific job title
    """
    service = MarketIntelligenceService(db)
    benchmarks = service.calculate_skill_benchmarks(
        job_title=job_title,
        industry=industry
    )
    return benchmarks


@router.get("/skill-trends")
async def get_skill_trends(
    skill: str = Query(..., description="Skill to analyze"),
    days: int = Query(90, description="Number of days to look back"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze trends for a specific skill
    """
    if days > 365:
        raise HTTPException(status_code=400, detail="Maximum 365 days")
    
    service = MarketIntelligenceService(db)
    trends = service.get_skill_trends(skill=skill, days=days)
    return trends


@router.get("/insights")
async def get_market_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated market insights for the organization
    """
    service = MarketIntelligenceService(db)
    insights = service.get_market_insights(
        organization_id=current_user.organization_id
    )
    return insights

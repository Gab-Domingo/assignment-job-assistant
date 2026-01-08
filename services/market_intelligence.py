"""
Market Intelligence Service
Provides market benchmarks, trends, and aggregated insights
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from database.models import Candidate, ResumeAnalysis, MarketIntelligence
from typing import List, Dict, Optional
from models.user_profile import UserProfile
from datetime import datetime, timedelta
import json


class MarketIntelligenceService:
    """Service for market intelligence and benchmarking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_skill_benchmarks(
        self,
        job_title: str,
        industry: Optional[str] = None
    ) -> Dict:
        """
        Calculate skill benchmarks for a job title
        Returns percentiles and distributions
        """
        # Get all candidates with analyses for this job title
        analyses = self.db.query(ResumeAnalysis).join(Candidate).filter(
            ResumeAnalysis.analysis_metadata.contains({"job_title": job_title})
        ).all()
        
        if not analyses:
            return {"message": "Insufficient data for benchmarks"}
        
        # Collect skills from all candidates
        skill_scores = {}
        candidate_profiles = []
        
        for analysis in analyses:
            candidate = analysis.candidate
            profile = UserProfile(**candidate.profile_data)
            candidate_profiles.append(profile)
            
            if profile.skills and profile.skills.technical:
                for skill in profile.skills.technical:
                    if skill not in skill_scores:
                        skill_scores[skill] = []
                    # Use match score as proxy for skill relevance
                    skill_scores[skill].append(analysis.match_score)
        
        # Calculate percentiles for each skill
        benchmarks = {}
        for skill, scores in skill_scores.items():
            if len(scores) >= 3:  # Need at least 3 data points
                sorted_scores = sorted(scores)
                benchmarks[skill] = {
                    "p10": sorted_scores[int(len(sorted_scores) * 0.1)],
                    "p25": sorted_scores[int(len(sorted_scores) * 0.25)],
                    "p50": sorted_scores[int(len(sorted_scores) * 0.5)],
                    "p75": sorted_scores[int(len(sorted_scores) * 0.75)],
                    "p90": sorted_scores[int(len(sorted_scores) * 0.9)],
                    "mean": sum(scores) / len(scores),
                    "sample_size": len(scores)
                }
        
        # Store in database for future reference
        market_data = MarketIntelligence(
            data_type="skill_benchmark",
            job_title=job_title,
            industry=industry,
            metrics=benchmarks,
            sample_size=len(analyses),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        self.db.add(market_data)
        self.db.commit()
        
        return {
            "job_title": job_title,
            "industry": industry,
            "sample_size": len(analyses),
            "benchmarks": benchmarks,
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    def get_skill_trends(
        self,
        skill: str,
        days: int = 90
    ) -> Dict:
        """
        Analyze trends for a specific skill over time
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get analyses from recent period
        analyses = self.db.query(ResumeAnalysis).join(Candidate).filter(
            ResumeAnalysis.created_at >= cutoff_date
        ).all()
        
        skill_appearances = []
        for analysis in analyses:
            candidate = analysis.candidate
            profile = UserProfile(**candidate.profile_data)
            
            if profile.skills and profile.skills.technical:
                if skill in profile.skills.technical:
                    skill_appearances.append({
                        "date": analysis.created_at,
                        "match_score": analysis.match_score,
                        "job_title": analysis.analysis_metadata.get("job_title") if analysis.analysis_metadata else None
                    })
        
        if not skill_appearances:
            return {"message": "No data found for this skill"}
        
        # Calculate trend
        recent_scores = [a["match_score"] for a in skill_appearances[-30:]]  # Last 30
        older_scores = [a["match_score"] for a in skill_appearances[:-30]] if len(skill_appearances) > 30 else []
        
        trend = "stable"
        if older_scores and recent_scores:
            old_avg = sum(older_scores) / len(older_scores)
            new_avg = sum(recent_scores) / len(recent_scores)
            if new_avg > old_avg * 1.1:
                trend = "increasing"
            elif new_avg < old_avg * 0.9:
                trend = "decreasing"
        
        return {
            "skill": skill,
            "total_appearances": len(skill_appearances),
            "trend": trend,
            "average_match_score": sum(a["match_score"] for a in skill_appearances) / len(skill_appearances),
            "recent_average": sum(recent_scores) / len(recent_scores) if recent_scores else None,
            "appearances_by_job": self._count_by_job(skill_appearances)
        }
    
    def get_market_insights(
        self,
        organization_id: str
    ) -> Dict:
        """
        Get aggregated market insights for an organization's candidates
        """
        candidates = self.db.query(Candidate).filter(
            Candidate.organization_id == organization_id
        ).all()
        
        if not candidates:
            return {"message": "No candidates found"}
        
        # Aggregate data
        all_skills = {}
        all_job_titles = {}
        experience_levels = {"entry": 0, "mid": 0, "senior": 0}
        
        for candidate in candidates:
            profile = UserProfile(**candidate.profile_data)
            
            # Skills
            if profile.skills and profile.skills.technical:
                for skill in profile.skills.technical:
                    all_skills[skill] = all_skills.get(skill, 0) + 1
            
            # Experience levels
            total_years = self._calculate_total_experience(profile.work_history or [])
            if total_years < 2:
                experience_levels["entry"] += 1
            elif total_years < 5:
                experience_levels["mid"] += 1
            else:
                experience_levels["senior"] += 1
            
            # Job titles from work history
            if profile.work_history:
                for exp in profile.work_history:
                    all_job_titles[exp.title] = all_job_titles.get(exp.title, 0) + 1
        
        # Get analyses for match score insights
        analyses = self.db.query(ResumeAnalysis).join(Candidate).filter(
            Candidate.organization_id == organization_id
        ).all()
        
        avg_match_score = sum(a.match_score for a in analyses) / len(analyses) if analyses else 0
        
        return {
            "total_candidates": len(candidates),
            "total_analyses": len(analyses),
            "average_match_score": round(avg_match_score, 1),
            "top_skills": sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_job_titles": sorted(all_job_titles.items(), key=lambda x: x[1], reverse=True)[:10],
            "experience_distribution": experience_levels,
            "skills_diversity": len(all_skills),
            "insights": self._generate_insights(all_skills, experience_levels, avg_match_score)
        }
    
    def _calculate_total_experience(self, work_history: List) -> float:
        """Calculate total years of experience"""
        total = 0.0
        for exp in work_history:
            try:
                from datetime import datetime
                start = datetime.strptime(exp.start_date, "%Y-%m")
                end = datetime.strptime(exp.end_date, "%Y-%m") if exp.end_date != "Present" else datetime.now()
                total += (end - start).days / 365.25
            except:
                pass
        return round(total, 1)
    
    def _count_by_job(self, appearances: List[Dict]) -> Dict:
        """Count appearances by job title"""
        counts = {}
        for app in appearances:
            job = app.get("job_title", "Unknown")
            counts[job] = counts.get(job, 0) + 1
        return counts
    
    def _generate_insights(
        self,
        skills: Dict[str, int],
        experience_levels: Dict[str, int],
        avg_match_score: float
    ) -> List[str]:
        """Generate human-readable insights"""
        insights = []
        
        if avg_match_score > 75:
            insights.append("Your candidate pool shows strong alignment with job requirements")
        elif avg_match_score < 50:
            insights.append("Consider expanding your candidate pool or refining job requirements")
        
        if experience_levels["senior"] > experience_levels["entry"] + experience_levels["mid"]:
            insights.append("Your candidate pool is heavily weighted toward senior-level talent")
        
        if len(skills) > 50:
            insights.append("High skills diversity in your candidate pool")
        
        return insights

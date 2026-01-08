"""
Candidate Analytics Service
Provides analytics and insights for candidate data
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from database.models import Candidate, ResumeAnalysis, Organization
from typing import List, Dict, Optional
from models.user_profile import UserProfile
import pandas as pd
import json


class CandidateAnalyticsService:
    """Service for candidate analytics and insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_candidate_comparison(
        self,
        organization_id: str,
        candidate_ids: List[str]
    ) -> Dict:
        """
        Compare multiple candidates side by side
        """
        candidates = self.db.query(Candidate).filter(
            Candidate.organization_id == organization_id,
            Candidate.id.in_(candidate_ids)
        ).all()
        
        if len(candidates) != len(candidate_ids):
            raise ValueError("Some candidates not found")
        
        comparison = {
            "candidates": [],
            "skills_comparison": {},
            "experience_comparison": {},
            "education_comparison": {}
        }
        
        all_skills = set()
        all_experiences = []
        all_education = []
        
        for candidate in candidates:
            profile = UserProfile(**candidate.profile_data)
            
            # Collect skills
            if profile.skills and profile.skills.technical:
                all_skills.update(profile.skills.technical)
            
            # Collect experience
            if profile.work_history:
                all_experiences.extend([
                    {
                        "candidate_id": candidate.id,
                        "title": exp.title,
                        "company": exp.company,
                        "years": self._calculate_years(exp.start_date, exp.end_date)
                    }
                    for exp in profile.work_history
                ])
            
            # Collect education
            if profile.education:
                all_education.extend([
                    {
                        "candidate_id": candidate.id,
                        "degree": edu.degree,
                        "institution": edu.institution,
                        "field": edu.field_of_study
                    }
                    for edu in profile.education
                ])
            
            comparison["candidates"].append({
                "id": candidate.id,
                "name": profile.personal_info.full_name,
                "email": profile.personal_info.email,
                "summary": profile.personal_info.professional_summary,
                "total_experience_years": self._calculate_total_experience(profile.work_history or []),
                "skills_count": len(profile.skills.technical) if profile.skills and profile.skills.technical else 0
            })
        
        # Skills comparison matrix
        for skill in all_skills:
            comparison["skills_comparison"][skill] = {
                candidate.id: skill in (UserProfile(**c.profile_data).skills.technical or [])
                for candidate in candidates
                if UserProfile(**candidate.profile_data).skills
            }
        
        return comparison
    
    def get_skills_gap_analysis(
        self,
        organization_id: str,
        job_title: Optional[str] = None
    ) -> Dict:
        """
        Analyze skills gaps across all candidates or for a specific job
        """
        query = self.db.query(Candidate).filter(
            Candidate.organization_id == organization_id
        )
        
        candidates = query.all()
        
        if not candidates:
            return {"message": "No candidates found"}
        
        # Aggregate all skills
        all_skills = {}
        skill_frequency = {}
        
        for candidate in candidates:
            profile = UserProfile(**candidate.profile_data)
            if profile.skills and profile.skills.technical:
                for skill in profile.skills.technical:
                    skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
                    if skill not in all_skills:
                        all_skills[skill] = []
                    all_skills[skill].append(candidate.id)
        
        # Calculate coverage
        total_candidates = len(candidates)
        skill_coverage = {
            skill: {
                "count": count,
                "percentage": (count / total_candidates) * 100,
                "candidate_ids": all_skills[skill]
            }
            for skill, count in skill_frequency.items()
        }
        
        # Identify rare skills (less than 20% have it)
        rare_skills = {
            skill: data
            for skill, data in skill_coverage.items()
            if data["percentage"] < 20
        }
        
        # Identify common skills (more than 80% have it)
        common_skills = {
            skill: data
            for skill, data in skill_coverage.items()
            if data["percentage"] > 80
        }
        
        return {
            "total_candidates": total_candidates,
            "unique_skills": len(all_skills),
            "skill_coverage": skill_coverage,
            "rare_skills": rare_skills,
            "common_skills": common_skills,
            "skills_distribution": self._get_skills_distribution(skill_frequency)
        }
    
    def get_candidate_statistics(
        self,
        organization_id: str
    ) -> Dict:
        """
        Get overall statistics about candidates
        """
        candidates = self.db.query(Candidate).filter(
            Candidate.organization_id == organization_id
        ).all()
        
        if not candidates:
            return {
                "total_candidates": 0,
                "by_status": {},
                "average_match_scores": {},
                "top_skills": []
            }
        
        # Status distribution
        status_counts = {}
        for candidate in candidates:
            status_counts[candidate.status] = status_counts.get(candidate.status, 0) + 1
        
        # Average match scores by job
        analyses = self.db.query(ResumeAnalysis).join(Candidate).filter(
            Candidate.organization_id == organization_id
        ).all()
        
        scores_by_job = {}
        for analysis in analyses:
            job_title = analysis.analysis_metadata.get("job_title", "Unknown") if analysis.analysis_metadata else "Unknown"
            if job_title not in scores_by_job:
                scores_by_job[job_title] = []
            scores_by_job[job_title].append(analysis.match_score)
        
        avg_scores = {
            job: sum(scores) / len(scores)
            for job, scores in scores_by_job.items()
        }
        
        # Top skills
        all_skills = {}
        for candidate in candidates:
            profile = UserProfile(**candidate.profile_data)
            if profile.skills and profile.skills.technical:
                for skill in profile.skills.technical:
                    all_skills[skill] = all_skills.get(skill, 0) + 1
        
        top_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_candidates": len(candidates),
            "by_status": status_counts,
            "average_match_scores": avg_scores,
            "top_skills": [{"skill": skill, "count": count} for skill, count in top_skills]
        }
    
    def _calculate_years(self, start_date: str, end_date: str) -> float:
        """Calculate years of experience from date strings"""
        try:
            from datetime import datetime
            start = datetime.strptime(start_date, "%Y-%m")
            end = datetime.strptime(end_date, "%Y-%m") if end_date != "Present" else datetime.now()
            return (end - start).days / 365.25
        except:
            return 0.0
    
    def _calculate_total_experience(self, work_history: List) -> float:
        """Calculate total years of experience"""
        total = 0.0
        for exp in work_history:
            total += self._calculate_years(exp.start_date, exp.end_date)
        return round(total, 1)
    
    def _get_skills_distribution(self, skill_frequency: Dict[str, int]) -> Dict:
        """Get skills distribution statistics"""
        if not skill_frequency:
            return {}
        
        counts = list(skill_frequency.values())
        return {
            "min": min(counts),
            "max": max(counts),
            "mean": sum(counts) / len(counts),
            "median": sorted(counts)[len(counts) // 2]
        }

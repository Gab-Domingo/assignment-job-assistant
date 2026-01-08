"""
Database models for Talent Intelligence Platform
Multi-tenant architecture with organizations, users, candidates, and analyses
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base
import uuid


def generate_uuid():
    """Generate UUID for primary keys"""
    return str(uuid.uuid4())


class Organization(Base):
    """Multi-tenant organization model"""
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    candidates = relationship("Candidate", back_populates="organization", cascade="all, delete-orphan")
    job_postings = relationship("JobPosting", back_populates="organization", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_org_slug', 'slug'),
    )


class User(Base):
    """User model with role-based access"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")  # admin, recruiter, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    created_candidates = relationship("Candidate", back_populates="created_by_user", foreign_keys="Candidate.created_by")
    
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_org', 'organization_id'),
    )


class Candidate(Base):
    """Candidate/resume model"""
    __tablename__ = "candidates"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Extracted profile data (stored as JSON for flexibility)
    profile_data = Column(JSON, nullable=False)  # Full UserProfile JSON
    
    # Metadata
    resume_filename = Column(String(255))
    resume_file_hash = Column(String(64))  # For deduplication
    ocr_confidence = Column(Float)
    extraction_metadata = Column(JSON)
    
    # Status
    status = Column(String(50), default="new")  # new, reviewed, shortlisted, rejected
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="candidates")
    created_by_user = relationship("User", foreign_keys=[created_by])
    analyses = relationship("ResumeAnalysis", back_populates="candidate", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_candidate_org', 'organization_id'),
        Index('idx_candidate_status', 'status'),
        Index('idx_candidate_created', 'created_at'),
    )


class JobPosting(Base):
    """Job posting model"""
    __tablename__ = "job_postings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Job details
    job_title = Column(String(255), nullable=False)
    location = Column(String(255))
    job_description = Column(Text, nullable=False)
    url = Column(String(500))
    
    # Metadata
    posted_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="job_postings")
    analyses = relationship("ResumeAnalysis", back_populates="job_posting", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_job_org', 'organization_id'),
        Index('idx_job_title', 'job_title'),
    )


class ResumeAnalysis(Base):
    """Resume analysis results"""
    __tablename__ = "resume_analyses"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_posting_id = Column(String, ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True)
    
    # Analysis results
    match_score = Column(Integer, nullable=False)  # 0-100
    key_matches = Column(JSON)  # List of strings
    gaps = Column(JSON)  # List of strings
    suggestions = Column(JSON)  # List of strings
    
    # Detailed breakdown
    section_scores = Column(JSON)  # {experience: 85, skills: 90, education: 75, projects: 80}
    skills_matched = Column(JSON)  # List of matched skills
    skill_gaps = Column(JSON)  # List of missing skills
    
    # Metadata
    analysis_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    candidate = relationship("Candidate", back_populates="analyses")
    job_posting = relationship("JobPosting", back_populates="analyses")
    
    __table_args__ = (
        Index('idx_analysis_candidate', 'candidate_id'),
        Index('idx_analysis_job', 'job_posting_id'),
        Index('idx_analysis_score', 'match_score'),
    )


class MarketIntelligence(Base):
    """Aggregated market intelligence data"""
    __tablename__ = "market_intelligence"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Data type and scope
    data_type = Column(String(100), nullable=False)  # skill_benchmark, salary_curve, trend_analysis
    industry = Column(String(100))
    job_title = Column(String(255))
    location = Column(String(255))
    
    # Aggregated data
    metrics = Column(JSON, nullable=False)  # Flexible structure for different data types
    
    # Sample size
    sample_size = Column(Integer, default=0)
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_market_type', 'data_type'),
        Index('idx_market_industry', 'industry'),
        Index('idx_market_job_title', 'job_title'),
    )


class AnalyticsEvent(Base):
    """Analytics events for dashboard metrics"""
    __tablename__ = "analytics_events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # resume_uploaded, analysis_run, candidate_viewed
    event_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_analytics_org', 'organization_id'),
        Index('idx_analytics_type', 'event_type'),
        Index('idx_analytics_created', 'created_at'),
    )

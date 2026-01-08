"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.base import get_db
from database.models import User, Organization
from auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    require_role
)
from auth.schemas import (
    UserCreate,
    UserResponse,
    Token,
    LoginRequest,
    OrganizationCreate,
    OrganizationResponse
)
from datetime import timedelta
import re

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def validate_slug(slug: str) -> bool:
    """Validate organization slug format"""
    return bool(re.match(r'^[a-z0-9-]+$', slug)) and len(slug) >= 3


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    org_data: OrganizationCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new organization and admin user
    """
    # Validate slug
    if not validate_slug(org_data.slug):
        raise HTTPException(
            status_code=400,
            detail="Organization slug must be lowercase alphanumeric with hyphens, minimum 3 characters"
        )
    
    # Check if organization slug exists
    existing_org = db.query(Organization).filter(Organization.slug == org_data.slug).first()
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization slug already exists")
    
    # Check if user email exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create organization
    organization = Organization(
        name=org_data.name,
        slug=org_data.slug
    )
    db.add(organization)
    db.flush()  # Get organization ID
    
    # Create admin user
    user = User(
        organization_id=organization.id,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role="admin"  # First user is always admin
    )
    db.add(user)
    db.commit()
    db.refresh(organization)
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
        "organization": OrganizationResponse.model_validate(organization)
    }


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login and get access token
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Create a new user in the organization (admin only)
    """
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate role
    valid_roles = ["admin", "recruiter", "viewer"]
    if user_data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(valid_roles)}")
    
    # Create user in same organization
    user = User(
        organization_id=current_user.organization_id,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)

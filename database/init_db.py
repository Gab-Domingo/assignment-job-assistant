"""
Database initialization script
Creates tables and optionally seeds initial data
"""
from database.base import Base, engine, SessionLocal
from database.models import Organization, User
from auth.security import get_password_hash
import sys

def init_database():
    """Initialize database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def create_demo_organization():
    """Create a demo organization for testing"""
    db = SessionLocal()
    try:
        # Check if demo org exists
        demo_org = db.query(Organization).filter(Organization.slug == "demo").first()
        if demo_org:
            print("Demo organization already exists")
            return
        
        # Create demo organization
        org = Organization(
            name="Demo Organization",
            slug="demo"
        )
        db.add(org)
        db.flush()
        
        # Create demo admin user
        admin_user = User(
            organization_id=org.id,
            email="admin@demo.com",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo Admin",
            role="admin"
        )
        db.add(admin_user)
        
        # Create demo recruiter
        recruiter = User(
            organization_id=org.id,
            email="recruiter@demo.com",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo Recruiter",
            role="recruiter"
        )
        db.add(recruiter)
        
        db.commit()
        print("✓ Demo organization created:")
        print(f"  - Organization: {org.name} (slug: {org.slug})")
        print(f"  - Admin: admin@demo.com / demo123")
        print(f"  - Recruiter: recruiter@demo.com / demo123")
        
    except Exception as e:
        print(f"Error creating demo organization: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        init_database()
        create_demo_organization()
    else:
        init_database()
        print("\nTo create a demo organization, run: python -m database.init_db demo")

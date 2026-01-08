# Migration to Talent Intelligence Platform v2.0

## Overview

The application has been upgraded from a single-user job assistant to an **enterprise multi-tenant Talent Intelligence Platform** with:

1. **Multi-tenant Architecture** - Organizations, users, role-based access
2. **Candidate Analytics Dashboard** - Compare candidates, skills gap analysis, statistics
3. **Market Intelligence** - Skill benchmarks, trends, aggregated insights

## What's New

### Database Layer
- PostgreSQL/SQLite support with SQLAlchemy ORM
- Multi-tenant data isolation
- User authentication and authorization
- Candidate and analysis storage

### New API Endpoints

#### Authentication (`/api/auth`)
- `POST /api/auth/register` - Register new organization and admin
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/users` - Create new user (admin only)

#### Candidates (`/api/candidates`)
- `POST /api/candidates/upload` - Upload single resume
- `POST /api/candidates/batch-upload` - Upload multiple resumes
- `GET /api/candidates/` - List candidates (paginated)
- `GET /api/candidates/{id}` - Get candidate details
- `POST /api/candidates/{id}/analyze` - Analyze candidate against job

#### Analytics (`/api/analytics`)
- `GET /api/analytics/comparison?candidate_ids=id1,id2` - Compare candidates
- `GET /api/analytics/skills-gap` - Skills gap analysis
- `GET /api/analytics/statistics` - Organization statistics

#### Market Intelligence (`/api/market-intelligence`)
- `GET /api/market-intelligence/skill-benchmarks?job_title=X` - Get skill benchmarks
- `GET /api/market-intelligence/skill-trends?skill=X` - Analyze skill trends
- `GET /api/market-intelligence/insights` - Market insights

## Setup Instructions

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

New dependencies include:
- `sqlalchemy` - ORM
- `alembic` - Database migrations
- `psycopg2-binary` - PostgreSQL driver (optional, for production)
- `python-jose` - JWT tokens
- `passlib` - Password hashing
- `redis` - Caching (optional)
- `celery` - Background jobs (optional)
- `pandas` - Data analysis

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Database (use SQLite for development)
DATABASE_URL=sqlite:///./talent_intelligence.db

# For PostgreSQL (production):
# DATABASE_URL=postgresql://user:password@localhost/talent_intelligence

# JWT Secret Key (generate a secure random string)
SECRET_KEY=your-secret-key-change-in-production

# Existing keys
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
APIFY_TOKEN=your_apify_token
```

### 3. Initialize Database

```bash
# Create tables
python -m database.init_db

# Create demo organization (optional)
python -m database.init_db demo
```

### 4. Start the Server

```bash
uvicorn app:app --reload
```

The database tables will be created automatically on startup.

## Authentication Flow

### 1. Register Organization

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "email": "admin@company.com",
      "password": "securepassword",
      "full_name": "Admin User",
      "role": "admin"
    },
    "org_data": {
      "name": "My Company",
      "slug": "my-company"
    }
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "securepassword"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Use Token

```bash
curl -X GET "http://localhost:8000/api/candidates/" \
  -H "Authorization: Bearer eyJ..."
```

## User Roles

- **admin** - Full access, can create users, manage organization
- **recruiter** - Can upload candidates, run analyses, view all data
- **viewer** - Read-only access to candidates and analytics

## Database Schema

### Organizations
- Multi-tenant isolation
- Each organization has unique slug

### Users
- Belong to one organization
- Role-based access control
- JWT authentication

### Candidates
- Stored per organization
- Profile data as JSON
- Resume file hash for deduplication

### Resume Analyses
- Linked to candidates and job postings
- Stores match scores, gaps, suggestions
- Historical analysis tracking

### Market Intelligence
- Aggregated benchmarks
- Skill trends
- Market insights

## Backward Compatibility

The old endpoints (`/upload_resume`, `/analyze`, `/generate_answer`) are still available but **not authenticated**. For production use, migrate to the new authenticated endpoints.

## Next Steps

1. **Frontend Update** - Update frontend to use new authentication and APIs
2. **Data Migration** - If you have existing data, create migration script
3. **Production Setup** - Configure PostgreSQL, Redis, proper secrets

## Demo Credentials

If you created the demo organization:

- **Admin**: admin@demo.com / demo123
- **Recruiter**: recruiter@demo.com / demo123
- **Organization Slug**: demo

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

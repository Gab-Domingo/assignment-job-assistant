# Talent Intelligence Platform - Architecture

## System Overview

Enterprise multi-tenant SaaS platform for candidate analytics and market intelligence.

## Architecture Layers

### 1. API Layer (`api/`)
- **auth.py** - Authentication and user management
- **candidates.py** - Candidate CRUD and resume processing
- **analytics.py** - Analytics endpoints
- **market_intelligence.py** - Market intelligence endpoints

### 2. Service Layer (`services/`)
- **analytics.py** - Candidate comparison, skills analysis, statistics
- **market_intelligence.py** - Benchmarks, trends, insights

### 3. Database Layer (`database/`)
- **base.py** - Database connection and session management
- **models.py** - SQLAlchemy ORM models
- **init_db.py** - Database initialization script

### 4. Authentication (`auth/`)
- **security.py** - JWT tokens, password hashing, role checking
- **schemas.py** - Pydantic models for auth

### 5. Agents (`agents/`)
- **resume_extractor.py** - OCR and profile extraction
- **resume_agent.py** - Resume analysis

## Multi-Tenant Architecture

### Data Isolation
- Every table includes `organization_id`
- All queries filtered by organization
- Users can only access their organization's data

### Authentication Flow
1. User logs in → JWT token issued
2. Token includes user ID and organization ID
3. All requests validated via JWT
4. Database queries automatically scoped to organization

### Role-Based Access Control
- **Admin**: Full access, user management
- **Recruiter**: Upload candidates, run analyses
- **Viewer**: Read-only access

## Database Schema

```
Organizations
  ├── Users (1:N)
  ├── Candidates (1:N)
  └── Job Postings (1:N)

Candidates
  └── Resume Analyses (1:N)

Resume Analyses
  └── Job Postings (N:1)

Market Intelligence (global, aggregated)
Analytics Events (per organization)
```

## Key Features

### 1. Candidate Management
- Batch resume upload
- OCR extraction with deduplication
- Profile data stored as JSON
- Status tracking (new, reviewed, shortlisted, rejected)

### 2. Analytics
- **Comparison**: Side-by-side candidate comparison
- **Skills Gap**: Identify missing skills across pool
- **Statistics**: Aggregate metrics and distributions

### 3. Market Intelligence
- **Skill Benchmarks**: Percentile rankings by job title
- **Trends**: Skill demand over time
- **Insights**: Aggregated market data

## Security

- JWT-based authentication
- Bcrypt password hashing
- Organization-level data isolation
- Role-based access control
- SQL injection protection (SQLAlchemy ORM)

## Scalability Considerations

### Current Implementation
- SQLite for development
- PostgreSQL ready for production
- Stateless API (horizontal scaling ready)

### Future Enhancements
- Redis for caching
- Celery for background jobs
- Database connection pooling
- CDN for static assets

## API Design

### RESTful Endpoints
- `/api/auth/*` - Authentication
- `/api/candidates/*` - Candidate management
- `/api/analytics/*` - Analytics
- `/api/market-intelligence/*` - Market data

### Response Format
- Consistent JSON responses
- Pydantic models for validation
- Error handling with proper HTTP codes

## Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: SQLAlchemy ORM (SQLite/PostgreSQL)
- **Authentication**: JWT (python-jose), bcrypt
- **AI/ML**: Google Gemini, Google Cloud Vision
- **Data Analysis**: Pandas, NumPy

## Development Workflow

1. **Local Development**
   - SQLite database
   - Auto-reload server
   - Debug mode enabled

2. **Testing**
   - Unit tests for services
   - API integration tests
   - Database fixtures

3. **Production**
   - PostgreSQL database
   - Environment-based config
   - Proper secret management
   - Monitoring and logging

## Performance

### Current Optimizations
- Database indexes on foreign keys
- Pagination for list endpoints
- JSON storage for flexible schema
- Connection pooling ready

### Future Optimizations
- Redis caching layer
- Background job processing
- Database query optimization
- CDN for static files

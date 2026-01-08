# Quick Start Guide - Talent Intelligence Platform v2.0

## 5-Minute Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create or update `.env`:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
SECRET_KEY=your-secret-key-here  # Generate a random string

# Optional (defaults to SQLite)
DATABASE_URL=sqlite:///./talent_intelligence.db

# Optional
APIFY_TOKEN=your_apify_token
```

### 3. Initialize Database

```bash
python -m database.init_db
```

### 4. Start Server

```bash
uvicorn app:app --reload
```

### 5. Create Your Organization

Visit http://localhost:8000/docs and use the `/api/auth/register` endpoint:

```json
{
  "user_data": {
    "email": "your@email.com",
    "password": "yourpassword",
    "full_name": "Your Name",
    "role": "admin"
  },
  "org_data": {
    "name": "Your Company",
    "slug": "your-company"
  }
}
```

### 6. Login

Use `/api/auth/login` to get your JWT token.

### 7. Start Using

- Upload candidates: `POST /api/candidates/upload`
- View analytics: `GET /api/analytics/statistics`
- Get market insights: `GET /api/market-intelligence/insights`

## Demo Mode

For quick testing, create a demo organization:

```bash
python -m database.init_db demo
```

Then login with:
- Email: `admin@demo.com`
- Password: `demo123`

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

### Authentication
- `POST /api/auth/register` - Create organization
- `POST /api/auth/login` - Get token
- `GET /api/auth/me` - Current user

### Candidates
- `POST /api/candidates/upload` - Upload resume
- `POST /api/candidates/batch-upload` - Upload multiple
- `GET /api/candidates/` - List candidates
- `POST /api/candidates/{id}/analyze` - Analyze candidate

### Analytics
- `GET /api/analytics/comparison?candidate_ids=id1,id2`
- `GET /api/analytics/skills-gap`
- `GET /api/analytics/statistics`

### Market Intelligence
- `GET /api/market-intelligence/skill-benchmarks?job_title=Software Engineer`
- `GET /api/market-intelligence/skill-trends?skill=Python`
- `GET /api/market-intelligence/insights`

## Using the API

### Example: Upload and Analyze Candidate

```bash
# 1. Login
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"demo123"}' \
  | jq -r '.access_token')

# 2. Upload resume
curl -X POST "http://localhost:8000/api/candidates/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@resume.pdf"

# 3. Get candidate ID from response, then analyze
curl -X POST "http://localhost:8000/api/candidates/{candidate_id}/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"job_title":"Software Engineer","job_location":"San Francisco"}'
```

## Troubleshooting

### Database errors
- Make sure you ran `python -m database.init_db`
- Check DATABASE_URL in .env

### Authentication errors
- Verify SECRET_KEY is set in .env
- Check token is included in Authorization header

### Import errors
- Run `pip install -r requirements.txt`
- Check Python version (3.8+)

## Next Steps

1. Read `MIGRATION_TO_V2.md` for detailed migration guide
2. Read `ARCHITECTURE.md` for system design
3. Update frontend to use new authenticated APIs

# Simple Setup Guide

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

You only need **2 API keys**:

#### A. Google Gemini API Key (Required)
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy your API key

#### B. Google Cloud Vision API (Required for OCR)
1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable "Cloud Vision API"
4. Create a Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Give it a name (e.g., "vision-api")
   - Grant role: "Cloud Vision API User"
   - Click "Create Key" → Choose "JSON"
   - Download the JSON file

### 3. Create `.env` File

Create a `.env` file in the project root:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/downloaded-credentials.json

# Optional (for job scraping)
APIFY_TOKEN=your_apify_token_here
```

**Example:**
```bash
GEMINI_API_KEY=AIzaSyAbc123...
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourname/Downloads/project-credentials.json
```

### 4. Start the Server

```bash
uvicorn app:app --reload
```

### 5. Open in Browser

- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:8000

## That's It! 🎉

The platform uses **in-memory storage** (no database needed) and **no authentication** - perfect for showcasing capabilities!

## What You Can Do

1. **Upload Resumes** - Extract candidate profiles using OCR
2. **Analyze Candidates** - Match candidates against job descriptions
3. **Compare Candidates** - Side-by-side comparison
4. **Skills Gap Analysis** - See what skills are missing
5. **Market Intelligence** - Get skill benchmarks and insights

## API Endpoints

- `POST /api/candidates/upload` - Upload resume
- `POST /api/candidates/batch-upload` - Upload multiple resumes
- `GET /api/candidates` - List all candidates
- `POST /api/candidates/{id}/analyze` - Analyze candidate
- `GET /api/analytics/comparison?candidate_ids=id1,id2` - Compare candidates
- `GET /api/analytics/skills-gap` - Skills gap analysis
- `GET /api/analytics/statistics` - Get statistics
- `GET /api/market-intelligence/skill-benchmarks?job_title=X` - Get benchmarks
- `GET /api/market-intelligence/insights` - Market insights

## Troubleshooting

### "Could not determine credentials"
→ Make sure `GOOGLE_APPLICATION_CREDENTIALS` points to your JSON file

### "API not enabled"
→ Enable Cloud Vision API in Google Cloud Console

### "Invalid API key"
→ Check your `GEMINI_API_KEY` in `.env`

## Free Tier Limits

- **Google Gemini**: Generous free tier
- **Google Cloud Vision**: 1,000 OCR requests/month FREE
- Perfect for showcasing! 🚀

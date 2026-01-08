# Talent Intelligence Platform

AI-powered candidate analytics and market intelligence showcase. Built with FastAPI and Google Gemini AI.

## 🚀 Core Features

1. **Candidate Analytics Dashboard** - Compare candidates, skills gap analysis, statistics
2. **Market Intelligence** - Skill benchmarks, trends, aggregated insights

## 🛠 Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **AI/ML**: Google Gemini, Google Cloud Vision (OCR)
- **Storage**: In-memory (perfect for showcasing)

## 📁 Project Structure

```
job-assistant/
├── agents/                # AI agents
│   ├── resume_extractor.py
│   └── resume_agent.py
├── models/                # Data models
├── utils/                 # Utilities
└── app.py                 # Main application
```

## ⚙️ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

You need 2 API keys:

**Google Gemini API Key:**
- Go to https://makersuite.google.com/app/apikey
- Create API key

**Google Cloud Vision API:**
- Go to https://console.cloud.google.com/
- Enable Cloud Vision API
- Create Service Account and download JSON key

### 3. Create `.env` File

```bash
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### 4. Start Server

```bash
uvicorn app:app --reload
```

### 5. Open Browser

- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:8000

## 📚 Documentation

- **[Setup Guide](SETUP.md)** - Detailed setup instructions
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs

## 🎯 Key API Endpoints

### Candidates
- `POST /api/candidates/upload` - Upload resume
- `POST /api/candidates/batch-upload` - Upload multiple
- `GET /api/candidates` - List candidates
- `POST /api/candidates/{id}/analyze` - Analyze candidate

### Analytics
- `GET /api/analytics/comparison?candidate_ids=id1,id2`
- `GET /api/analytics/skills-gap`
- `GET /api/analytics/statistics`

### Market Intelligence
- `GET /api/market-intelligence/skill-benchmarks?job_title=X`
- `GET /api/market-intelligence/insights`

## 📊 Features

### Candidate Analytics
- Resume upload with OCR extraction
- Candidate comparison
- Skills gap analysis
- Aggregate statistics

### Market Intelligence
- Skill benchmarks by job title
- Market insights
- Industry analysis

## 🔒 Note

This is a **showcase version** using in-memory storage. Perfect for demonstrating capabilities without database setup complexity.

## 📝 License

MIT License

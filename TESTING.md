# Backend Testing Guide

## Quick Test Steps

### 1. Install Dependencies (if not done)

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
uvicorn app:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 3. Test via Browser (Easiest Method) ✅

**Open: http://localhost:8000/docs**

This is FastAPI's interactive API documentation (Swagger UI). You can test all endpoints here!

#### Step-by-Step Testing:

**A. Health Check**
- Find `GET /` endpoint
- Click "Try it out" → "Execute"
- ✅ Should return HTML or JSON

**B. List Candidates (Empty Initially)**
- Find `GET /api/candidates`
- Click "Try it out" → "Execute"
- ✅ Should return: `[]`

**C. Upload Resume** 📄
- Find `POST /api/candidates/upload`
- Click "Try it out"
- Click "Choose File" and select a resume PDF/image
- Click "Execute"
- ✅ Should return candidate data with:
  - `id` (save this!)
  - `profile_data` (extracted info)
  - `resume_filename`
  - `ocr_confidence`

**D. Analyze Candidate** 🔍
- First, upload a resume to get a `candidate_id`
- Find `POST /api/candidates/{candidate_id}/analyze`
- Click "Try it out"
- Enter:
  - `candidate_id`: (paste the ID from upload)
  - `job_title`: "Software Engineer"
  - `job_location`: "San Francisco, CA" (optional)
- Click "Execute"
- ✅ Should return:
  - `match_score` (0-100)
  - `key_matches` (array)
  - `gaps` (array)
  - `suggestions` (array)

**E. Analytics Endpoints** 📊
- `GET /api/analytics/skills-gap`
  - ✅ Returns skills distribution across candidates
- `GET /api/analytics/statistics`
  - ✅ Returns total candidates, analyses, avg scores
- `GET /api/analytics/comparison?candidate_ids=id1,id2`
  - ✅ Compares 2+ candidates side-by-side

**F. Market Intelligence** 📈
- `GET /api/market-intelligence/insights`
  - ✅ Returns market insights
- `GET /api/market-intelligence/skill-benchmarks?job_title=Software Engineer`
  - ✅ Returns skill benchmarks for job title

### 4. Test via Command Line (curl)

```bash
# List candidates
curl http://localhost:8000/api/candidates

# Get statistics
curl http://localhost:8000/api/analytics/statistics

# Get skills gap
curl http://localhost:8000/api/analytics/skills-gap

# Get market insights
curl http://localhost:8000/api/market-intelligence/insights
```

### 5. Run Automated Test Script

```bash
# Make sure server is running first (in one terminal)
uvicorn app:app --reload

# In another terminal, run:
python test_backend.py
```

## Expected Results

### ✅ Success Indicators

1. **Server starts** without errors
2. **All GET endpoints** return 200 status
3. **Upload endpoint** accepts files and returns candidate data
4. **Analysis endpoint** returns match scores and insights
5. **Analytics endpoints** return data (even if empty initially)

### ❌ Common Issues & Solutions

**1. "ModuleNotFoundError: No module named 'fastapi'"**
```bash
pip install -r requirements.txt
```

**2. "Could not determine credentials"**
- Check `.env` file exists
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Make sure the JSON file exists at that path

**3. "Invalid API key" or "API key not found"**
- Check `GEMINI_API_KEY` in `.env` file
- Make sure there are no extra spaces

**4. "Connection refused"**
- Make sure server is running: `uvicorn app:app --reload`
- Check if port 8000 is already in use

**5. "422 Validation Error"**
- Check request parameters match the API schema
- Use `/docs` to see required fields
- Make sure file uploads are actual files (PDF/image)

**6. "500 Internal Server Error"**
- Check server terminal for error messages
- Verify API keys are set correctly
- Make sure Google Cloud Vision API is enabled

## Testing Checklist

Test each endpoint and check off:

- [ ] Server starts successfully (`uvicorn app:app --reload`)
- [ ] Can access `/docs` (Swagger UI loads)
- [ ] `GET /api/candidates` returns `[]` (empty array)
- [ ] `POST /api/candidates/upload` accepts file and returns candidate
- [ ] `POST /api/candidates/{id}/analyze` returns analysis with match_score
- [ ] `GET /api/analytics/statistics` returns data
- [ ] `GET /api/analytics/skills-gap` returns data
- [ ] `GET /api/analytics/comparison?candidate_ids=id1,id2` works (need 2+ candidates)
- [ ] `GET /api/market-intelligence/insights` returns data
- [ ] `GET /api/market-intelligence/skill-benchmarks?job_title=X` returns data

## Quick Test Workflow

1. **Start server**: `uvicorn app:app --reload`
2. **Open browser**: http://localhost:8000/docs
3. **Upload a resume**: Use `POST /api/candidates/upload`
4. **Analyze it**: Use `POST /api/candidates/{id}/analyze`
5. **Check analytics**: Use `GET /api/analytics/statistics`
6. **View insights**: Use `GET /api/market-intelligence/insights`

## Next Steps

Once all endpoints are working:
1. ✅ Backend is ready
2. ⏭️ Update frontend to use these endpoints
3. 🎉 Showcase the platform!

## Tips

- **Use `/docs`** - It's the easiest way to test
- **Save candidate IDs** - You'll need them for analysis/comparison
- **Upload multiple resumes** - Better for testing comparison features
- **Check server logs** - They show detailed error messages

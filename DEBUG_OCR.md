# Debugging OCR Issues

## Common 500 Errors

### 1. Google Cloud Vision API Credentials

**Error**: "Failed to load Google Cloud credentials" or "credentials not found"

**Solution**:
1. Check `.env` file has `GOOGLE_APPLICATION_CREDENTIALS` set
2. Verify the path points to your JSON credentials file
3. Make sure the file exists and is readable

**Test**:
```bash
# Check if credentials file exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Or check in project root
ls -la job-assistant-ocr-f3a050b4f819.json
```

### 2. Google Cloud Vision API Not Enabled

**Error**: "API not enabled" or "permission denied"

**Solution**:
1. Go to https://console.cloud.google.com/
2. Select your project
3. Go to "APIs & Services" → "Library"
4. Search for "Cloud Vision API"
5. Click "Enable"

### 3. Gemini API Key Missing

**Error**: "API key not found" or "Invalid API key"

**Solution**:
1. Check `.env` file has `GEMINI_API_KEY` set
2. Get your key from https://makersuite.google.com/app/apikey
3. Make sure there are no extra spaces

### 4. Service Account Permissions

**Error**: "Permission denied" or "insufficient permissions"

**Solution**:
1. Make sure service account has "Cloud Vision API User" role
2. Check service account is enabled
3. Verify JSON key file is correct

## Quick Debug Steps

### Step 1: Check Environment Variables

```bash
# In your terminal (with venv activated)
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GEMINI_API_KEY:', 'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'); print('GOOGLE_APPLICATION_CREDENTIALS:', os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or 'NOT SET')"
```

### Step 2: Test OCR Processor Directly

Create a test file `test_ocr.py`:

```python
import asyncio
from utils.ocr_processor import OCRProcessor

async def test():
    try:
        processor = OCRProcessor()
        print("✅ OCR Processor initialized successfully")
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(test())
```

Run: `python test_ocr.py`

### Step 3: Check Server Logs

When you get a 500 error, check your server terminal. The improved error handling will now print:
- Full error trace
- Specific error messages
- What component failed

### Step 4: Test with a Simple File

Try uploading a simple PDF or image first to isolate the issue.

## Expected Error Messages

With improved error handling, you'll now see:

- **"Failed to initialize resume extractor"** → Credentials issue
- **"Authentication error"** → Google Cloud Vision API issue
- **"API key error"** → Gemini API key issue
- **"Failed to extract profile"** → Processing issue

## Quick Fixes

### If credentials file not found:
```bash
# Add to .env
GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/your/credentials.json
```

### If API not enabled:
- Enable Cloud Vision API in Google Cloud Console
- Wait 1-2 minutes for propagation

### If permissions issue:
- Check service account has correct role
- Regenerate JSON key if needed

## Still Having Issues?

Check the server terminal output - it will now show detailed error traces to help identify the exact problem.

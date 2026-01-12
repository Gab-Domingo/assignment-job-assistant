# Troubleshooting Guide

## 500 Internal Server Error on Upload

### Quick Diagnosis

Run the test script:
```bash
python test_ocr_setup.py
```

### Common Issues

#### 1. **Poppler Not Installed** (Most Common for PDFs)

**Error**: "pdftoppm not found" or "poppler" error

**Solution**:
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# Download from: https://github.com/oschwartz10612/poppler-windows/releases
```

**Verify**:
```bash
which pdftoppm  # Should show a path
```

#### 2. **Google Cloud Vision API Not Enabled**

**Error**: "API not enabled" or "403 Forbidden"

**Solution**:
1. Go to https://console.cloud.google.com/
2. Select your project
3. Go to "APIs & Services" → "Library"
4. Search for "Cloud Vision API"
5. Click "Enable"
6. Wait 1-2 minutes

#### 3. **Missing Credentials File**

**Error**: "credentials not found"

**Solution**:
1. Check `.env` file has:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
   ```
2. Or place `job-assistant-ocr-f3a050b4f819.json` in project root
3. Verify file exists and is readable

#### 4. **Gemini API Key Missing**

**Error**: "API key not found"

**Solution**:
1. Get API key from: https://makersuite.google.com/app/apikey
2. Add to `.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```

#### 5. **File Too Large**

**Error**: Timeout or memory error

**Solution**:
- Try a smaller file first
- Check file size (should be < 10MB for best results)

### Check Server Logs

When you get a 500 error, check your server terminal. The improved error handling will show:
- Full error trace
- Specific component that failed
- Helpful error messages

### Test Individual Components

```bash
# Test OCR setup
python test_ocr_setup.py

# Test with a simple image (not PDF)
# Upload a PNG/JPG first to isolate PDF issues
```

### Still Having Issues?

1. **Check server terminal** - it now shows detailed errors
2. **Try an image file** instead of PDF (to test if it's Poppler)
3. **Check file size** - very large files might timeout
4. **Verify all dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Error Messages Reference

- **"Failed to initialize resume extractor"** → Credentials/API setup issue
- **"Authentication error"** → Google Cloud Vision API issue
- **"API key error"** → Gemini API key issue
- **"poppler" or "pdftoppm"** → Poppler not installed
- **"Failed to extract profile"** → Processing issue (check logs)

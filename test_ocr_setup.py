"""
Test OCR and API Setup
Run this to diagnose issues with Google Cloud Vision and Gemini API
"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_setup():
    print("=" * 60)
    print("🔍 Testing OCR and API Setup")
    print("=" * 60)
    
    # Test 1: Environment Variables
    print("\n1. Checking Environment Variables...")
    gemini_key = os.getenv("GEMINI_API_KEY")
    vision_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if gemini_key:
        print(f"   ✅ GEMINI_API_KEY: Set (length: {len(gemini_key)})")
    else:
        print("   ❌ GEMINI_API_KEY: NOT SET")
        print("      → Get it from: https://makersuite.google.com/app/apikey")
    
    if vision_creds:
        if os.path.exists(vision_creds):
            print(f"   ✅ GOOGLE_APPLICATION_CREDENTIALS: {vision_creds}")
        else:
            print(f"   ❌ GOOGLE_APPLICATION_CREDENTIALS: Path doesn't exist: {vision_creds}")
    else:
        print("   ⚠️  GOOGLE_APPLICATION_CREDENTIALS: NOT SET")
        print("      → Will try to find credentials.json in project root")
    
    # Test 2: Google Cloud Vision API
    print("\n2. Testing Google Cloud Vision API...")
    try:
        from utils.ocr_processor import OCRProcessor
        processor = OCRProcessor()
        print("   ✅ OCR Processor initialized successfully")
        
        # Try a simple test (if you have a test image)
        print("   ℹ️  OCR processor ready (test with actual file upload)")
    except Exception as e:
        print(f"   ❌ OCR Processor failed: {str(e)}")
        if "credentials" in str(e).lower():
            print("      → Check your GOOGLE_APPLICATION_CREDENTIALS path")
            print("      → Make sure Cloud Vision API is enabled")
        elif "api" in str(e).lower() and "enable" in str(e).lower():
            print("      → Enable Cloud Vision API: https://console.cloud.google.com/apis/library/vision.googleapis.com")
    
    # Test 3: Gemini API
    print("\n3. Testing Google Gemini API...")
    try:
        import google.genai as genai
        client = genai.Client(api_key=gemini_key)
        print("   ✅ Gemini client initialized successfully")
        
        # Try a simple API call
        if gemini_key:
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents="Say 'Hello'"
                )
                print("   ✅ Gemini API call successful")
            except Exception as e:
                print(f"   ❌ Gemini API call failed: {str(e)}")
                if "api key" in str(e).lower() or "invalid" in str(e).lower():
                    print("      → Check your GEMINI_API_KEY is correct")
                    print("      → Get a new key: https://makersuite.google.com/app/apikey")
        else:
            print("   ⚠️  Skipping API test (no API key)")
    except Exception as e:
        print(f"   ❌ Gemini import/init failed: {str(e)}")
    
    # Test 4: Resume Extractor
    print("\n4. Testing Resume Extractor...")
    try:
        from agents.resume_extractor import ResumeExtractor
        extractor = ResumeExtractor()
        print("   ✅ Resume Extractor initialized successfully")
    except Exception as e:
        print(f"   ❌ Resume Extractor failed: {str(e)}")
        print("      → This combines OCR + Gemini, check both above")
    
    print("\n" + "=" * 60)
    print("✅ Setup check complete!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Fix any ❌ errors above")
    print("   2. Make sure Cloud Vision API is enabled")
    print("   3. Check your .env file has correct paths")
    print("   4. Try uploading a resume again")
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_setup())

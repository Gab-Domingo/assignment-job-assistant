"""
Resume Extractor Agent
Parses OCR-extracted text from resumes into structured UserProfile data using Gemini AI
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
from models.user_profile import (
    UserProfile, PersonalInfo, WorkExperience,
    Education, Skills, Project, Certification
)
from utils.ocr_processor import OCRProcessor


class ResumeExtractor:
    """Extracts structured profile data from resume OCR text using Gemini AI"""
    
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.ocr_processor = OCRProcessor()
    
    async def extract_from_file(self, file_path: str) -> UserProfile:
        """
        Extract structured profile from a resume file (PDF or image)
        
        Args:
            file_path: Path to resume file
            
        Returns:
            UserProfile: Structured user profile data
        """
        # Step 1: Extract text using OCR
        ocr_result = await self.ocr_processor.process_resume_file(file_path)
        
        # Step 2: Parse text into structured data
        profile = await self.extract_from_text(ocr_result['text'])
        
        return profile
    
    async def extract_from_bytes(
        self,
        file_bytes: bytes,
        file_type: str
    ) -> UserProfile:
        """
        Extract structured profile from resume file bytes
        
        Args:
            file_bytes: Resume file content as bytes
            file_type: File extension (e.g., 'pdf', 'png', 'jpg')
            
        Returns:
            UserProfile: Structured user profile data
        """
        # Step 1: Extract text using OCR
        ocr_result = await self.ocr_processor.process_resume_bytes(file_bytes, file_type)
        
        # Step 2: Parse text into structured data
        profile = await self.extract_from_text(ocr_result['text'])
        
        return profile
    
    async def extract_from_text(self, resume_text: str) -> UserProfile:
        """
        Parse resume text into structured UserProfile using Gemini AI
        
        Args:
            resume_text: Raw text extracted from resume
            
        Returns:
            UserProfile: Structured user profile data
        """
        try:
            # Create prompt for Gemini to parse resume
            prompt = self._create_extraction_prompt(resume_text)
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for more consistent extraction
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            profile_data = self._parse_gemini_response(response.text)
            
            # Validate and create UserProfile
            profile = UserProfile(**profile_data)
            
            return profile
            
        except Exception as e:
            raise Exception(f"Failed to extract profile from resume: {str(e)}")
    
    def _create_extraction_prompt(self, resume_text: str) -> str:
        """
        Create prompt for Gemini to extract structured data from resume text
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            str: Formatted prompt for Gemini
        """
        return f"""You are an expert resume parser. Extract structured information from the following resume text and return it as a JSON object.

Resume Text:
{resume_text}

Extract the following information and format it exactly as specified:

{{
  "personal_info": {{
    "full_name": "string (required)",
    "email": "string (required, if not found use 'email@example.com')",
    "location": "string (required, if not found use 'Location Not Specified')",
    "professional_summary": "string (required, create a brief summary if not explicitly stated)"
  }},
  "work_history": [
    {{
      "company": "string",
      "title": "string",
      "start_date": "string (format: YYYY-MM or YYYY)",
      "end_date": "string (format: YYYY-MM or YYYY, or 'Present')",
      "description": "string (brief job description)",
      "achievements": ["string array of key achievements or responsibilities"]
    }}
  ],
  "education": [
    {{
      "institution": "string",
      "degree": "string",
      "field_of_study": "string",
      "graduation_date": "string (format: YYYY-MM or YYYY)",
      "gpa": number or null,
      "relevant_coursework": ["string array"] or null
    }}
  ],
  "skills": {{
    "technical": ["array of technical skills"],
    "soft": ["array of soft skills"],
    "certifications": [
      {{
        "name": "string",
        "issuer": "string",
        "date": "string (format: YYYY-MM or YYYY)",
        "expires": "string (format: YYYY-MM or YYYY)" or null
      }}
    ]
  }},
  "projects": [
    {{
      "name": "string",
      "description": "string",
      "technologies": ["array of technologies used"],
      "url": "string or null"
    }}
  ]
}}

Important instructions:
1. Extract dates in YYYY-MM format when possible, or YYYY if only year is available
2. For current positions, use "Present" as end_date
3. If sections are missing (like projects), return empty arrays []
4. If personal info is incomplete, use reasonable defaults but keep full_name accurate
5. Ensure all required fields have values
6. Parse achievements and responsibilities clearly
7. Identify technical vs soft skills appropriately
8. Return ONLY the JSON object, no additional text or explanations

Return the extracted data as a valid JSON object:"""
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate Gemini's JSON response
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Dict: Parsed profile data
        """
        try:
            # Find JSON boundaries
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ValueError("No valid JSON found in Gemini response")
            
            json_content = response_text[json_start:json_end]
            profile_data = json.loads(json_content)
            
            # Validate required fields
            self._validate_profile_data(profile_data)
            
            return profile_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to process Gemini response: {str(e)}")
    
    def _validate_profile_data(self, profile_data: Dict[str, Any]) -> None:
        """
        Validate that profile data has required structure
        
        Args:
            profile_data: Parsed profile data
            
        Raises:
            ValueError: If required fields are missing
        """
        required_sections = ['personal_info', 'education', 'skills']
        
        for section in required_sections:
            if section not in profile_data:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate personal_info required fields
        personal_info = profile_data['personal_info']
        required_personal_fields = ['full_name', 'email', 'location', 'professional_summary']
        
        for field in required_personal_fields:
            if field not in personal_info or not personal_info[field]:
                raise ValueError(f"Missing required personal_info field: {field}")
        
        # Ensure lists exist (can be empty)
        if 'work_history' not in profile_data:
            profile_data['work_history'] = []
        if 'projects' not in profile_data:
            profile_data['projects'] = []
        
        # Validate skills structure
        if 'technical' not in profile_data['skills']:
            profile_data['skills']['technical'] = []
        if 'soft' not in profile_data['skills']:
            profile_data['skills']['soft'] = []
        if 'certifications' not in profile_data['skills']:
            profile_data['skills']['certifications'] = []
    
    async def extract_and_validate(self, file_path: str) -> Dict[str, Any]:
        """
        Extract profile and return with validation metadata
        
        Args:
            file_path: Path to resume file
            
        Returns:
            Dict containing:
                - profile: Extracted UserProfile
                - ocr_confidence: OCR confidence score
                - extraction_metadata: Additional metadata
        """
        try:
            # Extract text using OCR
            ocr_result = await self.ocr_processor.process_resume_file(file_path)
            
            # Parse into structured data
            profile = await self.extract_from_text(ocr_result['text'])
            
            return {
                'profile': profile,
                'ocr_confidence': ocr_result['confidence'],
                'extraction_metadata': {
                    'pages_processed': ocr_result['pages'],
                    'raw_text_length': len(ocr_result['text']),
                    'ocr_metadata': ocr_result.get('metadata', {})
                }
            }
            
        except Exception as e:
            raise Exception(f"Failed to extract and validate resume: {str(e)}")


"""
OCR Processor using Google Cloud Vision API
Extracts text from resume images and PDFs
"""
import os
import io
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
import pdf2image

class OCRProcessor:
    """Processes resumes using Google Cloud Vision API OCR"""
    
    def __init__(self):
        load_dotenv()
        # Get credentials path from environment or .env file
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # If not set, try to find credentials file in project root
        if not creds_path or not os.path.exists(creds_path):
            project_root = Path(__file__).parent.parent
            # Look for common credential file names
            possible_paths = [
                project_root / "job-assistant-ocr-f3a050b4f819.json",
                project_root / "google-cloud-credentials.json",
                project_root / "credentials.json"
            ]
            for path in possible_paths:
                if path.exists():
                    creds_path = str(path)
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                    break
        
        # Initialize client with explicit credentials if available
        if creds_path and os.path.exists(creds_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(creds_path)
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
            except Exception as e:
                raise Exception(f"Failed to load Google Cloud credentials from {creds_path}: {str(e)}")
        else:
            # Fall back to default credentials (ADC)
            # This will raise an error if credentials are not found
            try:
                self.client = vision.ImageAnnotatorClient()
            except Exception as e:
                raise Exception(
                    f"Google Cloud Vision credentials not found. Please set GOOGLE_APPLICATION_CREDENTIALS "
                    f"in your .env file or place credentials.json in the project root. Error: {str(e)}"
                )
    
    async def process_resume_file(self, file_path: str) -> Dict[str, any]:
        """
        Process a resume file (PDF or image) and extract text using OCR
        
        Args:
            file_path: Path to the resume file (PDF, PNG, JPG, etc.)
            
        Returns:
            Dict containing:
                - text: Extracted text from the resume
                - confidence: Average confidence score
                - pages: Number of pages processed
                - metadata: Additional OCR metadata
        """
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return await self._process_pdf(file_path)
        elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return await self._process_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    async def process_resume_bytes(
        self,
        file_bytes: bytes,
        file_type: str
    ) -> Dict[str, any]:
        """
        Process resume from bytes (useful for API uploads)
        
        Args:
            file_bytes: File content as bytes
            file_type: File extension (e.g., 'pdf', 'png', 'jpg')
            
        Returns:
            Dict with extracted text and metadata
        """
        if file_type.lower() == 'pdf':
            return await self._process_pdf_bytes(file_bytes)
        elif file_type.lower() in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
            return await self._process_image_bytes(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {file_type}")
    
    async def _process_image(self, image_path: str) -> Dict[str, any]:
        """Process a single image file"""
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        return await self._ocr_image_content(content)
    
    async def _process_image_bytes(self, image_bytes: bytes) -> Dict[str, any]:
        """Process image from bytes"""
        return await self._ocr_image_content(image_bytes)
    
    async def _process_pdf(self, pdf_path: str) -> Dict[str, any]:
        """Process a PDF file by converting to images and OCR'ing each page"""
        # Convert PDF to images
        images = pdf2image.convert_from_path(pdf_path)
        
        all_text = []
        all_confidences = []
        
        for i, image in enumerate(images):
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Process the image
            result = await self._ocr_image_content(img_byte_arr)
            all_text.append(result['text'])
            all_confidences.append(result['confidence'])
        
        # Combine results
        combined_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        return {
            'text': combined_text,
            'confidence': avg_confidence,
            'pages': len(images),
            'metadata': {
                'page_count': len(images),
                'per_page_confidence': all_confidences
            }
        }
    
    async def _process_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, any]:
        """Process PDF from bytes"""
        # Convert PDF bytes to images
        images = pdf2image.convert_from_bytes(pdf_bytes)
        
        all_text = []
        all_confidences = []
        
        for i, image in enumerate(images):
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Process the image
            result = await self._ocr_image_content(img_byte_arr)
            all_text.append(result['text'])
            all_confidences.append(result['confidence'])
        
        # Combine results
        combined_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        return {
            'text': combined_text,
            'confidence': avg_confidence,
            'pages': len(images),
            'metadata': {
                'page_count': len(images),
                'per_page_confidence': all_confidences
            }
        }
    
    async def _ocr_image_content(self, image_content: bytes) -> Dict[str, any]:
        """
        Perform OCR on image content using Google Cloud Vision API
        
        Args:
            image_content: Image bytes
            
        Returns:
            Dict with extracted text and confidence
        """
        # Create vision API image object
        image = vision.Image(content=image_content)
        
        # Perform text detection
        response = self.client.document_text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
        
        # Extract text and confidence
        full_text = response.full_text_annotation.text if response.full_text_annotation else ""
        
        # Calculate average confidence from all detected text
        confidences = []
        if response.full_text_annotation and response.full_text_annotation.pages:
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    confidences.append(block.confidence)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': full_text,
            'confidence': avg_confidence,
            'pages': 1,
            'metadata': {
                'detected_languages': self._extract_languages(response),
                'page_count': 1
            }
        }
    
    def _extract_languages(self, response) -> List[str]:
        """Extract detected languages from Vision API response"""
        languages = set()
        if response.full_text_annotation and response.full_text_annotation.pages:
            for page in response.full_text_annotation.pages:
                if page.property and page.property.detected_languages:
                    for lang in page.property.detected_languages:
                        languages.add(lang.language_code)
        return list(languages)
    
    def validate_image_quality(self, image_path: str) -> Dict[str, any]:
        """
        Validate if an image is suitable for OCR
        Checks resolution, size, and format
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict with validation results
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format = img.format
                
                # Minimum recommended resolution for OCR
                min_width = 800
                min_height = 600
                
                issues = []
                if width < min_width or height < min_height:
                    issues.append(f"Low resolution: {width}x{height}. Recommended: {min_width}x{min_height} minimum")
                
                if format not in ['PNG', 'JPEG', 'TIFF']:
                    issues.append(f"Suboptimal format: {format}. Recommended: PNG, JPEG, or TIFF")
                
                return {
                    'is_valid': len(issues) == 0,
                    'issues': issues,
                    'width': width,
                    'height': height,
                    'format': format
                }
        except Exception as e:
            return {
                'is_valid': False,
                'issues': [f"Failed to validate image: {str(e)}"],
                'width': 0,
                'height': 0,
                'format': None
            }


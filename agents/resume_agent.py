from typing import Dict
from datetime import datetime
from models.user_profile import (
    UserProfile, ScrapedJobData, JobSearchParams, ResumeAnalysisResult
)
from utils.prompt_templates import get_resume_analysis_prompt
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json
from scraper import scrape_indeed_jobs


class ResumeAnalyzer:
    def __init__(self):
        load_dotenv()
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_KEY"),
            api_version="2024-05-01-preview",
            azure_endpoint=os.getenv("AZURE_ENDPOINT")
        )
        
    async def analyze_resume_and_jd(
        self,
        user_profile: UserProfile,
        job_params: JobSearchParams,
    ) -> ResumeAnalysisResult:
        """
        Main function to analyze resume against job description and generate tailored response
        
        Args:
            user_profile: Structured user profile data
            job_params: Either URL or job title + location
            application_question: Optional question to answer
        
        Returns:
            ResumeAnalysisResult
        """
        try:
            # 1. Scrape job description
            job_data = await scrape_indeed_jobs(search_params=job_params)
        
            
            # Handle scraping result
            if isinstance(job_data, object) and "error" in job_data:
                print(f"Scraping returned error: {job_data['error']}")
                # If scraping failed, use the search parameters to create a minimal job data
                if job_params.job_title and job_params.location:
                    job_scraped_data = ScrapedJobData(
                        job_title=job_params.job_title,
                        job_description=f"Position for {job_params.job_title} in {job_params.location}. Full job details could not be retrieved."
                    )
                else:
                    # If we don't have job params either, use default values
                    job_scraped_data = ScrapedJobData(
                        job_title="Software Engineer",  # Default title
                        job_description="Generic software engineering position. Full job details could not be retrieved."
                    )
            elif isinstance(job_data, dict):
                # If we got a dict with actual job data
                job_scraped_data = ScrapedJobData(
                    job_title=job_data.get("title") or job_params.job_title or "Software Engineer",
                    job_description=job_data.get("description") or f"Position for {job_params.job_title} in {job_params.location}"
                )
            else:
                # If we got a ScrapedJobData directly
                job_scraped_data = job_data


            # 2. Format data for prompt
            prompt = get_resume_analysis_prompt(
                profile=user_profile,
                job_data=job_scraped_data
            )

            # 3. Call LLM for analysis
            response = self.client.chat.completions.create(
                model=os.getenv("model_name"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a resume analysis expert. You MUST respond with ONLY a valid JSON object, with no additional text, explanations, or XML tags."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # 4. Parse and validate response
            llm_response = response.choices[0].message.content
            #print("Raw LLM Response:", llm_response)
            
            # 5. Parse response
            parsed_response = self._parse_llm_response(llm_response)

            # 6. Create result object
            result = ResumeAnalysisResult(
                match_score=parsed_response['match_score'],
                suggestions=parsed_response['suggestions'],
                key_matches=parsed_response['key_matches'],
                gaps=parsed_response['gaps'],
                metadata={
                    'job_title': job_scraped_data.job_title,
                    'job_description': job_scraped_data.job_description,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            )

            return result

        except Exception as e:
            print(f"Error in analyze_resume_and_jd: {str(e)}")
            raise Exception(f"Resume analysis failed: {str(e)}") from e

    def _parse_llm_response(self, llm_response: str) -> Dict:
        """Parse and validate LLM response"""
        try:
            if not llm_response:
                raise ValueError("Empty response from LLM")
            
            # Find and extract JSON content
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1  # Add 1 to include the closing brace
            
            if json_start != -1 and json_end > json_start:
                json_content = llm_response[json_start:json_end]
                # Try to parse the JSON
                parsed = json.loads(json_content)
            else:
                print(f"Raw response: {llm_response}")  # For debugging
                raise ValueError("No valid JSON object found in response")

            # Validate required fields
            required_fields = ['match_score', 'suggestions', 'key_matches', 'gaps']
            missing_fields = [field for field in required_fields if field not in parsed]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Validate types
            if not isinstance(parsed['match_score'], (int, float)):
                raise ValueError("match_score must be a number")
            if not isinstance(parsed['suggestions'], list):
                raise ValueError("suggestions must be a list")
            if not isinstance(parsed['key_matches'], list):
                raise ValueError("key_matches must be a list")
            if not isinstance(parsed['gaps'], list):
                raise ValueError("gaps must be a list")

            # Validate score range
            if not (0 <= parsed['match_score'] <= 100):
                raise ValueError("match_score must be between 0 and 100")

            return parsed

        except json.JSONDecodeError as e:
            print(f"JSON Decode Error. Response was: {llm_response}")  # Debug print
            raise ValueError(f"Invalid JSON response: {str(e)}") from e
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}") from e



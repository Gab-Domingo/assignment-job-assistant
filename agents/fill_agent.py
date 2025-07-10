import json
from typing import Any, Dict
from pydantic import ValidationError
from models.user_profile import (
    UserProfile, PersonalInfo, WorkExperience,
    Education, Skills, Project
)
from utils.prompt_templates import get_profile_validation_prompt
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

class UserProfileManager:
    def __init__(self):
        load_dotenv()
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_KEY"),
            api_version="2024-05-01-preview",
            azure_endpoint=os.getenv("AZURE_ENDPOINT")
        )
        
    async def create_profile(self, profile_data: Dict[str, Any]) -> UserProfile:
        """
        Create a new user profile with validation
        """
        try:
            # First validate the data structure
            profile = UserProfile(**profile_data)
            
            # Use LLM to validate content quality
            validation_results = await self._validate_profile_content(profile)
            if not validation_results["is_valid"]:
                raise ValueError(f"Profile content validation failed: {validation_results['issues']}")
                
            return profile
            
        except ValidationError as e:
            raise ValueError(f"Invalid profile structure: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to create profile: {str(e)}")

    async def update_profile_section(
        self,
        profile: UserProfile,
        section: str,
        data: Dict[str, Any]
    ) -> UserProfile:
        """
        Update a specific section of the user profile
        """
        try:
            profile_dict = profile.dict()
            
            if section not in profile_dict:
                raise ValueError(f"Invalid section: {section}")
                
            # Update the specific section
            if section == "personal_info":
                profile_dict[section] = PersonalInfo(**data).dict()
            elif section == "work_history":
                profile_dict[section] = [WorkExperience(**exp).dict() for exp in data]
            elif section == "education":
                profile_dict[section] = [Education(**edu).dict() for edu in data]
            elif section == "skills":
                profile_dict[section] = Skills(**data).dict()
            elif section == "projects":
                profile_dict[section] = [Project(**proj).dict() for proj in data]
                
            # Validate the entire profile again
            updated_profile = UserProfile(**profile_dict)
            validation_results = await self._validate_profile_content(updated_profile)
            
            if not validation_results["is_valid"]:
                raise ValueError(f"Profile update validation failed: {validation_results['issues']}")
                
            return updated_profile
            
        except ValidationError as e:
            raise ValueError(f"Invalid data structure: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to update profile: {str(e)}")

    async def _validate_profile_content(self, profile: UserProfile) -> Dict[str, Any]:
        """
        Use LLM to validate profile content quality
        """
        try:
            prompt = get_profile_validation_prompt(profile)
            response = await self.client.chat.completions.create(
                model=os.getenv("model_name"),
                messages=[
                    {"role": "system", "content": "You are an expert resume reviewer and profile validator."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            validation_result = json.loads(response.choices[0].message.content)
            return validation_result
            
        except Exception as e:
            raise Exception(f"Profile validation failed: {str(e)}")

    def export_profile(self, profile: UserProfile, format: str = "json") -> str:
        """
        Export profile in specified format
        """
        if format == "json":
            return profile.json(indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

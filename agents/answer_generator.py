import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, Dict, Tuple, Any
from models.user_profile import (
    UserProfile, JobSearchParams, ApplicationQuestion,
    GeneratedAnswer, TailoredElements, AnswerMetadata,
     ResumeAnalysisResult
)
from utils.prompt_templates import get_answer_generation_prompt, get_answer_validation_prompt
from agents.resume_agent import ResumeAnalyzer
import json

class AnswerGenerator:
    def __init__(self):
        load_dotenv()
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_KEY"),
            api_version="2024-05-01-preview",
            azure_endpoint=os.getenv("AZURE_ENDPOINT")
        )

    async def generate_answer(
        self,
        profile: UserProfile,
        job_params: JobSearchParams,
        question: ApplicationQuestion,
        user_answer: Optional[GeneratedAnswer] = None,
        job_data: Optional[ResumeAnalysisResult] = None
    ) -> Tuple[GeneratedAnswer, ResumeAnalysisResult]:
        """
        Generate personalized answer to application question
        Args:
            profile: Structured user profile data
            job_params: Job search parameters
            question: Application question to answer
            user_answer: Optional user's answer in GeneratedAnswer format
            job_data: Optional pre-analyzed resume data
        Returns:
            Tuple containing:
            - GeneratedAnswer: Structured answer with metadata
            - ResumeAnalysisResult: Analysis of resume against job requirements
        """
        try:
            # Get resume analysis
            resume_agent = ResumeAnalyzer()
            if job_data is None:
                resume_analysis_result = await resume_agent.analyze_resume_and_jd(profile, job_params)
            else:
                resume_analysis_result = job_data
            
            # Generate initial answer
            initial_answer_dict = await self._generate_initial_answer(
                profile=profile,
                question=question,
                resume_analysis_result=resume_analysis_result,
                user_answer=user_answer
            )
            
            # Convert initial answer to GeneratedAnswer format
            initial_answer = GeneratedAnswer(
                text=initial_answer_dict["answer"],
                word_count=len(initial_answer_dict["answer"].split()),
                key_points_addressed=initial_answer_dict["key_points"],
                tailored_elements=TailoredElements(
                    skills_mentioned=initial_answer_dict["profile_elements_used"],
                    experience_highlighted=[],  # Will be filled by validation
                    achievements_referenced=[]   # Will be filled by validation
                ),
                metadata=AnswerMetadata(
                    generation_timestamp=datetime.now(),
                    question_id=question.question_id,
                    job_id=None
                )
            )
            
            # Validate and improve answer
            improved_answer = await self._validate_and_improve_answer(
                answer=initial_answer,
                profile=profile,
                resume_analysis_result=resume_analysis_result,
                question=question
            )
            
            # Create final structured response
            final_answer = GeneratedAnswer(
                text=improved_answer["final_answer"],
                word_count=len(improved_answer["final_answer"].split()),
                key_points_addressed=improved_answer["key_points"],
                tailored_elements=TailoredElements(
                    skills_mentioned=improved_answer["skills_referenced"],
                    experience_highlighted=improved_answer["experience_referenced"],
                    achievements_referenced=improved_answer["achievements_referenced"]
                ),
                metadata=AnswerMetadata(
                    generation_timestamp=datetime.now(),
                    question_id=question.question_id,
                    job_id=None
                )
            )
            
            return resume_analysis_result, final_answer
            
        except Exception as e:
            raise Exception(f"Answer generation failed: {str(e)}")

    async def _generate_initial_answer(
        self,
        profile: UserProfile,
        resume_analysis_result: Optional[ResumeAnalysisResult],
        question: ApplicationQuestion,
        user_answer: Optional[GeneratedAnswer] = None
    ) -> Dict[str, Any]:
        """
        Generate initial answer using LLM
        Args:
            profile: User profile data
            question: Application question
            resume_analysis_result: Resume analysis results
            user_answer: Optional user's answer in GeneratedAnswer format
        Returns:
            Dict containing the generated answer and metadata
        """
        try:
            prompt = get_answer_generation_prompt(
                profile=profile,
                question=question,
                resume_analysis_result=resume_analysis_result,
                user_answer=user_answer
            )
            
            response = self.client.chat.completions.create(
                model=os.getenv("model_name"),
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at crafting compelling job application answers. You MUST respond with ONLY a valid JSON object, with no additional text, explanations, or XML tags."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            try:
                content = response.choices[0].message.content
                # Find JSON content boundaries
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    return json.loads(json_content)
                else:
                    print(f"Raw API response: {content}")
                    raise Exception("No valid JSON object found in response")
            except json.JSONDecodeError as json_err:
                print(f"Raw API response: {content}")
                raise Exception(f"Failed to parse API response as JSON: {str(json_err)}")
            
        except Exception as e:
            raise Exception(f"Initial answer generation failed: {str(e)}")

    async def _validate_and_improve_answer(
        self,
        answer: GeneratedAnswer,
        profile: UserProfile,
        resume_analysis_result: ResumeAnalysisResult,
        question: ApplicationQuestion
    ) -> Dict[str, Any]:
        """
        Validate and improve the generated answer
        Args:
            answer: Initial answer in GeneratedAnswer format
            profile: User profile data
            resume_analysis_result: Resume analysis results
            question: Application question
        Returns:
            Dict containing the improved answer and metadata
        """
        try:
            prompt = get_answer_validation_prompt(
                profile=profile,
                resume_analysis_result=resume_analysis_result,
                answer=answer,
                question=question
            )
            
            response = self.client.chat.completions.create(
                model=os.getenv("model_name"),
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at reviewing and improving job application answers. You MUST respond with ONLY a valid JSON object, with no additional text, explanations, or XML tags."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            # Find JSON content boundaries
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            else:
                print(f"Raw API response: {content}")
                raise Exception("No valid JSON object found in response")
            
        except Exception as e:
            raise Exception(f"Answer validation failed: {str(e)}")

    def validate_answer_requirements(
        self,
        answer: str,
        question: ApplicationQuestion
    ) -> bool:
        """
        Validate answer meets question requirements
        Args:
            answer: Answer text to validate
            question: Application question with requirements
        Returns:
            bool: Whether the answer meets the requirements
        """
        if question.max_length and len(answer.split()) > question.max_length:
            return False
            
        # Add more validation as needed
        return True

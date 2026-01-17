"""
RAG Service using ChromaDB for Ideal Candidate Profiles
Stores and retrieves ideal candidate profiles for matching
"""
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
from pathlib import Path
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime

class RAGService:
    """Service for managing ideal candidate profiles in ChromaDB"""
    
    def __init__(self, collection_name: str = "ideal_candidate_profiles"):
        """
        Initialize ChromaDB client and collection
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        load_dotenv()
        
        # Get or create persistent client
        persist_directory = os.getenv(
            "CHROMA_DB_PATH", 
            str(Path(__file__).parent.parent / "chroma_db")
        )
        Path(persist_directory).mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Ideal candidate profiles for job matching"}
        )
    
    def _create_document_text(self, ideal_profile: Dict[str, Any]) -> str:
        """
        Convert ideal candidate profile to searchable text document
        
        Args:
            ideal_profile: Dictionary containing ideal candidate profile data
            
        Returns:
            Formatted text document for embedding
        """
        parts = []
        
        # Job Title & Requirements
        if ideal_profile.get('job_title'):
            parts.append(f"Job Title: {ideal_profile['job_title']}")
        
        if ideal_profile.get('job_description'):
            parts.append(f"Job Description: {ideal_profile['job_description']}")
        
        # Must-have Skills
        if ideal_profile.get('must_have_skills'):
            skills = ', '.join(ideal_profile['must_have_skills'])
            parts.append(f"Must-Have Skills: {skills}")
        
        # Preferred Skills
        if ideal_profile.get('preferred_skills'):
            skills = ', '.join(ideal_profile['preferred_skills'])
            parts.append(f"Preferred Skills: {skills}")
        
        # Experience Requirements
        if ideal_profile.get('years_experience'):
            parts.append(f"Years of Experience Required: {ideal_profile['years_experience']}")
        
        # Education Requirements
        if ideal_profile.get('education_requirements'):
            edu = ideal_profile['education_requirements']
            if isinstance(edu, list):
                parts.append(f"Education Requirements: {', '.join(edu)}")
            else:
                parts.append(f"Education Requirements: {edu}")
        
        # Certifications
        if ideal_profile.get('certifications'):
            certs = ', '.join(ideal_profile['certifications'])
            parts.append(f"Certifications: {certs}")
        
        # Key Responsibilities
        if ideal_profile.get('key_responsibilities'):
            resp = ', '.join(ideal_profile['key_responsibilities'])
            parts.append(f"Key Responsibilities: {resp}")
        
        # Additional Criteria
        if ideal_profile.get('additional_criteria'):
            parts.append(f"Additional Criteria: {ideal_profile['additional_criteria']}")
        
        return "\n".join(parts)
    
    async def add_ideal_profile(self, ideal_profile: Dict[str, Any]) -> str:
        """
        Add an ideal candidate profile to ChromaDB
        
        Args:
            ideal_profile: Dictionary containing ideal candidate profile
            
        Returns:
            Profile ID
        """
        profile_id = str(uuid.uuid4())
        
        # Create document text for embedding
        document_text = self._create_document_text(ideal_profile)
        
        # Prepare metadata
        metadata = {}
        for key, value in ideal_profile.items():
            if isinstance(value, list):
                metadata[key] = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                metadata[key] = str(value) if not isinstance(value, bool) else value
            else:
                metadata[key] = str(value)
        
        metadata["created_at"] = datetime.now().isoformat()
        
        # Add to collection
        self.collection.add(
            documents=[document_text],
            metadatas=[metadata],
            ids=[profile_id]
        )
        
        return profile_id
    
    async def search_ideal_profiles(
        self, 
        query: str, 
        job_title: Optional[str] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for ideal candidate profiles using RAG
        
        Args:
            query: Search query (e.g., job title or description)
            job_title: Optional job title filter
            n_results: Number of results to return
            
        Returns:
            List of matching ideal profiles with similarity scores
        """
        # Build query with filters
        where_filter = None
        if job_title:
            where_filter = {"job_title": {"$eq": job_title}}
        
        # Search collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        # Format results
        profiles = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                profile_id = results['ids'][0][i]
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if results.get('distances') and results['distances'][0] else None
                
                # Parse JSON fields from metadata
                parsed_metadata = {}
                for key, value in metadata.items():
                    if key in ['must_have_skills', 'preferred_skills', 'education_requirements',
                              'certifications', 'key_responsibilities']:
                        try:
                            parsed_metadata[key] = json.loads(value) if isinstance(value, str) else value
                        except:
                            parsed_metadata[key] = value
                    elif key == 'years_experience':
                        try:
                            parsed_metadata[key] = int(value)
                        except:
                            parsed_metadata[key] = value
                    else:
                        parsed_metadata[key] = value
                
                profiles.append({
                    "id": profile_id,
                    "similarity_score": 1 - distance if distance is not None else 1.0,
                    "profile": parsed_metadata,
                    "document": results['documents'][0][i] if results.get('documents') else None
                })
        
        return profiles
    
    async def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Get all ideal candidate profiles"""
        results = self.collection.get()
        
        profiles = []
        if results.get('ids'):
            for i, profile_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if results.get('metadatas') else {}
                
                # Parse JSON fields
                parsed_metadata = {}
                for key, value in metadata.items():
                    if key in ['must_have_skills', 'preferred_skills', 'education_requirements',
                              'certifications', 'key_responsibilities']:
                        try:
                            parsed_metadata[key] = json.loads(value) if isinstance(value, str) else value
                        except:
                            parsed_metadata[key] = value
                    elif key == 'years_experience':
                        try:
                            parsed_metadata[key] = int(value)
                        except:
                            parsed_metadata[key] = value
                    else:
                        parsed_metadata[key] = value
                
                profiles.append({
                    "id": profile_id,
                    "profile": parsed_metadata,
                    "document": results['documents'][i] if results.get('documents') else None
                })
        
        return profiles
    
    async def delete_profile(self, profile_id: str) -> bool:
        """Delete an ideal candidate profile"""
        try:
            self.collection.delete(ids=[profile_id])
            return True
        except Exception:
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            "collection_name": self.collection.name,
            "profile_count": count
        }

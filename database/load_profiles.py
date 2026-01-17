"""
Load ideal candidate profiles into ChromaDB
Run this script once to populate the vector database
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings
import json
import uuid

# Import profiles from database directory
from database.profiles import PROFILES

# Initialize ChromaDB with persistent storage
persist_directory = str(Path(__file__).parent.parent / "chroma_db")
Path(persist_directory).mkdir(exist_ok=True)

client = chromadb.PersistentClient(
    path=persist_directory,
    settings=Settings(anonymized_telemetry=False)
)

# Get or create collection
collection = client.get_or_create_collection(
    name="ideal_candidate_profiles",
    metadata={"description": "Ideal candidate profiles for job matching"}
)

def create_document_text(profile):
    """Convert profile to searchable text document"""
    parts = []
    parts.append(f"Job Title: {profile['job_title']}")
    parts.append(f"Description: {profile['job_description']}")
    
    if profile.get('must_have_skills'):
        parts.append(f"Must-Have Skills: {', '.join(profile['must_have_skills'])}")
    if profile.get('preferred_skills'):
        parts.append(f"Preferred Skills: {', '.join(profile['preferred_skills'])}")
    if profile.get('years_experience'):
        parts.append(f"Years of Experience: {profile['years_experience']}")
    if profile.get('education_requirements'):
        parts.append(f"Education: {', '.join(profile['education_requirements'])}")
    if profile.get('certifications'):
        parts.append(f"Certifications: {', '.join(profile['certifications'])}")
    if profile.get('key_responsibilities'):
        parts.append(f"Responsibilities: {', '.join(profile['key_responsibilities'])}")
    if profile.get('additional_criteria'):
        parts.append(f"Additional: {profile['additional_criteria']}")
    
    return "\n".join(parts)

# Prepare documents and metadata
documents = []
metadatas = []
ids = []

for i, profile in enumerate(PROFILES):
    # Create searchable document text
    doc_text = create_document_text(profile)
    
    # Prepare metadata (convert lists to JSON strings for ChromaDB)
    metadata = {}
    for key, value in profile.items():
        if isinstance(value, list):
            metadata[key] = json.dumps(value)
        elif isinstance(value, (str, int, float, bool)):
            metadata[key] = str(value) if not isinstance(value, bool) else value
        else:
            metadata[key] = str(value)
    
    documents.append(doc_text)
    metadatas.append(metadata)
    ids.append(f"profile_{i}")

# Check if collection is empty, if not, clear it first
existing_count = collection.count()
if existing_count > 0:
    print(f"Found {existing_count} existing profiles. Clearing collection...")
    collection.delete()  # Delete all
    collection = client.get_or_create_collection(
        name="ideal_candidate_profiles",
        metadata={"description": "Ideal candidate profiles for job matching"}
    )

# Add all profiles to collection
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print(f"✅ Successfully loaded {len(PROFILES)} profiles into ChromaDB!")
print(f"   Collection: ideal_candidate_profiles")
print(f"   Storage: {persist_directory}")

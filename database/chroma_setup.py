import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# 1) Initialize Chroma
client = chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False
    )
)

# 2) Create (or load) a collection
collection = client.get_or_create_collection(
    name="ideal_candidate_profiles"
)

# 3) Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

print("ChromaDB setup complete!")

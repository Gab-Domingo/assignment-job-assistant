"""
Quick test script for RAG service
"""
import asyncio
from services.rag_service import RAGService

async def test_rag():
    print("🧪 Testing RAG Service...\n")
    
    rag_service = RAGService()
    
    # Test 1: Get collection stats
    print("1. Collection Stats:")
    stats = rag_service.get_collection_stats()
    print(f"   Collection: {stats['collection_name']}")
    print(f"   Profiles: {stats['profile_count']}\n")
    
    # Test 2: Search for Software Engineer
    print("2. Searching for 'Software Engineer':")
    results = await rag_service.search_ideal_profiles(
        query="Software Engineer",
        job_title="Software Engineer",
        n_results=1
    )
    
    if results:
        result = results[0]
        print(f"   ✅ Found profile: {result['profile']['job_title']}")
        print(f"   Similarity: {result['similarity_score']:.3f}")
        print(f"   Years Experience: {result['profile'].get('years_experience', 'N/A')}")
        print(f"   Must-Have Skills: {', '.join(result['profile'].get('must_have_skills', [])[:3])}...\n")
    else:
        print("   ❌ No results found\n")
    
    # Test 3: List all profiles
    print("3. All Profiles:")
    all_profiles = await rag_service.get_all_profiles()
    for profile in all_profiles[:3]:  # Show first 3
        print(f"   - {profile['profile'].get('job_title', 'N/A')}")
    print(f"   ... and {len(all_profiles) - 3} more\n")
    
    print("✅ RAG Service test complete!")

if __name__ == "__main__":
    asyncio.run(test_rag())

#!/usr/bin/env python3
"""
Debug vector search issue comprehensively
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

def debug_comprehensive():
    """Comprehensive vector search debugging"""
    
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("🔍 COMPREHENSIVE VECTOR SEARCH DEBUG")
    print("=" * 50)
    
    # Step 1: Check raw data
    print("\n1️⃣ CHECKING RAW DATA:")
    chunks_result = supabase.table("document_chunks").select("id, text_content, embedding").limit(2).execute()
    print(f"📊 Found {len(chunks_result.data)} chunks")
    
    if chunks_result.data:
        chunk = chunks_result.data[0]
        embedding = chunk['embedding']
        print(f"📝 First chunk text: {chunk['text_content'][:100]}...")
        print(f"🔢 Embedding type: {type(embedding)}")
        
        # Try to parse the embedding if it's a string
        if isinstance(embedding, str):
            print(f"📄 Embedding string (first 100 chars): {embedding[:100]}...")
            # Try to detect if it's JSON or some other format
            if embedding.startswith('[') and embedding.endswith(']'):
                print("✅ Looks like JSON array format")
                try:
                    import json
                    parsed = json.loads(embedding)
                    print(f"✅ Successfully parsed: {len(parsed)} dimensions")
                except:
                    print("❌ Failed to parse as JSON")
            else:
                print("❌ Unknown embedding format")
    
    # Step 2: Test embedding generation
    print("\n2️⃣ TESTING EMBEDDING GENERATION:")
    query = "tool mode"
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = response.data[0].embedding
    print(f"✅ Generated query embedding: {len(query_embedding)} dimensions")
    
    # Step 3: Test different match_documents parameters
    print("\n3️⃣ TESTING MATCH_DOCUMENTS FUNCTION:")
    
    test_cases = [
        {"threshold": 0.0, "count": 5},
        {"threshold": -1.0, "count": 5},
        {"threshold": 0.5, "count": 10}
    ]
    
    for i, params in enumerate(test_cases):
        try:
            print(f"\nTest {i+1}: threshold={params['threshold']}, count={params['count']}")
            result = supabase.rpc("match_documents", {
                "query_embedding": query_embedding,
                "match_threshold": params['threshold'],
                "match_count": params['count']
            }).execute()
            
            print(f"✅ Function executed successfully")
            print(f"📊 Results: {len(result.data) if result.data else 0}")
            
            if result.data:
                for j, item in enumerate(result.data[:2]):
                    print(f"  Result {j+1}: similarity={item.get('similarity', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Test {i+1} failed: {e}")
    
    # Step 4: Try manual vector similarity
    print("\n4️⃣ TESTING MANUAL VECTOR OPERATIONS:")
    try:
        # Test if we can manually compute similarity using PostgreSQL vector operations
        print("Testing manual vector similarity calculation...")
        
        # This would require raw SQL execution which might not be available
        # Let's just test if our function definitions are working
        functions_result = supabase.rpc("match_documents", {
            "query_embedding": [0.1] * 1536,  # Simple test vector
            "match_threshold": -10.0,  # Extremely low threshold
            "match_count": 1
        }).execute()
        
        print(f"✅ Function exists and executes")
        print(f"📊 Test vector results: {len(functions_result.data) if functions_result.data else 0}")
        
    except Exception as e:
        print(f"❌ Manual test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print("If no results are found with threshold -1.0, the issue is likely:")
    print("1. Vector index not properly created")
    print("2. Embedding format incompatible with vector operations")
    print("3. Function definition mismatch")
    
if __name__ == "__main__":
    debug_comprehensive()
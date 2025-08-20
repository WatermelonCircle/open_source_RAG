#!/usr/bin/env python3
"""
Test vector index and direct similarity operations
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

def test_vector_operations():
    """Test vector operations directly"""
    
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("🔍 Testing vector operations...")
    
    # Generate test embedding
    query = "How do I switch between modes?"
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    try:
        # Test direct vector similarity without function
        print("🧪 Testing direct vector similarity...")
        
        # Use raw SQL through RPC (if available) or try direct table query with vector ops
        # Let's try to get chunks with their similarity scores directly
        chunks_result = supabase.table("document_chunks").select(
            "id, text_content, embedding"
        ).limit(3).execute()
        
        print(f"📊 Retrieved {len(chunks_result.data)} chunks with embeddings")
        
        if chunks_result.data:
            print("✅ Embeddings are stored in database")
            # Check first embedding dimensions
            first_embedding = chunks_result.data[0]['embedding']
            if isinstance(first_embedding, list):
                print(f"✅ First embedding has {len(first_embedding)} dimensions")
            else:
                print(f"⚠️  Embedding format: {type(first_embedding)}")
        
        # Test if the function exists and what parameters it expects
        print("\n🔍 Testing function existence...")
        
        # Try to call with different parameter formats
        test_cases = [
            # Case 1: Array format
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.0,
                "match_count": 3
            }
        ]
        
        for i, params in enumerate(test_cases):
            try:
                print(f"Testing case {i+1}...")
                result = supabase.rpc("match_documents", params).execute()
                print(f"✅ Case {i+1} worked! Got {len(result.data) if result.data else 0} results")
                if result.data:
                    for item in result.data[:2]:  # Show first 2
                        print(f"  - Similarity: {item.get('similarity', 'N/A')}")
                        print(f"  - Text: {item.get('text_content', 'N/A')[:50]}...")
                break  # Stop on first success
            except Exception as e:
                print(f"❌ Case {i+1} failed: {e}")
    
    except Exception as e:
        print(f"❌ Vector operations test failed: {e}")

if __name__ == "__main__":
    test_vector_operations()
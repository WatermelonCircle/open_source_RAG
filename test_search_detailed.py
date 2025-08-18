#!/usr/bin/env python3
"""
Detailed search testing
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

def test_search_detailed():
    """Test search with different thresholds and direct function calls"""
    
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("🔍 Testing search with different approaches...")
    
    # Test 1: Check if data exists
    chunks_result = supabase.table("document_chunks").select("id, text_content, page_number").limit(3).execute()
    print(f"📊 Database contains {len(chunks_result.data)} chunks (showing first 3):")
    for chunk in chunks_result.data[:3]:
        print(f"  - ID: {chunk['id']}")
        print(f"    Text: {chunk['text_content'][:100]}...")
        print(f"    Page: {chunk['page_number']}")
        print()
    
    # Test 2: Generate embedding for search query  
    query = "How do I switch between modes?"
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = response.data[0].embedding
    print(f"✅ Generated query embedding with {len(query_embedding)} dimensions")
    
    # Test 3: Call match_documents function directly with very low threshold
    print("\n🔍 Testing match_documents function...")
    try:
        result = supabase.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_threshold": 0.0,  # Very low threshold
            "match_count": 5
        }).execute()
        
        print(f"📊 match_documents returned {len(result.data) if result.data else 0} results")
        if result.data:
            for i, item in enumerate(result.data):
                print(f"Result {i+1}:")
                print(f"  - Text: {item['text_content'][:100]}...")
                print(f"  - Filename: {item['filename']}")
                print(f"  - Similarity: {item['similarity']}")
                print()
        else:
            print("❌ No results returned from match_documents")
            
    except Exception as e:
        print(f"❌ Error calling match_documents: {e}")

if __name__ == "__main__":
    test_search_detailed()
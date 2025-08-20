#!/usr/bin/env python3
"""
Test database operations directly
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

def test_database_operations():
    """Test database operations directly"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not all([supabase_url, supabase_key, openai_key]):
        print("❌ Missing credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    openai_client = OpenAI(api_key=openai_key)
    
    try:
        print("🧪 Testing database operations...")
        
        # 1. Generate a real OpenAI embedding
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input="test document content"
        )
        embedding = response.data[0].embedding
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        
        # 2. Create a test document
        doc_result = supabase.table("documents").insert({
            "filename": "test.pdf",
            "total_chunks": 1,
            "processed": False
        }).execute()
        
        if not doc_result.data:
            print("❌ Failed to create test document")
            return False
        
        document_id = doc_result.data[0]["id"]
        print(f"✅ Created test document with ID: {document_id}")
        
        # 3. Try direct table insertion
        try:
            chunk_result = supabase.table("document_chunks").insert({
                "document_id": document_id,
                "chunk_index": 0,
                "text_content": "test content",
                "embedding": embedding,
                "page_number": 1
            }).execute()
            
            if chunk_result.data:
                print("✅ Direct table insertion successful!")
                chunk_id = chunk_result.data[0]["id"]
                print(f"   Stored chunk with ID: {chunk_id}")
                
                # Clean up
                supabase.table("document_chunks").delete().eq("id", chunk_id).execute()
                supabase.table("documents").delete().eq("id", document_id).execute()
                print("✅ Cleanup completed")
                return True
            else:
                print("❌ Direct table insertion failed - no data returned")
                return False
                
        except Exception as e:
            print(f"❌ Direct table insertion failed: {e}")
            
            # Clean up document
            supabase.table("documents").delete().eq("id", document_id).execute()
            return False
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    test_database_operations()
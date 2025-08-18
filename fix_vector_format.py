#!/usr/bin/env python3
"""
Fix vector format issue by converting stored JSON strings to proper vectors
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def fix_vector_format():
    """Convert JSON string embeddings to proper vector format"""
    
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    
    print("🔧 Fixing vector format in database...")
    
    try:
        # Get all chunks with their string embeddings
        chunks_result = supabase.table("document_chunks").select("id, embedding").execute()
        print(f"📊 Found {len(chunks_result.data)} chunks to fix")
        
        for i, chunk in enumerate(chunks_result.data):
            chunk_id = chunk['id']
            embedding_str = chunk['embedding']
            
            print(f"Processing chunk {i+1}/{len(chunks_result.data)}")
            
            if isinstance(embedding_str, str):
                try:
                    # Parse the JSON string to get the array
                    embedding_array = json.loads(embedding_str)
                    
                    # Format as PostgreSQL vector literal
                    vector_literal = f"[{','.join(map(str, embedding_array))}]"
                    
                    # Update using a custom RPC function that can handle raw SQL
                    # Since we can't execute raw SQL directly, let's try the insert function approach
                    print(f"  - Embedding has {len(embedding_array)} dimensions")
                    
                    # We'll need to use the SQL editor in Supabase dashboard for this
                    print(f"  - Chunk ID: {chunk_id}")
                    print(f"  - Vector format ready for SQL update")
                    
                except json.JSONDecodeError as e:
                    print(f"  ❌ Failed to parse embedding for chunk {chunk_id}: {e}")
            else:
                print(f"  ✅ Chunk {chunk_id} already has proper format")
        
        print("\n💡 MANUAL FIX REQUIRED:")
        print("Go to Supabase Dashboard > SQL Editor and run this query:")
        print("""
-- Update embeddings from JSON strings to proper vectors
UPDATE document_chunks 
SET embedding = (embedding::text)::vector(1536)
WHERE embedding::text ~ '^\\[.*\\]$';
        """)
        
        print("\nThis will convert JSON array strings to proper PostgreSQL vectors.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_vector_format()
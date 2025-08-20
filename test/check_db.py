#!/usr/bin/env python3
"""
Script to check if documents have been uploaded to Supabase database
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def check_database():
    """Check documents and chunks in the database"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Missing Supabase credentials")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Check documents
        print("Checking documents...")
        docs_result = supabase.table("documents").select("*").execute()
        print(f"📄 Documents found: {len(docs_result.data)}")
        
        for doc in docs_result.data:
            print(f"  - {doc['filename']} (chunks: {doc.get('total_chunks', 0)}, processed: {doc.get('processed', False)})")
        
        # Check chunks
        print("\nChecking document chunks...")
        chunks_result = supabase.table("document_chunks").select("id, document_id, chunk_index").execute()
        print(f"📝 Chunks found: {len(chunks_result.data)}")
        
        if chunks_result.data:
            # Group by document_id
            by_doc = {}
            for chunk in chunks_result.data:
                doc_id = chunk['document_id']
                if doc_id not in by_doc:
                    by_doc[doc_id] = 0
                by_doc[doc_id] += 1
            
            for doc_id, count in by_doc.items():
                print(f"  - Document {doc_id}: {count} chunks")
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()
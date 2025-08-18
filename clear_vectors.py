#!/usr/bin/env python3
"""
Script to clear old vector data from Supabase database
This is needed when switching embedding models with different dimensions
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def clear_vector_data():
    """Clear all documents and chunks from the database"""
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Missing Supabase credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        print("Clearing document chunks...")
        # Clear chunks first (due to foreign key constraints)
        result = supabase.table("document_chunks").delete().gt("created_at", "1900-01-01").execute()
        chunks_deleted = len(result.data) if result.data else 0
        print(f"Deleted {chunks_deleted} document chunks")
        
        print("Clearing documents...")
        # Clear documents
        result = supabase.table("documents").delete().gt("created_at", "1900-01-01").execute()
        docs_deleted = len(result.data) if result.data else 0
        print(f"Deleted {docs_deleted} documents")
        
        print("✅ Database cleared successfully!")
        print("You can now add new documents with OpenAI embeddings.")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False

if __name__ == "__main__":
    clear_vector_data()
#!/usr/bin/env python3
"""
Clear all data from database for fresh testing
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def clear_database():
    """Clear all data from database tables"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        print("🗑️  Clearing all data from database...")
        
        # Delete all chunks first (due to foreign key constraint)
        chunks_result = supabase.table("document_chunks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Deleted {len(chunks_result.data) if chunks_result.data else 0} chunks")
        
        # Delete all documents
        docs_result = supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Deleted {len(docs_result.data) if docs_result.data else 0} documents")
        
        print("🎉 Database cleared successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False

if __name__ == "__main__":
    clear_database()
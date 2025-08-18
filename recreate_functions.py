#!/usr/bin/env python3
"""
Recreate Supabase database functions for OpenAI embeddings
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def recreate_functions():
    """Recreate database functions for 1536 dimensions"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        print("🔧 Checking existing database functions...")
        
        # Let's check what functions exist
        print("📊 Available RPC functions:")
        
        # Try calling match_documents with 1536 dimensions to see if it works
        test_embedding = [0.0] * 1536  # Create test 1536-dimension vector
        
        try:
            result = supabase.rpc("match_documents", {
                "query_embedding": test_embedding,
                "match_threshold": 0.1,
                "match_count": 1
            }).execute()
            print("✅ match_documents function works with 1536 dimensions!")
            return True
            
        except Exception as e:
            print(f"❌ match_documents function error: {e}")
            
            # Try with 384 dimensions to confirm the issue
            test_embedding_384 = [0.0] * 384
            try:
                result = supabase.rpc("match_documents", {
                    "query_embedding": test_embedding_384,
                    "match_threshold": 0.1,
                    "match_count": 1
                }).execute()
                print("✅ Function expects 384 dimensions - confirmed schema needs update")
                
            except Exception as e2:
                print(f"❌ Function also fails with 384 dimensions: {e2}")
        
        print("\n💡 Manual schema update required:")
        print("   Go to Supabase Dashboard > SQL Editor and run:")
        print("   1. ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536);")
        print("   2. Update match_documents function to use vector(1536)")
        print("   3. Update insert_document_chunk function to use vector(1536)")
        
        return False
        
    except Exception as e:
        print(f"❌ Error checking functions: {e}")
        return False

if __name__ == "__main__":
    recreate_functions()
#!/usr/bin/env python3
"""
Update Supabase database schema for OpenAI embeddings (1536 dimensions)
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def update_schema():
    """Update database schema for OpenAI embeddings"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        print("🔧 Updating Supabase schema for OpenAI embeddings (1536 dimensions)...")
        
        # Drop and recreate the match_documents function with correct dimensions
        update_function_sql = """
        -- Drop existing function
        DROP FUNCTION IF EXISTS match_documents(vector(384), float, int);
        DROP FUNCTION IF EXISTS match_documents(vector(1536), float, int);
        
        -- Create new function for 1536 dimensions
        CREATE OR REPLACE FUNCTION match_documents(
          query_embedding vector(1536),
          match_threshold float,
          match_count int
        )
        RETURNS TABLE (
          id bigint,
          text_content text,
          filename text,
          page_number int,
          similarity float
        )
        LANGUAGE sql STABLE
        AS $$
        SELECT
          dc.id,
          dc.text_content,
          d.filename,
          dc.page_number,
          1 - (dc.embedding <=> query_embedding) AS similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
        ORDER BY dc.embedding <=> query_embedding
        LIMIT match_count;
        $$;
        """
        
        # Execute the function update
        result = supabase.rpc("exec", {"sql": update_function_sql}).execute()
        print("✅ Updated match_documents function for 1536 dimensions")
        
        # Update insert function for 1536 dimensions
        insert_function_sql = """
        -- Drop existing insert function
        DROP FUNCTION IF EXISTS insert_document_chunk(bigint, int, text, vector(384), int);
        DROP FUNCTION IF EXISTS insert_document_chunk(bigint, int, text, vector(1536), int);
        
        -- Create new insert function for 1536 dimensions
        CREATE OR REPLACE FUNCTION insert_document_chunk(
          doc_id bigint,
          chunk_idx int,
          content text,
          embed_array float[],
          page_num int
        )
        RETURNS bigint
        LANGUAGE plpgsql
        AS $$
        DECLARE
          chunk_id bigint;
        BEGIN
          INSERT INTO document_chunks (document_id, chunk_index, text_content, embedding, page_number)
          VALUES (doc_id, chunk_idx, content, embed_array::vector(1536), page_num)
          RETURNING id INTO chunk_id;
          
          RETURN chunk_id;
        END;
        $$;
        """
        
        result = supabase.rpc("exec", {"sql": insert_function_sql}).execute()
        print("✅ Updated insert_document_chunk function for 1536 dimensions")
        
        print("🎉 Schema update completed successfully!")
        print("✅ Database now supports OpenAI embeddings (1536 dimensions)")
        return True
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        
        # Fallback: Try to update the table directly if functions fail
        try:
            print("🔄 Trying alternative approach - updating table schema...")
            
            # Check current table structure
            result = supabase.rpc("exec", {"sql": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'document_chunks' AND column_name = 'embedding';"}).execute()
            print(f"📊 Current embedding column: {result.data}")
            
            # Alter table to support 1536 dimensions
            alter_sql = """
            -- Update embedding column to support 1536 dimensions
            ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536);
            """
            
            result = supabase.rpc("exec", {"sql": alter_sql}).execute()
            print("✅ Updated document_chunks table for 1536 dimensions")
            
            return True
            
        except Exception as e2:
            print(f"❌ Alternative approach also failed: {e2}")
            print("💡 You may need to update the schema manually in Supabase dashboard")
            print("   1. Go to SQL editor in Supabase dashboard")
            print("   2. Run: ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536);")
            print("   3. Update the match_documents function for vector(1536)")
            return False

if __name__ == "__main__":
    update_schema()
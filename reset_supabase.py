#!/usr/bin/env python3
"""
Reset and recreate Supabase database schema from scratch
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def reset_supabase_schema():
    """Reset and recreate the Supabase schema properly"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        print("🗑️  Resetting Supabase database schema...")
        
        # Step 1: Drop existing tables
        drop_tables_sql = """
        -- Drop tables in correct order (due to foreign keys)
        DROP TABLE IF EXISTS document_chunks CASCADE;
        DROP TABLE IF EXISTS documents CASCADE;
        
        -- Drop any existing functions
        DROP FUNCTION IF EXISTS match_documents CASCADE;
        DROP FUNCTION IF EXISTS insert_document_chunk CASCADE;
        """
        
        print("🔧 Dropping existing tables and functions...")
        try:
            result = supabase.rpc("sql", {"query": drop_tables_sql}).execute()
            print("✅ Existing schema dropped")
        except Exception as e:
            print(f"⚠️  Some components may not have existed: {e}")
        
        # Step 2: Create documents table
        create_documents_sql = """
        -- Enable pgvector extension
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- Create documents table
        CREATE TABLE documents (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            file_size INTEGER,
            total_chunks INTEGER DEFAULT 0,
            processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        print("🏗️  Creating documents table...")
        result = supabase.rpc("sql", {"query": create_documents_sql}).execute()
        print("✅ Documents table created")
        
        # Step 3: Create document_chunks table with correct vector dimensions
        create_chunks_sql = """
        -- Create document_chunks table with 1536 dimensions for OpenAI embeddings
        CREATE TABLE document_chunks (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            text_content TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            page_number INTEGER DEFAULT 1,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Create unique constraint
            UNIQUE(document_id, chunk_index)
        );
        
        -- Create index for vector similarity search
        CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        
        -- Create index for faster lookups
        CREATE INDEX ON document_chunks (document_id);
        CREATE INDEX ON document_chunks (page_number);
        """
        
        print("🏗️  Creating document_chunks table with 1536-dimension vectors...")
        result = supabase.rpc("sql", {"query": create_chunks_sql}).execute()
        print("✅ Document chunks table created with correct dimensions")
        
        # Step 4: Create match_documents function
        create_match_function_sql = """
        -- Create match_documents function for similarity search
        CREATE OR REPLACE FUNCTION match_documents(
          query_embedding vector(1536),
          match_threshold float DEFAULT 0.2,
          match_count int DEFAULT 5
        )
        RETURNS TABLE (
          id uuid,
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
        
        print("🏗️  Creating match_documents function...")
        result = supabase.rpc("sql", {"query": create_match_function_sql}).execute()
        print("✅ Match documents function created")
        
        # Step 5: Create insert function (optional, we can use direct table insertion)
        create_insert_function_sql = """
        -- Create insert function for document chunks
        CREATE OR REPLACE FUNCTION insert_document_chunk(
          doc_id uuid,
          chunk_idx int,
          content text,
          embed_array float[],
          page_num int DEFAULT 1
        )
        RETURNS uuid
        LANGUAGE plpgsql
        AS $$
        DECLARE
          chunk_id uuid;
        BEGIN
          INSERT INTO document_chunks (document_id, chunk_index, text_content, embedding, page_number)
          VALUES (doc_id, chunk_idx, content, embed_array::vector(1536), page_num)
          RETURNING id INTO chunk_id;
          
          RETURN chunk_id;
        END;
        $$;
        """
        
        print("🏗️  Creating insert function...")
        result = supabase.rpc("sql", {"query": create_insert_function_sql}).execute()
        print("✅ Insert function created")
        
        print("🎉 Database schema reset completed successfully!")
        print("✅ Fresh database ready for OpenAI embeddings (1536 dimensions)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

if __name__ == "__main__":
    success = reset_supabase_schema()
    if success:
        print("\n🚀 Ready to test document upload with fresh schema!")
    else:
        print("\n💡 You may need to reset manually in Supabase dashboard")
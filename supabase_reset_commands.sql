-- =============================================================================
-- SUPABASE DATABASE RESET - COPY AND PASTE THESE COMMANDS
-- =============================================================================
-- Go to your Supabase Dashboard > SQL Editor
-- Copy and paste these commands section by section

-- 1. CLEANUP: Drop existing tables and functions
-- =============================================================================
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP FUNCTION IF EXISTS match_documents CASCADE;
DROP FUNCTION IF EXISTS insert_document_chunk CASCADE;

-- 2. SETUP: Enable pgvector extension
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- 3. CREATE: Documents table
-- =============================================================================
CREATE TABLE documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    file_size INTEGER,
    total_chunks INTEGER DEFAULT 0,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. CREATE: Document chunks table with 1536-dimension vectors
-- =============================================================================
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

-- 5. CREATE: Indexes for performance
-- =============================================================================
-- Vector similarity search index
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Regular indexes for faster lookups
CREATE INDEX ON document_chunks (document_id);
CREATE INDEX ON document_chunks (page_number);

-- 6. CREATE: Search function for similarity matching
-- =============================================================================
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

-- 7. CREATE: Insert function (optional - we can use direct table insertion)
-- =============================================================================
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

-- =============================================================================
-- VERIFICATION: Check that everything was created correctly
-- =============================================================================
-- You can run these to verify:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'document_chunks';
-- SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public';
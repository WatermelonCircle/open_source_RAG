"""
Supabase Vector Store for RAG System

This module replaces ChromaDB with Supabase PostgreSQL + pgvector
for persistent vector storage and similarity search.
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from supabase import create_client, Client
from .config import settings

class SupabaseVectorStore:
    """Vector store implementation using Supabase PostgreSQL with pgvector"""
    
    def __init__(self):
        # Initialize Supabase client
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("Supabase URL and ANON_KEY are required")
        
        try:
            # Try with minimal options first
            self.supabase: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            raise
        
        # Initialize OpenAI client for embeddings
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print(f"Initialized Supabase vector store with OpenAI model: {settings.EMBEDDING_MODEL}")
    
    def add_documents(self, documents: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """
        Add documents to the vector store
        
        Args:
            documents: List of document chunks with text and metadata
            filename: Name of the uploaded file
            
        Returns:
            Dictionary with processing results
        """
        try:
            # First, create a document record
            document_data = {
                "filename": filename,
                "file_size": None,  # You can add this if needed
                "total_chunks": len(documents),
                "processed": False
            }
            
            # Insert document record
            doc_result = self.supabase.table("documents").insert(document_data).execute()
            
            if not doc_result.data:
                raise Exception("Failed to create document record")
            
            document_id = doc_result.data[0]["id"]
            
            # Process each chunk
            chunks_added = 0
            for i, doc in enumerate(documents):
                try:
                    # Debug: Print what we're actually receiving
                    print(f"🔍 Processing chunk {i}: type={type(doc)}, doc={doc}")
                    
                    text = doc.get("text", "")
                    if not text.strip():
                        continue
                    
                    # Generate embedding using OpenAI
                    response = self.openai_client.embeddings.create(
                        model=settings.EMBEDDING_MODEL,
                        input=text
                    )
                    embedding_list = response.data[0].embedding
                    
                    # Use RPC function with proper array formatting
                    chunk_result = self.supabase.rpc("insert_document_chunk", {
                        "doc_id": str(document_id),
                        "chunk_idx": i,
                        "content": text,
                        "embed_array": embedding_list,
                        "page_num": doc.get("page_number", 1)
                    }).execute()
                    
                    if chunk_result.data is not None:
                        chunks_added += 1
                        
                except Exception as e:
                    print(f"Error processing chunk {i}: {e}")
                    continue
            
            # Update document as processed
            self.supabase.table("documents").update({
                "processed": True,
                "total_chunks": chunks_added
            }).eq("id", document_id).execute()
            
            return {
                "document_id": document_id,
                "chunks_added": chunks_added,
                "total_chunks": len(documents),
                "success": True
            }
            
        except Exception as e:
            print(f"Error adding documents: {e}")
            return {
                "chunks_added": 0,
                "total_chunks": len(documents),
                "success": False,
                "error": str(e)
            }
    
    def similarity_search(self, query: str, top_k: int = 5, threshold: float = 0.2) -> List[Dict[str, Any]]:
        """
        Perform similarity search using vector embeddings (manual computation)
        
        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar documents with metadata
        """
        try:
            import json
            import math
            
            def cosine_similarity(vec1, vec2):
                """Compute cosine similarity between two vectors"""
                dot_product = sum(a * b for a, b in zip(vec1, vec2))
                magnitude1 = math.sqrt(sum(a * a for a in vec1))
                magnitude2 = math.sqrt(sum(a * a for a in vec2))
                return dot_product / (magnitude1 * magnitude2)
            
            # Generate query embedding using OpenAI
            response = self.openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=query
            )
            query_embedding = response.data[0].embedding
            
            # Get all chunks with embeddings
            result = self.supabase.table("document_chunks").select(
                "id, text_content, embedding, page_number, documents!inner(filename)"
            ).execute()
            
            if not result.data:
                return []
            
            # Compute similarities manually
            similarities = []
            for chunk in result.data:
                try:
                    # Parse embedding from JSON string
                    if isinstance(chunk['embedding'], str):
                        chunk_embedding = json.loads(chunk['embedding'])
                    else:
                        chunk_embedding = chunk['embedding']
                    
                    # Compute similarity
                    similarity = cosine_similarity(query_embedding, chunk_embedding)
                    
                    if similarity >= threshold:
                        similarities.append({
                            'id': chunk['id'],
                            'text': chunk['text_content'],
                            'similarity_score': similarity,
                            'filename': chunk.get('documents', {}).get('filename', 'unknown'),
                            'page_number': chunk['page_number']
                        })
                        
                except Exception as e:
                    print(f"Error processing chunk {chunk['id']}: {e}")
                    continue
            
            # Sort by similarity (descending) and return top_k
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get all documents in the vector store
        
        Returns:
            List of all documents with metadata
        """
        try:
            result = self.supabase.table("documents").select("*").execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting all documents: {e}")
            return []
    
    def delete_document(self, filename: str) -> bool:
        """
        Delete a document and all its chunks
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete document (chunks will be deleted by cascade)
            result = self.supabase.table("documents").delete().eq("filename", filename).execute()
            return bool(result.data)
            
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    def get_document_count(self) -> int:
        """
        Get total number of documents
        
        Returns:
            Number of documents in the store
        """
        try:
            result = self.supabase.table("documents").select("id", count="exact").execute()
            return result.count if result.count else 0
            
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0
    
    def get_chunk_count(self) -> int:
        """
        Get total number of chunks
        
        Returns:
            Number of chunks in the store
        """
        try:
            result = self.supabase.table("document_chunks").select("id", count="exact").execute()
            return result.count if result.count else 0
            
        except Exception as e:
            print(f"Error getting chunk count: {e}")
            return 0

# Create global instance
vector_store = SupabaseVectorStore()
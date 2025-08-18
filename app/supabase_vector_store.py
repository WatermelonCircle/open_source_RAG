"""
Supabase Vector Store for RAG System

This module replaces ChromaDB with Supabase PostgreSQL + pgvector
for persistent vector storage and similarity search.
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from .config import settings

class SupabaseVectorStore:
    """Vector store implementation using Supabase PostgreSQL with pgvector"""
    
    def __init__(self):
        # Initialize Supabase client
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("Supabase URL and ANON_KEY are required")
        
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        print(f"Initialized Supabase vector store with model: {settings.EMBEDDING_MODEL}")
    
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
                    text = doc.get("text", "")
                    if not text.strip():
                        continue
                    
                    # Generate embedding
                    embedding_array = self.embedding_model.encode(text)
                    embedding_list = embedding_array.tolist()
                    
                    # Use custom function to insert with proper vector casting
                    chunk_result = self.supabase.rpc("insert_document_chunk", {
                        "doc_id": document_id,
                        "chunk_idx": i,
                        "content": text,
                        "embed_array": embedding_list,
                        "page_num": doc.get("page_number", 1)
                    }).execute()
                    
                    if chunk_result.data:
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
        Perform similarity search using vector embeddings
        
        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar documents with metadata
        """
        try:
            # Generate query embedding
            query_embedding_array = self.embedding_model.encode(query)
            query_embedding_list = query_embedding_array.tolist()
            
            # Call the match_documents function with array format
            result = self.supabase.rpc("match_documents", {
                "query_embedding": query_embedding_list,
                "match_threshold": threshold,
                "match_count": top_k
            }).execute()
            
            if not result.data:
                return []
            
            # Format results
            documents = []
            for item in result.data:
                documents.append({
                    "id": item["id"],
                    "text": item["text_content"],
                    "filename": item["filename"],
                    "page_number": item["page_number"],
                    "similarity_score": item["similarity"]
                })
            
            return documents
            
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
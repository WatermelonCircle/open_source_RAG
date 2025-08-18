"""
Vector Store Service using Chroma

This module handles:
1. Embedding generation for text chunks
2. Storage and retrieval from Chroma vector database
3. Similarity search for RAG queries

Chroma is used as our vector database for storing document embeddings
with metadata for source citations.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import os
from .models import TextChunk
from .config import settings

class VectorStore:
    """Handles vector embeddings and similarity search using Chroma"""
    
    def __init__(self):
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"description": "RAG document embeddings"}
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        print(f"Initialized vector store with model: {settings.EMBEDDING_MODEL}")
    
    def add_documents(self, chunks: List[TextChunk]) -> int:
        """
        Add document chunks to the vector store
        
        Args:
            chunks: List of TextChunk objects to add
            
        Returns:
            Number of chunks successfully added
        """
        if not chunks:
            return 0
        
        # Prepare data for Chroma
        texts = [chunk.text for chunk in chunks]
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            # Create unique ID for each chunk
            chunk_id = f"{chunk.filename}_{chunk.page_number}_{chunk.chunk_index}_{i}"
            ids.append(chunk_id)
            
            # Prepare metadata for Chroma
            metadata = {
                "filename": chunk.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "text_length": len(chunk.text),
                **chunk.metadata
            }
            metadatas.append(metadata)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to Chroma collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(chunks)
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Search query text
            n_results: Number of results to return
            
        Returns:
            List of similar document chunks with metadata
        """
        # Generate embedding for query
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Search in Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        similar_docs = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                # Chroma uses cosine distance, so similarity = 1 - distance
                # But we need to handle potential negative values due to floating point precision
                distance = results["distances"][0][i]
                similarity = max(0.0, min(1.0, 1 - distance))  # Clamp between 0 and 1
                
                doc = {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": similarity,
                    "filename": results["metadatas"][0][i]["filename"],
                    "page_number": results["metadatas"][0][i]["page_number"]
                }
                similar_docs.append(doc)
        
        return similar_docs
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
        except Exception:
            # Collection might not exist, return 0
            count = 0
        
        return {
            "total_chunks": count,
            "collection_name": settings.COLLECTION_NAME,
            "embedding_model": settings.EMBEDDING_MODEL
        }
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection
        
        Returns:
            True if successful
        """
        try:
            # Delete the collection and recreate it
            self.chroma_client.delete_collection(name=settings.COLLECTION_NAME)
            self.collection = self.chroma_client.get_or_create_collection(
                name=settings.COLLECTION_NAME,
                metadata={"description": "RAG document embeddings"}
            )
            return True
        except Exception:
            return False
    
    def remove_document(self, filename: str) -> int:
        """
        Remove all chunks for a specific document
        
        Args:
            filename: Name of the document to remove
            
        Returns:
            Number of chunks removed
        """
        # Query for all chunks from this document
        results = self.collection.get(
            where={"filename": filename},
            include=["metadatas"]
        )
        
        if results["ids"]:
            # Delete all chunks for this document
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])
        
        return 0
#!/usr/bin/env python3
"""
Test the search functionality directly
"""

from app.supabase_vector_store import vector_store

def test_search():
    """Test similarity search"""
    print("🔍 Testing similarity search...")
    
    # Test search
    results = vector_store.similarity_search("How do I switch between modes?", top_k=3, threshold=0.1)
    
    print(f"📊 Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"Result {i+1}:")
        print(f"  - Text: {result['text'][:100]}...")
        print(f"  - Filename: {result['filename']}")
        print(f"  - Similarity: {result['similarity_score']}")
        print()
    
    # Also check total document count
    doc_count = vector_store.get_document_count()
    chunk_count = vector_store.get_chunk_count()
    print(f"📈 Database stats: {doc_count} documents, {chunk_count} chunks")

if __name__ == "__main__":
    test_search()
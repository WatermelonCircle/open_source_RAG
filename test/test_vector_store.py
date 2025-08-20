"""
Test Vector Store with Chroma

This test verifies that our vector store integration works correctly:
1. Chroma initialization and collection creation
2. Document embedding and storage
3. Similarity search functionality
4. Metadata preservation for citations
5. Document management (add/remove)

Why this test is important:
- Ensures Chroma vector database works correctly
- Verifies embeddings are generated and stored
- Confirms similarity search returns relevant results
- Tests source metadata is preserved for citations
- Validates document management operations

We use sample text chunks to test the vector operations.
"""

import pytest
import tempfile
import shutil
from app.vector_store import VectorStore
from app.models import TextChunk
from app.config import settings

@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for Chroma database during tests"""
    temp_dir = tempfile.mkdtemp()
    
    # Temporarily override the Chroma directory
    original_dir = settings.CHROMA_PERSIST_DIR
    settings.CHROMA_PERSIST_DIR = temp_dir
    
    yield temp_dir
    
    # Restore original setting and cleanup
    settings.CHROMA_PERSIST_DIR = original_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def vector_store(temp_chroma_dir):
    """Create a VectorStore instance for testing"""
    return VectorStore()

@pytest.fixture
def sample_chunks():
    """Create sample text chunks for testing"""
    chunks = [
        TextChunk(
            text="Python is a high-level programming language known for its simplicity and readability.",
            filename="python_guide.pdf",
            page_number=1,
            chunk_index=0,
            metadata={"topic": "programming"}
        ),
        TextChunk(
            text="Machine learning is a subset of artificial intelligence that uses statistical techniques.",
            filename="ml_basics.pdf", 
            page_number=1,
            chunk_index=0,
            metadata={"topic": "machine_learning"}
        ),
        TextChunk(
            text="FastAPI is a modern web framework for building APIs with Python.",
            filename="fastapi_docs.pdf",
            page_number=2,
            chunk_index=1,
            metadata={"topic": "web_development"}
        )
    ]
    return chunks

def test_vector_store_initialization(vector_store):
    """Test that vector store initializes correctly"""
    assert vector_store.collection is not None
    assert vector_store.embedding_model is not None
    
    stats = vector_store.get_collection_stats()
    assert stats["total_chunks"] == 0  # Should start empty
    assert stats["collection_name"] == settings.COLLECTION_NAME
    
    print("✅ Vector store initialized successfully")

def test_add_documents(vector_store, sample_chunks):
    """Test adding documents to the vector store"""
    # Add documents
    num_added = vector_store.add_documents(sample_chunks)
    
    assert num_added == len(sample_chunks)
    
    # Check collection stats
    stats = vector_store.get_collection_stats()
    assert stats["total_chunks"] == len(sample_chunks)
    
    print(f"✅ Successfully added {num_added} document chunks to vector store")

def test_similarity_search(vector_store, sample_chunks):
    """Test similarity search functionality"""
    # First add documents
    vector_store.add_documents(sample_chunks)
    
    # Search for Python-related content
    query = "What is Python programming language?"
    results = vector_store.search_similar(query, n_results=3)
    
    assert len(results) > 0
    assert len(results) <= 3
    
    # Check result structure
    for result in results:
        assert "text" in result
        assert "metadata" in result
        assert "similarity_score" in result
        assert "filename" in result
        assert "page_number" in result
        
        # Similarity score should be between 0 and 1
        assert 0 <= result["similarity_score"] <= 1
    
    # The first result should be most relevant (Python-related)
    top_result = results[0]
    assert "Python" in top_result["text"]
    assert top_result["filename"] == "python_guide.pdf"
    
    print(f"✅ Similarity search returned {len(results)} results")
    print(f"   Top result: {top_result['filename']}, page {top_result['page_number']}")
    print(f"   Similarity score: {top_result['similarity_score']:.3f}")

def test_search_preserves_metadata(vector_store, sample_chunks):
    """Test that search results preserve source metadata for citations"""
    vector_store.add_documents(sample_chunks)
    
    # Search for FastAPI content
    query = "web framework API development"
    results = vector_store.search_similar(query, n_results=1)
    
    assert len(results) > 0
    
    result = results[0]
    metadata = result["metadata"]
    
    # Check that original chunk metadata is preserved
    assert metadata["filename"] == "fastapi_docs.pdf"
    assert metadata["page_number"] == 2
    assert metadata["chunk_index"] == 1
    assert metadata["topic"] == "web_development"
    
    print("✅ Search results preserve metadata for source citations")

def test_remove_document(vector_store, sample_chunks):
    """Test removing documents from vector store"""
    # Add documents first
    vector_store.add_documents(sample_chunks)
    
    initial_stats = vector_store.get_collection_stats()
    assert initial_stats["total_chunks"] == 3
    
    # Remove one document
    removed_count = vector_store.remove_document("python_guide.pdf")
    assert removed_count == 1
    
    # Check that document was removed
    final_stats = vector_store.get_collection_stats()
    assert final_stats["total_chunks"] == 2
    
    # Search should no longer return the removed document
    results = vector_store.search_similar("Python programming", n_results=5)
    filenames = [r["filename"] for r in results]
    assert "python_guide.pdf" not in filenames
    
    print(f"✅ Successfully removed document: {removed_count} chunks deleted")

def test_clear_collection(vector_store, sample_chunks):
    """Test clearing the entire collection"""
    # Add documents first
    vector_store.add_documents(sample_chunks)
    
    initial_stats = vector_store.get_collection_stats()
    assert initial_stats["total_chunks"] == 3
    
    # Clear collection
    success = vector_store.clear_collection()
    assert success is True
    
    # Check that collection is empty
    final_stats = vector_store.get_collection_stats()
    assert final_stats["total_chunks"] == 0
    
    print("✅ Successfully cleared vector store collection")

def test_empty_query(vector_store, sample_chunks):
    """Test handling of empty or invalid queries"""
    vector_store.add_documents(sample_chunks)
    
    # Test empty query
    results = vector_store.search_similar("", n_results=3)
    # Should still return results (or empty list), not crash
    assert isinstance(results, list)
    
    print("✅ Vector store handles edge cases correctly")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
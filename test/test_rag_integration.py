"""
Test RAG Integration

This test verifies that our complete RAG system works end-to-end:
1. PDF upload and processing
2. Vector storage and retrieval
3. Chat endpoint with RAG responses
4. Source citations in responses

Why this test is important:
- Tests the complete workflow from upload to chat
- Verifies all components work together
- Ensures source citations are preserved
- Validates error handling across the system

We mock the Claude API to test without requiring actual API calls.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from main import app

client = TestClient(app)

@pytest.fixture
def sample_pdf_with_content():
    """Create a PDF with specific content for RAG testing"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        c = canvas.Canvas(tmp_file.name, pagesize=letter)
        
        # Page 1 - Python content
        c.drawString(100, 750, "Python Programming Language")
        c.drawString(100, 700, "Python is a high-level programming language.")
        c.drawString(100, 650, "It was created by Guido van Rossum in 1991.")
        c.drawString(100, 600, "Python is known for its simplicity and readability.")
        c.showPage()
        
        # Page 2 - FastAPI content
        c.drawString(100, 750, "FastAPI Web Framework")
        c.drawString(100, 700, "FastAPI is a modern web framework for building APIs.")
        c.drawString(100, 650, "It is built on top of Starlette and Pydantic.")
        c.drawString(100, 600, "FastAPI provides automatic API documentation.")
        c.showPage()
        
        c.save()
        
        yield tmp_file.name
        
        # Cleanup
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

@patch('app.claude_service.anthropic.Anthropic')
def test_full_rag_workflow(mock_anthropic, sample_pdf_with_content):
    """Test complete RAG workflow from upload to chat"""
    # Mock Claude API response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Based on the documents, Python is a high-level programming language created by Guido van Rossum in 1991, known for its simplicity and readability.")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client
    
    # Step 1: Upload PDF
    with open(sample_pdf_with_content, 'rb') as f:
        files = {'files': (os.path.basename(sample_pdf_with_content), f, 'application/pdf')}
        upload_response = client.post("/upload", files=files)
    
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["success"] is True
    assert upload_data["files_processed"] == 1
    
    print(f"✅ Document uploaded: {upload_data['processed_files'][0]['chunks_created']} chunks created")
    
    # Step 2: Ask a question about Python
    chat_payload = {"message": "What is Python and who created it?"}
    chat_response = client.post("/chat", json=chat_payload)
    
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    
    # Verify response structure
    assert "response" in chat_data
    assert "sources" in chat_data
    assert "timestamp" in chat_data
    
    # Verify Claude was called
    mock_client.messages.create.assert_called_once()
    
    # Verify response content
    assert "Python" in chat_data["response"]
    assert "high-level programming language" in chat_data["response"]
    
    # Verify sources are included
    assert len(chat_data["sources"]) > 0
    source_filenames = [s["filename"] for s in chat_data["sources"]]
    assert os.path.basename(sample_pdf_with_content) in source_filenames
    
    print(f"✅ RAG chat response generated with {len(chat_data['sources'])} sources")
    
    # Step 3: Ask about FastAPI
    chat_payload2 = {"message": "Tell me about FastAPI"}
    chat_response2 = client.post("/chat", json=chat_payload2)
    
    assert chat_response2.status_code == 200
    chat_data2 = chat_response2.json()
    
    # Should find FastAPI content from page 2
    sources = chat_data2["sources"]
    page_numbers = [s["page"] for s in sources]
    assert 2 in page_numbers  # Should reference page 2 which has FastAPI content
    
    print("✅ RAG system correctly retrieves content from different pages")

def test_chat_without_documents():
    """Test chat endpoint when no documents are uploaded"""
    # Clear any existing documents from vector store
    from app.vector_store import VectorStore
    vector_store = VectorStore()
    vector_store.clear_collection()
    
    chat_payload = {"message": "What is machine learning?"}
    chat_response = client.post("/chat", json=chat_payload)
    
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    
    # Should indicate no documents available
    assert "upload" in chat_data["response"].lower() or "documents" in chat_data["response"].lower()
    assert len(chat_data["sources"]) == 0
    
    print("✅ RAG system handles no-documents case appropriately")

def test_document_listing():
    """Test document listing endpoint"""
    response = client.get("/documents")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "documents" in data
    assert isinstance(data["documents"], list)
    
    print(f"✅ Document listing endpoint works: {len(data['documents'])} documents found")

@patch('app.claude_service.anthropic.Anthropic')
def test_rag_with_irrelevant_query(mock_anthropic, sample_pdf_with_content):
    """Test RAG behavior with query not relevant to uploaded documents"""
    # Mock Claude API response for irrelevant query
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="I don't have information about quantum physics in the provided documents. The documents contain information about Python programming and FastAPI.")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client
    
    # Upload document first
    with open(sample_pdf_with_content, 'rb') as f:
        files = {'files': (os.path.basename(sample_pdf_with_content), f, 'application/pdf')}
        client.post("/upload", files=files)
    
    # Ask about something not in the documents
    chat_payload = {"message": "What is quantum physics?"}
    chat_response = client.post("/chat", json=chat_payload)
    
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    
    # Should still return sources (the most similar chunks found)
    # but Claude should indicate the information isn't in the documents
    assert len(chat_data["sources"]) > 0  # Sources are retrieved regardless
    
    print("✅ RAG system handles irrelevant queries appropriately")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
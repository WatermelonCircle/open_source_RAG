"""
Test Upload Endpoint

This test verifies that our PDF upload endpoint works correctly:
1. File upload accepts PDF files
2. File validation works (rejects non-PDFs, large files)
3. PDF processing happens correctly
4. Response includes correct metadata

Why this test is important:
- Ensures file upload security and validation
- Verifies PDF processing integration
- Confirms correct API response format
- Tests error handling for invalid files

We create test PDF files and test various upload scenarios.
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from main import app

client = TestClient(app)

@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing uploads"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        # Create a simple PDF
        c = canvas.Canvas(tmp_file.name, pagesize=letter)
        c.drawString(100, 750, "This is a test PDF for upload testing.")
        c.drawString(100, 700, "It contains sample content for processing.")
        c.showPage()
        c.save()
        
        yield tmp_file.name
        
        # Cleanup
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing file type validation"""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
        tmp_file.write(b"This is a text file, not a PDF")
        
        yield tmp_file.name
        
        # Cleanup
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

def test_upload_valid_pdf(sample_pdf_file):
    """Test uploading a valid PDF file"""
    with open(sample_pdf_file, 'rb') as f:
        files = {'files': (os.path.basename(sample_pdf_file), f, 'application/pdf')}
        response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["files_processed"] == 1
    assert len(data["processed_files"]) == 1
    assert len(data["failed_files"]) == 0
    
    # Check processed file details
    processed_file = data["processed_files"][0]
    assert processed_file["filename"] == os.path.basename(sample_pdf_file)
    assert processed_file["page_count"] == 1
    assert processed_file["chunks_created"] > 0
    assert processed_file["chunks_stored"] > 0
    assert processed_file["file_size"] > 0
    
    print(f"✅ Successfully uploaded PDF: {processed_file['chunks_created']} chunks created, {processed_file['chunks_stored']} stored")

def test_upload_invalid_file_type(sample_text_file):
    """Test uploading a non-PDF file"""
    with open(sample_text_file, 'rb') as f:
        files = {'files': (os.path.basename(sample_text_file), f, 'text/plain')}
        response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert data["files_processed"] == 0
    assert len(data["processed_files"]) == 0
    assert len(data["failed_files"]) == 1
    assert "Not a PDF file" in data["failed_files"][0]
    
    print("✅ Correctly rejected non-PDF file")

def test_upload_multiple_files(sample_pdf_file):
    """Test uploading multiple PDF files"""
    # Create a second PDF file
    with tempfile.NamedTemporaryFile(suffix='_2.pdf', delete=False) as tmp_file2:
        c = canvas.Canvas(tmp_file2.name, pagesize=letter)
        c.drawString(100, 750, "This is the second test PDF.")
        c.showPage()
        c.save()
        
        try:
            files = []
            with open(sample_pdf_file, 'rb') as f1, open(tmp_file2.name, 'rb') as f2:
                files = [
                    ('files', (os.path.basename(sample_pdf_file), f1, 'application/pdf')),
                    ('files', (os.path.basename(tmp_file2.name), f2, 'application/pdf'))
                ]
                response = client.post("/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["files_processed"] == 2
            assert len(data["processed_files"]) == 2
            assert len(data["failed_files"]) == 0
            
            print(f"✅ Successfully uploaded {data['files_processed']} PDF files")
            
        finally:
            # Cleanup
            if os.path.exists(tmp_file2.name):
                os.unlink(tmp_file2.name)

def test_upload_no_files():
    """Test upload endpoint with no files"""
    response = client.post("/upload", files={})
    
    assert response.status_code == 422  # FastAPI validation error
    print("✅ Correctly handled no files upload")

def test_documents_list_endpoint():
    """Test the documents listing endpoint"""
    response = client.get("/documents")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "documents" in data
    assert isinstance(data["documents"], list)
    
    print(f"✅ Documents endpoint working, found {len(data['documents'])} documents")

def test_chat_endpoint_placeholder():
    """Test the chat endpoint (placeholder for now)"""
    response = client.post("/chat", json={"message": "Test question"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "response" in data
    assert "sources" in data
    assert "timestamp" in data
    
    print("✅ Chat endpoint responding (placeholder implementation)")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Test Document Processor

This test verifies that our document processing works correctly:
1. PDF text extraction maintains page information
2. Text chunking preserves source metadata
3. Document metadata extraction works
4. File saving functionality works

Why this test is important:
- Ensures PDF processing extracts text correctly
- Verifies source tracking for citations
- Confirms chunking maintains metadata
- Tests file upload handling

We create a sample PDF programmatically to test with.
"""

import pytest
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from app.document_processor import DocumentProcessor
from app.models import TextChunk, DocumentMetadata

@pytest.fixture
def document_processor():
    """Create a DocumentProcessor instance for testing"""
    return DocumentProcessor()

@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        # Create a simple PDF with reportlab
        c = canvas.Canvas(tmp_file.name, pagesize=letter)
        
        # Page 1
        c.drawString(100, 750, "This is page 1 of the test document.")
        c.drawString(100, 700, "It contains some sample text for testing.")
        c.showPage()
        
        # Page 2
        c.drawString(100, 750, "This is page 2 with different content.")
        c.drawString(100, 700, "We use this to test multi-page processing.")
        c.showPage()
        
        c.save()
        
        yield tmp_file.name
        
        # Cleanup
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

def test_extract_text_from_pdf(document_processor, sample_pdf):
    """Test PDF text extraction with page tracking"""
    chunks = document_processor.extract_text_from_pdf(sample_pdf)
    
    # Should have chunks from the PDF
    assert len(chunks) > 0
    print(f"✅ Extracted {len(chunks)} chunks from PDF")
    
    # Check that chunks have correct structure
    for chunk in chunks:
        assert isinstance(chunk, TextChunk)
        assert chunk.filename == os.path.basename(sample_pdf)
        assert chunk.page_number > 0
        assert len(chunk.text) > 0
        print(f"✅ Chunk from page {chunk.page_number} has {len(chunk.text)} characters")
    
    # Should have chunks from both pages
    page_numbers = [chunk.page_number for chunk in chunks]
    assert 1 in page_numbers
    assert 2 in page_numbers
    print("✅ PDF text extraction maintains page information correctly")

def test_get_document_metadata(document_processor, sample_pdf):
    """Test document metadata extraction"""
    metadata = document_processor.get_document_metadata(sample_pdf)
    
    assert isinstance(metadata, DocumentMetadata)
    assert metadata.filename == os.path.basename(sample_pdf)
    assert metadata.page_count == 2  # Our sample PDF has 2 pages
    assert metadata.file_size > 0
    assert metadata.upload_timestamp is not None
    
    print(f"✅ Document metadata: {metadata.filename}, {metadata.page_count} pages, {metadata.file_size} bytes")

def test_save_uploaded_file(document_processor):
    """Test file saving functionality"""
    test_content = b"This is test file content"
    filename = "test_file.txt"
    
    saved_path = document_processor.save_uploaded_file(test_content, filename)
    
    # Check file was saved
    assert os.path.exists(saved_path)
    
    # Check content is correct
    with open(saved_path, 'rb') as f:
        saved_content = f.read()
    assert saved_content == test_content
    
    # Cleanup
    os.unlink(saved_path)
    print("✅ File saving and retrieval works correctly")

def test_text_chunking_preserves_metadata(document_processor):
    """Test that text chunking maintains source information"""
    test_text = "This is a long piece of text that should be split into multiple chunks for processing. " * 50
    
    chunks = document_processor._split_text_into_chunks(test_text, 1, "test.pdf")
    
    assert len(chunks) > 1  # Should be split into multiple chunks
    
    for i, chunk in enumerate(chunks):
        assert chunk.filename == "test.pdf"
        assert chunk.page_number == 1
        assert chunk.chunk_index == i
        assert "word_count" in chunk.metadata
        assert "char_count" in chunk.metadata
        
    print(f"✅ Text chunking created {len(chunks)} chunks with preserved metadata")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
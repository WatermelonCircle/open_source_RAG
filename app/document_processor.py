"""
Document Processing Module

This module handles:
1. PDF text extraction with page tracking
2. Text chunking with source metadata
3. Document metadata extraction

Each function is designed to maintain source information for citations.
"""

import os
from pypdf import PdfReader
from typing import List, Dict, Any
from datetime import datetime
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from .models import DocumentMetadata, TextChunk
from .config import settings

class DocumentProcessor:
    """Handles PDF processing and text extraction with source tracking"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[TextChunk]:
        """
        Extract text from PDF with page-level tracking
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of TextChunk objects with source metadata
        """
        chunks = []
        filename = os.path.basename(pdf_path)
        
        try:
            pdf_reader = PdfReader(pdf_path)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    
                    # If no text extracted, try OCR
                    if not text.strip():
                        try:
                            text = self._extract_text_with_ocr(pdf_path, page_num)
                        except Exception as ocr_error:
                            print(f"OCR failed for page {page_num}: {ocr_error}")
                            continue
                    
                    if text.strip():  # Only process non-empty pages
                        # Split page text into smaller chunks
                        page_chunks = self._split_text_into_chunks(text, page_num, filename)
                        chunks.extend(page_chunks)
                        
        except Exception as e:
            raise ValueError(f"Error processing PDF {filename}: {str(e)}")
            
        return chunks
    
    def _extract_text_with_ocr(self, pdf_path: str, page_num: int) -> str:
        """
        Extract text from a specific PDF page using OCR
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (1-indexed)
            
        Returns:
            Extracted text from the page
        """
        try:
            # Convert specific page to image
            images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=300)
            
            if not images:
                return ""
            
            # Perform OCR on the image
            text = pytesseract.image_to_string(images[0], lang='eng')
            return text
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def _split_text_into_chunks(self, text: str, page_num: int, filename: str) -> List[TextChunk]:
        """
        Split text into smaller chunks while preserving source information
        
        Args:
            text: Text to split
            page_num: Page number for source tracking
            filename: Source filename
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        
        # Simple text splitting (could be enhanced with sentence-aware splitting)
        words = text.split()
        
        # Calculate step size to ensure overlap
        step_size = max(1, chunk_size - overlap)
        
        for i in range(0, len(words), step_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if chunk_text.strip():
                chunk = TextChunk(
                    text=chunk_text,
                    filename=filename,
                    page_number=page_num,
                    chunk_index=len(chunks),
                    metadata={
                        "word_count": len(chunk_words),
                        "char_count": len(chunk_text)
                    }
                )
                chunks.append(chunk)
                
        return chunks
    
    def get_document_metadata(self, pdf_path: str) -> DocumentMetadata:
        """
        Extract metadata from PDF document
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            DocumentMetadata object
        """
        filename = os.path.basename(pdf_path)
        file_size = os.path.getsize(pdf_path)
        
        try:
            pdf_reader = PdfReader(pdf_path)
            page_count = len(pdf_reader.pages)
                
        except Exception as e:
            raise ValueError(f"Error reading PDF metadata for {filename}: {str(e)}")
        
        return DocumentMetadata(
            filename=filename,
            page_count=page_count,
            upload_timestamp=datetime.now().isoformat(),
            file_size=file_size
        )
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded file to disk
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            
        Returns:
            Path to saved file
        """
        file_path = os.path.join(self.upload_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
            
        return file_path
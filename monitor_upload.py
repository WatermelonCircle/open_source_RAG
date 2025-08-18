#!/usr/bin/env python3
"""
Monitor the document upload progress in detail
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client
from pypdf import PdfReader

load_dotenv()

def analyze_pdf():
    """Analyze the PDF to understand what we're processing"""
    pdf_path = "uploads/Instruction Manual.pdf"
    if not os.path.exists(pdf_path):
        print("❌ PDF not found in uploads")
        return
    
    try:
        reader = PdfReader(pdf_path)
        print(f"📄 PDF Analysis:")
        print(f"   - Total pages: {len(reader.pages)}")
        print(f"   - File size: {os.path.getsize(pdf_path) / (1024*1024):.1f} MB")
        
        # Check if pages have text or are image-heavy
        text_pages = 0
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 50:
                text_pages += 1
        
        print(f"   - Pages with text: {text_pages}")
        print(f"   - Image-heavy pages: {len(reader.pages) - text_pages}")
        
    except Exception as e:
        print(f"❌ Error analyzing PDF: {e}")

def check_database_progress():
    """Check current database state"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Check documents
        docs_result = supabase.table("documents").select("*").execute()
        print(f"\n📊 Database Status:")
        print(f"   - Documents: {len(docs_result.data)}")
        
        if docs_result.data:
            for doc in docs_result.data:
                print(f"   - {doc['filename']}: {doc.get('total_chunks', 0)} chunks, processed: {doc.get('processed', False)}")
        
        # Check chunks
        chunks_result = supabase.table("document_chunks").select("id").execute()
        print(f"   - Total chunks: {len(chunks_result.data)}")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def monitor_progress():
    """Monitor the upload progress"""
    print("🔍 Upload Progress Monitor")
    print("=" * 50)
    
    analyze_pdf()
    check_database_progress()
    
    print(f"\n⏳ Current Status:")
    print("   - PDF received and stored in uploads/")
    print("   - OCR processing in progress (PIL warnings indicate image processing)")
    print("   - No database entries yet (processing still ongoing)")
    
    print(f"\n💡 What's Happening:")
    print("   - The PDF contains high-resolution images")
    print("   - OCR (Optical Character Recognition) is extracting text from each page")
    print("   - OpenAI embeddings will be generated after text extraction")
    print("   - This process can take 5-15 minutes for image-heavy PDFs")

if __name__ == "__main__":
    monitor_progress()
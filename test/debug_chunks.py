#!/usr/bin/env python3
"""
Debug the chunk creation and conversion process
"""

from app.document_processor import DocumentProcessor

def debug_chunks():
    """Debug chunk creation process"""
    document_processor = DocumentProcessor()
    
    # Process the Quick Start Guide
    print("🔍 Debugging chunk creation process...")
    
    # Extract chunks
    chunks = document_processor.extract_text_from_pdf("Quick Start Guide.pdf")
    print(f"✅ Extracted {len(chunks)} chunks")
    
    # Check first chunk structure
    if chunks:
        first_chunk = chunks[0]
        print(f"📝 First chunk type: {type(first_chunk)}")
        print(f"📝 First chunk: {first_chunk}")
        
        # Convert to dict
        chunk_dict = first_chunk.dict()
        print(f"📝 Converted dict type: {type(chunk_dict)}")
        print(f"📝 Converted dict: {chunk_dict}")
        
        # Check if we can access 'text' field
        print(f"📝 Text field accessible: {chunk_dict.get('text', 'NOT_FOUND')[:100]}...")
    
    print("\n✅ Debug complete!")

if __name__ == "__main__":
    debug_chunks()
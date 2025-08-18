"""
FastAPI Routes for RAG Webapp

This module contains all the API endpoints:
1. File upload endpoint for PDFs
2. Chat endpoint for document questions
3. Document management endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
from datetime import datetime
from .document_processor import DocumentProcessor
from .supabase_vector_store import vector_store
from .claude_service import ClaudeService
from .models import ChatMessage, ChatResponse, SessionRequest, SessionResponse
from .config import settings
from .conversation_memory import conversation_memory

router = APIRouter()
document_processor = DocumentProcessor()
# vector_store is imported from supabase_vector_store

# Initialize Claude service lazily to handle missing API keys in tests
claude_service = None

def get_claude_service():
    global claude_service
    if claude_service is None:
        claude_service = ClaudeService()
    return claude_service

@router.post("/session", response_model=SessionResponse)
async def create_session(request: SessionRequest = SessionRequest()):
    """
    Create a new conversation session
    
    Returns:
        Session ID and creation timestamp
    """
    session_id = conversation_memory.create_session()
    
    return SessionResponse(
        session_id=session_id,
        created_at=datetime.now().isoformat()
    )

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload PDF files and process them for RAG
    
    Args:
        files: List of uploaded PDF files
        
    Returns:
        Success status with processed file information
    """
    # Check if admin mode is enabled
    if not settings.ADMIN_MODE:
        raise HTTPException(
            status_code=403, 
            detail="Upload functionality is disabled. This app is in user mode."
        )
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    processed_files = []
    failed_files = []
    
    for file in files:
        try:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                failed_files.append(f"{file.filename}: Not a PDF file")
                continue
            
            # Check file size
            content = await file.read()
            if len(content) > settings.MAX_FILE_SIZE:
                failed_files.append(f"{file.filename}: File too large")
                continue
            
            # Save file and process
            file_path = document_processor.save_uploaded_file(content, file.filename)
            
            # Extract text and metadata
            metadata = document_processor.get_document_metadata(file_path)
            chunks = document_processor.extract_text_from_pdf(file_path)
            
            # Convert TextChunk objects to dictionaries for vector store
            chunks_dict = [chunk.dict() for chunk in chunks]
            
            # Debug: Check conversion
            print(f"🔍 Route debug: chunks type={type(chunks)}, chunks_dict type={type(chunks_dict)}")
            if chunks_dict:
                print(f"🔍 First dict: {type(chunks_dict[0])}, keys={list(chunks_dict[0].keys())}")
            
            # Store in vector database
            result = vector_store.add_documents(chunks_dict, file.filename)
            chunks_added = result.get('chunks_added', 0)
            
            processed_files.append({
                "filename": file.filename,
                "page_count": metadata.page_count,
                "chunks_created": len(chunks),
                "chunks_stored": chunks_added,
                "file_size": metadata.file_size
            })
            
        except Exception as e:
            failed_files.append(f"{file.filename}: {str(e)}")
    
    return {
        "success": len(processed_files) > 0,
        "files_processed": len(processed_files),
        "processed_files": processed_files,
        "failed_files": failed_files,
        "filenames": [f["filename"] for f in processed_files]
    }

@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(message: ChatMessage):
    """
    Chat with uploaded documents using RAG with conversation memory
    
    Args:
        message: User's chat message with optional session_id
        
    Returns:
        AI response with source citations and session_id
    """
    try:
        # Check if we have any documents in the vector store
        chunk_count = vector_store.get_chunk_count()
        if chunk_count == 0:
            return ChatResponse(
                response="I'd be happy to help you! However, I don't currently have access to the product information needed to answer your question. Please contact our technical support team or check if the product documentation has been properly loaded.",
                sources=[],
                timestamp=datetime.now().isoformat(),
                session_id=message.session_id
            )
        
        # Create new session if none provided
        session_id = message.session_id
        if not session_id:
            session_id = conversation_memory.create_session()
        
        # Get conversation history for context
        conversation_history = conversation_memory.get_conversation_context(session_id, max_turns=5)
        
        # Retrieve relevant documents using vector similarity
        relevant_docs = vector_store.similarity_search(message.message, top_k=5, threshold=0.1)
        
        # Generate response using Claude with RAG context and conversation history
        claude = get_claude_service()
        response = claude.generate_rag_response(
            message.message, 
            relevant_docs, 
            conversation_history
        )
        
        # Add this conversation turn to memory
        conversation_memory.add_conversation_turn(
            session_id=session_id,
            user_message=message.message,
            assistant_response=response.response,
            sources=response.sources
        )
        
        # Include session_id in response
        response.session_id = session_id
        
        return response
        
    except Exception as e:
        return ChatResponse(
            response=f"Sorry, I encountered an error processing your question: {str(e)}",
            sources=[],
            timestamp=datetime.now().isoformat(),
            session_id=message.session_id
        )

@router.get("/documents")
async def list_documents():
    """
    List all uploaded documents
    
    Returns:
        List of uploaded document metadata
    """
    upload_dir = settings.UPLOAD_DIR
    
    if not os.path.exists(upload_dir):
        return {"documents": []}
    
    documents = []
    for filename in os.listdir(upload_dir):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(upload_dir, filename)
            try:
                metadata = document_processor.get_document_metadata(file_path)
                documents.append(metadata.model_dump())
            except Exception as e:
                # Skip files that can't be processed
                continue
    
    return {"documents": documents}
"""
FastAPI Routes for RAG Webapp

This module contains all the API endpoints:
1. File upload endpoint for PDFs
2. Chat endpoint for document questions
3. Document management endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from typing import List
import os
import json
from datetime import datetime
from .document_processor import DocumentProcessor
from .supabase_vector_store import vector_store
from .claude_service import ClaudeService
from .models import ChatMessage, ChatResponse, SessionRequest, SessionResponse
from .config import settings
from .conversation_memory import conversation_memory
from .time_service import beijing_time_service
from .email_service import email_service
from .websocket_manager import live_chat_manager, UserType
import re

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

# Session state manager for email collection
email_collection_states = {}  # session_id -> {"awaiting_email": bool, "reason": str}

def is_valid_email(email: str) -> bool:
    """Check if the provided string is a valid email address"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email.strip()) is not None

def set_email_collection_state(session_id: str, reason: str = "low_confidence"):
    """Mark a session as awaiting email collection"""
    email_collection_states[session_id] = {
        "awaiting_email": True,
        "reason": reason
    }

def clear_email_collection_state(session_id: str):
    """Clear email collection state for a session"""
    if session_id in email_collection_states:
        del email_collection_states[session_id]

def is_awaiting_email(session_id: str) -> bool:
    """Check if a session is awaiting email input"""
    return email_collection_states.get(session_id, {}).get("awaiting_email", False)

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

@router.post("/chat/image")
async def chat_with_image(image: UploadFile = File(...), session_id: str = None):
    """
    Chat with an uploaded image using Claude's vision capabilities
    
    Args:
        image: Uploaded image file
        session_id: Optional session ID for conversation context
        
    Returns:
        AI response analyzing the image
    """
    try:
        # Validate image file
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image content
        image_content = await image.read()
        
        # Validate file size (5MB max)
        if len(image_content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image file too large (max 5MB)")
        
        # Create session if none provided
        if not session_id:
            session_id = conversation_memory.create_session()
        
        # Get conversation history for context
        conversation_history = conversation_memory.get_conversation_context(session_id, max_turns=5)
        
        # Convert image to base64 for Claude API
        import base64
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        # Create prompt for image analysis
        prompt = f"""You are a professional customer support representative helping customers with their product questions and concerns.

{f"PREVIOUS CONVERSATION:{conversation_history}" if conversation_history.strip() else ""}

The customer has shared an image in response to your conversation. This image may be providing information you requested (like a photo of a product issue, model number, etc.). Please analyze the image and provide helpful assistance. Follow these guidelines:

RESPONSE FORMAT:
1. Keep responses brief and focused - aim for 2-3 sentences max unless providing steps
2. When giving instructions, use clear numbered steps (1., 2., 3.)
3. Break complex solutions into simple, actionable steps
4. Prioritize the most important information first
5. End with a specific next action or follow-up question

FORMATTING GUIDELINES:
6. Use **bold text** for important actions, warnings, or key points
7. Use bullet points (•) for lists of items or quick checks
8. Use line breaks to separate different topics or sections
9. Emphasize critical steps that customers must not miss
10. Make responses visually scannable with proper formatting

COMMUNICATION STYLE:
11. Be friendly, professional, and empathetic
12. Answer directly and confidently based on what you can see in the image
13. Focus on solving the customer's problem quickly
14. Use natural, conversational language
15. Never mention "documents," "context," or "sources" in your response
16. Start responses with helpful phrases like "I can see in your image..." or "Looking at your photo..."
17. **IMPORTANT**: If you previously asked for a photo and the customer has now provided one, acknowledge this and proceed with the next steps rather than asking for more photos

Please analyze this image and provide helpful customer support assistance:"""

        # Call Claude API with vision
        claude = get_claude_service()
        response = claude.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image.content_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
        )
        
        response_text = response.content[0].text
        
        # Store conversation turn
        conversation_memory.add_conversation_turn(
            session_id=session_id,
            user_message=f"[Image uploaded: {image.filename}]",
            assistant_response=response_text,
            sources=[]
        )
        
        return {
            "response": response_text,
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "response": f"Sorry, I encountered an error processing your image: {str(e)}",
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }

@router.post("/chat/combined")
async def chat_with_text_and_image(
    image: UploadFile = File(None), 
    message: str = None,
    session_id: str = None
):
    """
    Chat with both text message and image combined
    
    Args:
        image: Optional uploaded image file
        message: Optional text message
        session_id: Optional session ID for conversation context
        
    Returns:
        AI response analyzing both text and image with conversation context
    """
    try:
        # Must have either text or image
        if not message and not image:
            raise HTTPException(status_code=400, detail="Must provide either message or image")
        
        # Create session if none provided
        if not session_id:
            session_id = conversation_memory.create_session()
        
        # Get conversation history for context
        conversation_history = conversation_memory.get_conversation_context(session_id, max_turns=5)
        
        # Build user message description for storage
        user_message_parts = []
        if message:
            user_message_parts.append(message)
        if image:
            user_message_parts.append(f"[Image: {image.filename}]")
        user_message_text = " ".join(user_message_parts)
        
        # Handle text + image combination
        image_data = None
        if image:
            # Validate image
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            image_content = await image.read()
            if len(image_content) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Image file too large (max 5MB)")
            
            # Store image data for future escalation (don't process with Claude Vision)
            import base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            image_data = {
                "filename": image.filename,
                "content_type": image.content_type,
                "base64_data": image_base64
            }
        
        # Use regular RAG flow for text message (ignore image for AI processing)
        if message:
            # Check if message contains email address and auto-escalate if image was previously uploaded
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, message)
            
            # Check if this session has any images from conversation history
            conversation_history_full = conversation_memory.get_full_conversation_history(session_id)
            has_images = any(turn.get('image_data') for turn in conversation_history_full)
            
            if email_matches and has_images:
                # Auto-escalate: send email report immediately
                customer_email = email_matches[0]  # Use first email found
                
                # Extract order number if mentioned
                order_pattern = r'\b(?:order|order number|reference|ref)[\s:]*([A-Za-z0-9\-]+)\b'
                order_matches = re.findall(order_pattern, message, re.IGNORECASE)
                order_id = order_matches[0] if order_matches else ""
                
                # Send support request
                from .email_service import email_service
                result = email_service.send_support_request(
                    customer_email=customer_email,
                    order_id=order_id,
                    conversation_history=conversation_history_full,
                    additional_notes="Customer uploaded image and provided contact information"
                )
                
                if result.get("success"):
                    response_text = f"✅ **EMAIL SENT TO SUPPORT TEAM!**\n\nPerfect! I've immediately forwarded your request along with your image to our support team at **{customer_email}**.\n\n🎯 **Your support request has been submitted successfully!**\n\n• **Reference ID**: {result.get('reference_id', 'N/A')}\n• **Email sent to**: {customer_email}\n• **Response time**: Within 4 hours maximum\n• **What's included**: Your uploaded image and full conversation history\n\n📧 **Our support team has received your email and will review your case personally.** They'll get back to you soon!\n\nIs there anything else I can help you with in the meantime?"
                else:
                    response_text = f"Thank you for providing your email address! I've noted your contact information, but there was an issue submitting your request. Please try again or contact our support team directly."
            else:
                # Regular RAG response
                relevant_docs = vector_store.similarity_search(message, top_k=5, threshold=0.1)
                
                claude = get_claude_service()
                response = claude.generate_rag_response(
                    message, 
                    relevant_docs, 
                    conversation_history
                )
                response_text = response.response
        else:
            # If only image was provided, ask for email and offer support
            response_text = "Thank you for sharing the image! I've saved it for our support team to review. \n\n**To get you the best assistance, please provide your email address and briefly describe what you need help with.** Our support team will review your image and respond within 4 hours."
        
        # Store conversation turn (including image data for future escalation)
        stored = conversation_memory.add_conversation_turn(
            session_id=session_id,
            user_message=user_message_text,
            assistant_response=response_text,
            sources=[],
            image_data=image_data
        )
        
        return {
            "response": response_text,
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "response": f"Sorry, I encountered an error: {str(e)}",
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
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
                response="I'd be happy to help you! However, I don't currently have access to the product information needed to answer your question. Please contact our support manager or check if the product documentation has been properly loaded.",
                sources=[],
                timestamp=datetime.now().isoformat(),
                session_id=message.session_id
            )
        
        # Create new session if none provided
        session_id = message.session_id
        if not session_id:
            session_id = conversation_memory.create_session()
        
        # Check if we're awaiting email input from this session
        if is_awaiting_email(session_id):
            # Check if the message contains a valid email address
            email_match = re.search(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', message.message)
            
            if email_match:
                customer_email = email_match.group().strip()
                
                # Get full conversation history for email report
                full_conversation = conversation_memory.get_full_conversation_history(session_id)
                
                # Send email report
                email_result = email_service.send_support_request(
                    customer_email=customer_email,
                    conversation_history=full_conversation,
                    additional_notes="Customer provided email after FAQ chat couldn't provide sufficient help"
                )
                
                # Clear email collection state
                clear_email_collection_state(session_id)
                
                # Return success response
                if email_result.get("success"):
                    response_text = f"""✅ **Perfect! Your support request has been sent.**

• **Email report sent to:** our support manager
• **Your email:** {customer_email}
• **Response time:** {email_result.get('estimated_response_time', '4 hours')}
• **Reference ID:** {email_result.get('reference_id', 'Generated')}

Our support manager will review your entire conversation and get back to you with personalized assistance. Thank you for using our support service!"""
                else:
                    response_text = f"❌ There was an issue sending your support request: {email_result.get('message', 'Unknown error')}. Please try again."
                
                # Store this final interaction
                conversation_memory.add_conversation_turn(
                    session_id=session_id,
                    user_message=message.message,
                    assistant_response=response_text,
                    sources=[]
                )
                
                return ChatResponse(
                    response=response_text,
                    sources=[],
                    timestamp=datetime.now().isoformat(),
                    session_id=session_id
                )
            else:
                # No valid email found, ask again
                return ChatResponse(
                    response="I don't see a valid email address in your message. Please provide your email address (like example@domain.com) so I can send your conversation to our support manager.",
                    sources=[],
                    timestamp=datetime.now().isoformat(),
                    session_id=session_id,
                    requires_email=True
                )
        
        # Normal chat flow continues...
        # Get conversation history for context
        conversation_history = conversation_memory.get_conversation_context(session_id, max_turns=5)
        
        # Get current support status for proper escalation guidance
        support_status = beijing_time_service.get_business_status()
        
        # Retrieve relevant documents using vector similarity
        relevant_docs = vector_store.similarity_search(message.message, top_k=5, threshold=0.1)
        
        # Generate response using Claude with RAG context and conversation history
        claude = get_claude_service()
        response = claude.generate_rag_response(
            message.message, 
            relevant_docs, 
            conversation_history,
            support_status
        )
        
        # Check if Claude indicated email collection is needed
        if response.requires_email:
            set_email_collection_state(session_id, "low_confidence")
        
        # Add this conversation turn to memory
        stored = conversation_memory.add_conversation_turn(
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

@router.get("/support/business-hours")
async def get_business_hours_status():
    """
    Get current business hours status for live support
    
    Returns:
        Business hours status with Beijing time information
    """
    try:
        status = beijing_time_service.get_business_status()
        return {
            "success": True,
            **status
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "is_online": False,
            "status_message": "Unable to determine support availability"
        }

@router.post("/support/email-report")
async def submit_email_report(request: dict):
    """
    Submit email report to human support team
    
    Args:
        request: Dictionary containing customer_email, order_id, session_id, and additional_notes
        
    Returns:
        Email submission result
    """
    try:
        # Extract request data
        customer_email = request.get("customer_email")
        order_id = request.get("order_id", "")
        session_id = request.get("session_id")
        additional_notes = request.get("additional_notes", "")
        
        # Get conversation history
        if session_id:
            conversation_history = conversation_memory.get_full_conversation_history(session_id)
        else:
            conversation_history = []
        
        # Send email report
        result = email_service.send_support_request(
            customer_email=customer_email,
            order_id=order_id,
            conversation_history=conversation_history,
            additional_notes=additional_notes
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to submit email report: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# WebSocket endpoints for live chat
@router.websocket("/ws/customer")
async def websocket_customer_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for customers to connect to live chat
    """
    connection_id = None
    try:
        # Connect customer
        connection_id = await live_chat_manager.connect_user(websocket, UserType.CUSTOMER)
        
        while True:
            # Receive message from customer
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "chat_message")
            
            if message_type == "chat_message":
                content = message_data.get("content", "")
                if content.strip():
                    await live_chat_manager.send_message(connection_id, content)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Customer WebSocket error: {e}")
    finally:
        if connection_id:
            await live_chat_manager.disconnect_user(connection_id)

@router.websocket("/ws/agent/{agent_id}")
async def websocket_agent_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for agents to connect to live chat
    """
    connection_id = None
    try:
        # Connect agent
        connection_id = await live_chat_manager.connect_user(websocket, UserType.AGENT, agent_id)
        
        while True:
            # Receive message from agent
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "chat_message")
            
            if message_type == "chat_message":
                content = message_data.get("content", "")
                if content.strip():
                    await live_chat_manager.send_message(connection_id, content)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Agent WebSocket error: {e}")
    finally:
        if connection_id:
            await live_chat_manager.disconnect_user(connection_id)

@router.get("/support/live-chat/stats")
async def get_live_chat_stats():
    """
    Get live chat system statistics
    """
    try:
        stats = live_chat_manager.get_stats()
        return {
            "success": True,
            **stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
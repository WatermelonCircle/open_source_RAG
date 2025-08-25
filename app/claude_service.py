"""
Claude AI Service for RAG Chat

This module handles:
1. Claude API integration for chat responses
2. Prompt engineering for RAG with source citations
3. Context management for document-based conversations

The service combines retrieved document chunks with user queries
to generate contextual responses with proper source citations.
"""

import anthropic
from typing import List, Dict, Any
from datetime import datetime
from .config import settings
from .models import ChatResponse

class ClaudeService:
    """Handles Claude AI integration for RAG chat responses"""
    
    def __init__(self):
        if not settings.CLAUDE_API_KEY:
            raise ValueError("Claude API key is required. Set CLAUDE_API_KEY environment variable.")
        
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        print("Initialized Claude AI service")
    
    def generate_rag_response(
        self, 
        query: str, 
        context_docs: List[Dict[str, Any]], 
        conversation_history: str = "",
        support_status: Dict[str, Any] = None,
        max_similarity_threshold: float = 0.3
    ) -> ChatResponse:
        """
        Generate a response using Claude with RAG context
        
        Args:
            query: User's question
            context_docs: Retrieved document chunks with metadata
            conversation_history: Previous conversation context
            support_status: Current live support availability status
            
        Returns:
            ChatResponse with answer and source citations
        """
        # Check if we have documents and their relevance
        if not context_docs:
            return self._generate_email_collection_response("no_docs_available", conversation_history)
            
        # Check if this is a simple confirmation/follow-up response
        query_lower = query.lower().strip()
        confirmation_words = ['yes', 'okay', 'ok', 'sure', 'please', 'go ahead', 'proceed', 'continue', 'confirm']
        
        if any(word in query_lower for word in confirmation_words) and len(query.split()) <= 3:
            # This is likely a confirmation - proceed with normal RAG response regardless of confidence
            pass
        else:
            # Check confidence level based on similarity scores for substantive queries
            max_similarity = max((doc.get("similarity_score", 0.0) for doc in context_docs), default=0.0)
            is_low_confidence = max_similarity < max_similarity_threshold
            
            if is_low_confidence:
                return self._generate_email_collection_response("low_confidence", conversation_history)
        
        # Build context from retrieved documents
        context_text = self._build_context(context_docs)
        
        # Create the prompt with conversation history and support status
        prompt = self._create_rag_prompt(query, context_text, conversation_history, support_status)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Format sources for citation
            sources = self._format_sources(context_docs)
            
            return ChatResponse(
                response=response_text,
                sources=sources,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return ChatResponse(
                response=f"Sorry, I encountered an error while generating a response: {str(e)}",
                sources=[],
                timestamp=datetime.now().isoformat()
            )
    
    def _build_context(self, context_docs: List[Dict[str, Any]]) -> str:
        """
        Build context text from retrieved document chunks
        
        Args:
            context_docs: List of document chunks with metadata
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(context_docs, 1):
            filename = doc.get("filename", "Unknown")
            page_num = doc.get("page_number", "Unknown")
            text = doc.get("text", "")
            
            context_part = f"Document {i} (Source: {filename}, Page {page_num}):\n{text}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _create_rag_prompt(self, query: str, context: str, conversation_history: str = "", support_status: Dict[str, Any] = None) -> str:
        """
        Create a RAG prompt for Claude
        
        Args:
            query: User's question
            context: Context from retrieved documents
            conversation_history: Previous conversation context
            support_status: Current live support availability status
            
        Returns:
            Formatted prompt string
        """
        # Build conversation history section
        history_section = ""
        if conversation_history.strip():
            history_section = f"""
PREVIOUS CONVERSATION:
{conversation_history}

"""

        # Build dynamic escalation guidance based on current support status
        escalation_guidance = self._build_escalation_guidance(support_status)

        prompt = f"""You are a professional customer support representative helping customers with their product questions and concerns. Your goal is to provide helpful, accurate, and friendly assistance.

PRODUCT INFORMATION:
{context}
{history_section}CURRENT CUSTOMER QUESTION: {query}

Please respond as a knowledgeable customer support agent. Follow these guidelines:

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
12. Answer directly and confidently using the product information available
13. Focus on solving the customer's problem quickly
14. Use natural, conversational language
15. Never mention "documents," "context," or "sources" in your response
16. Start responses with helpful phrases like "I'll help you with that!" or "Let's get this fixed!"
17. Reference previous conversation naturally when relevant (e.g., "As we discussed..." or "Following up...")
18. **IMPORTANT**: If the previous conversation shows the customer uploaded an image, acknowledge this and don't ask for photos again. Say things like "I can see from the image you shared..." or "Based on the photo you provided..."

{escalation_guidance}

RESPONSE:"""
        
        return prompt
    
    def _format_sources(self, context_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format source citations for the response
        
        Args:
            context_docs: Document chunks used in the response
            
        Returns:
            List of formatted source citations
        """
        sources = []
        seen_sources = set()  # To avoid duplicate citations
        
        for doc in context_docs:
            filename = doc.get("filename", "Unknown")
            page_num = doc.get("page_number", "Unknown")
            
            # Create a unique identifier for this source
            source_id = f"{filename}_{page_num}"
            
            if source_id not in seen_sources:
                sources.append({
                    "filename": filename,
                    "page": page_num,
                    "similarity_score": doc.get("similarity_score", 0.0)
                })
                seen_sources.add(source_id)
        
        return sources
    
    def _generate_email_collection_response(self, reason: str, conversation_history: str = "") -> ChatResponse:
        """
        Generate a dynamic response using Claude AI that asks for email to escalate to human support
        
        Args:
            reason: Reason for email collection ("no_docs_available" or "low_confidence")
            conversation_history: Previous conversation context for natural flow
            
        Returns:
            ChatResponse requesting email for support escalation
        """
        # Create instruction prompt for escalation
        if reason == "no_docs_available":
            situation_context = "I don't have access to the specific product information needed to answer the customer's question accurately."
        else:  # low_confidence
            situation_context = "I have some information but want to ensure the customer gets the most accurate and helpful answer possible."
        
        # Build conversation history section
        history_section = ""
        if conversation_history.strip():
            history_section = f"""
PREVIOUS CONVERSATION:
{conversation_history}

"""

        escalation_prompt = f"""You are a professional customer support representative. {situation_context}

{history_section}Based on this conversation context, please guide the customer to provide their email address and any order ID number so they can get proper support through email from our support manager.

REQUIREMENTS:
- Be natural, friendly, and conversational
- Reference the conversation naturally if there's history
- Request email address for support manager escalation
- Mention 4-hour response time commitment
- Use "support manager" (never "human support team" or "robot")
- Keep response brief (2-3 sentences max)
- Use **bold** for key actions like connecting with support manager
- Make it feel like a natural conversation flow, not a template

Generate a response that guides the customer to provide their email for escalation:"""

        try:
            # Use Claude to generate natural escalation response
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.3,  # Slightly higher temperature for natural variation
                messages=[
                    {
                        "role": "user",
                        "content": escalation_prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            
        except Exception as e:
            # Fallback response if Claude call fails
            response_text = """I'd be happy to help you! To make sure you get the most accurate assistance, **let me connect you with our support manager**.

Please share your email address in your next message, and I'll send them our conversation. They'll get back to you within 4 hours with personalized help."""
        
        return ChatResponse(
            response=response_text,
            sources=[],
            timestamp=datetime.now().isoformat(),
            requires_email=True  # Flag to indicate email collection is needed
        )
    
    def generate_simple_response(self, query: str) -> str:
        """
        Generate a simple Claude response without RAG context
        
        Args:
            query: User's question
            
        Returns:
            Simple response string
        """
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _build_escalation_guidance(self, support_status: Dict[str, Any] = None) -> str:
        """
        Build escalation guidance for email support only (no live support in this version)
        
        Args:
            support_status: Not used in this version - kept for compatibility
            
        Returns:
            Formatted escalation guidance string
        """
        # Only email support available in this version
        return """ESCALATION GUIDANCE - CRITICAL REQUIREMENTS:
18. **ABSOLUTELY NEVER** provide ANY external contact methods including:
    - Email addresses (especially support@gavasto.com)
    - Facebook Messenger links or external websites
    - Phone numbers or other external contact methods
19. **ONLY** use the integrated support system built into this interface
20. **EMAIL SUPPORT ONLY** - When customers need human support:
    - **FIRST**: Try to resolve with available product information
    - **IF STILL UNRESOLVED**: The system will automatically prompt for email collection within the chat
21. **MANDATORY**: Email collection happens seamlessly within this chat interface
22. **NEVER** direct customers to external email sections - the chat itself handles email collection

CRITICAL: This version only supports email escalation. Email collection will be handled automatically by the chat system when needed."""
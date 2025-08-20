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
        support_status: Dict[str, Any] = None
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
        if not context_docs:
            return ChatResponse(
                response="I'd be happy to help you! However, I don't currently have access to the product information needed to answer your question. Please contact our technical support team or check if the product documentation has been properly loaded.",
                sources=[],
                timestamp=datetime.now().isoformat()
            )
        
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
        Build dynamic escalation guidance based on current support status
        
        Args:
            support_status: Current live support availability status
            
        Returns:
            Formatted escalation guidance string
        """
        if not support_status:
            # Default to email support if status is unavailable
            support_status = {"is_online": False}
        
        is_online = support_status.get("is_online", False)
        
        if is_online:
            # Support is online - direct to live chat
            return """ESCALATION GUIDANCE - CRITICAL REQUIREMENTS:
18. **ABSOLUTELY NEVER** provide ANY external contact methods including:
    - Email addresses (especially support@Gavasto.com)
    - Facebook Messenger links (m.me/Gavasto)
    - External websites (www.Gavasto.com)
    - Phone numbers or other external contact methods
19. **ONLY** use the integrated support system built into this interface
20. **CURRENT STATUS: LIVE SUPPORT IS ONLINE** - When customers need human support:
    - **ALWAYS direct them to**: "Please click the 'Online Support' button above to connect with a live agent immediately"
    - **NEVER mention email support** when live agents are available
21. **MANDATORY**: Always phrase escalation as directing customers to use the interface elements visible on their current page
22. Make escalation feel seamless by referring to "the button above" rather than external services

CRITICAL: Live support is currently ONLINE. Use ONLY the Online Support button for escalation."""
        else:
            # Support is offline - direct to email
            return """ESCALATION GUIDANCE - CRITICAL REQUIREMENTS:
18. **ABSOLUTELY NEVER** provide ANY external contact methods including:
    - Email addresses (especially support@Gavasto.com)
    - Facebook Messenger links (m.me/Gavasto)
    - External websites (www.Gavasto.com)
    - Phone numbers or other external contact methods
19. **ONLY** use the integrated support system built into this interface
20. **CURRENT STATUS: LIVE SUPPORT IS OFFLINE** - When customers need human support:
    - **ALWAYS direct them to**: "Please enter your email in the 'Email Report' section below, and our support team will contact you within 4 hours"
    - **NEVER mention Online Support button** when live agents are offline
21. **MANDATORY**: Always phrase escalation as directing customers to use the interface elements visible on their current page
22. Make escalation feel seamless by referring to "the section below" rather than external services

CRITICAL: Live support is currently OFFLINE. Use ONLY the Email Report section for escalation."""
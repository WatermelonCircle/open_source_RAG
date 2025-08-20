"""
Escalation Service for Human Support Routing

This module handles:
1. Query satisfaction evaluation using Claude
2. Detection of explicit human support requests
3. Confidence scoring for escalation decisions

The service determines whether a RAG response satisfies the user's query
and whether the user should be escalated to human support.
"""

import anthropic
from typing import Dict, List, Any
from datetime import datetime
from .config import settings

class EscalationService:
    """Evaluates whether queries need human support escalation"""
    
    def __init__(self):
        if not settings.CLAUDE_API_KEY:
            raise ValueError("Claude API key is required for escalation service")
        
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        print("🔄 Initialized escalation evaluation service")
    
    def evaluate_query_satisfaction(
        self, 
        user_query: str, 
        rag_response: str, 
        retrieved_sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate whether the RAG response satisfies the user's query
        
        Args:
            user_query: Original user question
            rag_response: Generated RAG response
            retrieved_sources: Documents used to generate response
            
        Returns:
            Dictionary with satisfaction assessment and escalation recommendation
        """
        # Use LLM for both explicit request detection AND satisfaction evaluation in one call
        
        # Evaluate satisfaction using Claude
        evaluation_prompt = self._create_evaluation_prompt(
            user_query, rag_response, retrieved_sources
        )
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=400,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": evaluation_prompt
                    }
                ]
            )
            
            # Parse Claude's evaluation
            evaluation_text = response.content[0].text
            return self._parse_evaluation_response(evaluation_text)
            
        except Exception as e:
            print(f"❌ Error in satisfaction evaluation: {e}")
            # Default to no escalation on error
            return {
                'needs_escalation': False,
                'confidence': 0.5,
                'reason': 'evaluation_error',
                'explanation': f"Could not evaluate satisfaction: {str(e)}",
                'satisfaction_score': 0.5
            }
    
    def _detect_explicit_human_request(self, user_query: str) -> Dict[str, Any]:
        """
        Use Claude to detect if user explicitly requests human support
        
        Args:
            user_query: User's question
            
        Returns:
            Dictionary with detection results
        """
        detection_prompt = f"""You are an expert at detecting customer intent. Analyze this user message to determine if they are explicitly requesting to speak with a human representative, customer support agent, or be transferred to human assistance.

USER MESSAGE: "{user_query}"

EXPLICIT HUMAN REQUEST INDICATORS:
- Direct requests to talk/speak to humans, agents, or representatives
- Requests to be connected/transferred to customer support
- Requests for live chat or human assistance
- Expressions of wanting to speak with "someone" or "a person"
- Frustration leading to human escalation requests

NOT EXPLICIT REQUESTS:
- Questions about how to contact support (informational)
- Questions about support hours or processes
- General product/technical questions
- Mentions of humans/support without requesting connection

RESPONSE FORMAT:
IS_EXPLICIT: [true/false]
CONFIDENCE: [0.0-1.0]
EXPLANATION: [Brief explanation of your decision]

Be accurate - only return true if the user is clearly asking to be connected to human support."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": detection_prompt
                    }
                ]
            )
            
            # Parse Claude's response
            response_text = response.content[0].text
            return self._parse_detection_response(response_text)
            
        except Exception as e:
            print(f"❌ Error in human request detection: {e}")
            # Conservative fallback - assume no explicit request on error
            return {
                'is_explicit': False,
                'explanation': f"Could not detect intent due to error: {str(e)}"
            }
    
    def _parse_detection_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Claude's explicit request detection response
        
        Args:
            response_text: Raw response from Claude
            
        Returns:
            Structured detection results
        """
        try:
            lines = response_text.strip().split('\n')
            result = {
                'is_explicit': False,
                'explanation': 'Could not parse detection response'
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('IS_EXPLICIT:'):
                    explicit_str = line.split(':', 1)[1].strip().lower()
                    result['is_explicit'] = explicit_str in ['true', 'yes', '1']
                    
                elif line.startswith('EXPLANATION:'):
                    result['explanation'] = line.split(':', 1)[1].strip()
            
            return result
            
        except Exception as e:
            print(f"❌ Error parsing detection response: {e}")
            return {
                'is_explicit': False,
                'explanation': f"Could not parse detection: {str(e)}"
            }
    
    def _create_evaluation_prompt(
        self, 
        user_query: str, 
        rag_response: str, 
        retrieved_sources: List[Dict[str, Any]]
    ) -> str:
        """
        Create prompt for Claude to evaluate query satisfaction
        
        Args:
            user_query: User's original question
            rag_response: Generated response
            retrieved_sources: Source documents used
            
        Returns:
            Formatted evaluation prompt
        """
        sources_info = ""
        if retrieved_sources:
            sources_info = f"\n\nSOURCE DOCUMENTS USED:\n"
            for i, source in enumerate(retrieved_sources[:3], 1):
                filename = source.get('filename', 'Unknown')
                page = source.get('page', 'Unknown')
                similarity = source.get('similarity_score', 0.0)
                sources_info += f"{i}. {filename} (Page {page}) - Relevance: {similarity:.2f}\n"
        else:
            sources_info = "\n\nSOURCE DOCUMENTS USED: None (no relevant documents found)"
        
        prompt = f"""You are an expert customer service quality assessor. Your job is to:
1. First check if the user is explicitly requesting human support
2. Then evaluate whether the RAG response satisfies their query

USER'S ORIGINAL QUERY:
{user_query}

RAG SYSTEM RESPONSE:
{rag_response}{sources_info}

STEP 1 - EXPLICIT HUMAN REQUEST CHECK:
First determine if the user is explicitly asking for human support, such as:
- "I want to talk to a human/agent/representative"
- "Connect me to customer support"
- "Can I speak with someone?"
- "Transfer me to a person"

If YES: Immediately escalate regardless of RAG response quality.
If NO: Proceed to satisfaction evaluation.

STEP 2 - SATISFACTION EVALUATION:
Assess the RAG response on these dimensions:
1. **Completeness**: Does the response fully address the user's question?
2. **Accuracy**: Is the information provided correct and reliable?
3. **Relevance**: Does the response directly relate to what was asked?
4. **Actionability**: Can the user take clear next steps based on the response?
5. **Source Quality**: Are the retrieved documents relevant and sufficient?

ESCALATION INDICATORS:
The user should be escalated to human support if:
- They explicitly requested human support (Step 1)
- The response is incomplete or doesn't answer the core question
- The response is vague, generic, or unhelpful
- The user's query requires personalized help or account-specific information
- The response lacks actionable steps for complex problems
- No relevant source documents were found (similarity scores very low)
- The query involves complaints, refunds, or sensitive issues

RESPONSE FORMAT:
Provide your assessment in this exact format:

EXPLICIT_HUMAN_REQUEST: [true/false]
SATISFACTION_SCORE: [0.0-1.0, where 1.0 = completely satisfied]
NEEDS_ESCALATION: [true/false]
CONFIDENCE: [0.0-1.0, how confident you are in this assessment]
REASON: [brief reason code: explicit_human_request, adequate_response, incomplete_answer, no_relevant_sources, complex_issue, vague_response, or personalized_help_needed]
EXPLANATION: [2-3 sentence explanation of your decision]

Be strict in your evaluation - err on the side of escalation if there's any doubt about user satisfaction."""

        return prompt
    
    def _parse_evaluation_response(self, evaluation_text: str) -> Dict[str, Any]:
        """
        Parse Claude's evaluation response into structured data
        
        Args:
            evaluation_text: Raw response from Claude
            
        Returns:
            Structured evaluation results
        """
        try:
            lines = evaluation_text.strip().split('\n')
            result = {
                'satisfaction_score': 0.5,
                'needs_escalation': False,
                'confidence': 0.5,
                'reason': 'parsing_error',
                'explanation': 'Could not parse evaluation response'
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('EXPLICIT_HUMAN_REQUEST:'):
                    explicit_str = line.split(':', 1)[1].strip().lower()
                    result['explicit_human_request'] = explicit_str in ['true', 'yes', '1']
                    
                elif line.startswith('SATISFACTION_SCORE:'):
                    try:
                        score = float(line.split(':', 1)[1].strip())
                        result['satisfaction_score'] = max(0.0, min(1.0, score))
                    except:
                        pass
                        
                elif line.startswith('NEEDS_ESCALATION:'):
                    escalation_str = line.split(':', 1)[1].strip().lower()
                    result['needs_escalation'] = escalation_str in ['true', 'yes', '1']
                    
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                        result['confidence'] = max(0.0, min(1.0, confidence))
                    except:
                        pass
                        
                elif line.startswith('REASON:'):
                    result['reason'] = line.split(':', 1)[1].strip()
                    
                elif line.startswith('EXPLANATION:'):
                    result['explanation'] = line.split(':', 1)[1].strip()
            
            return result
            
        except Exception as e:
            print(f"❌ Error parsing evaluation response: {e}")
            return {
                'satisfaction_score': 0.5,
                'needs_escalation': False,
                'confidence': 0.3,
                'reason': 'parsing_error',
                'explanation': f"Could not parse evaluation: {str(e)}"
            }
    
    def should_escalate_query(
        self, 
        user_query: str, 
        rag_response: str, 
        retrieved_sources: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Simple boolean check for whether query needs escalation
        
        Args:
            user_query: User's question
            rag_response: Generated response  
            retrieved_sources: Source documents (optional)
            
        Returns:
            True if query should be escalated to human support
        """
        if retrieved_sources is None:
            retrieved_sources = []
            
        evaluation = self.evaluate_query_satisfaction(
            user_query, rag_response, retrieved_sources
        )
        
        return evaluation.get('needs_escalation', False)
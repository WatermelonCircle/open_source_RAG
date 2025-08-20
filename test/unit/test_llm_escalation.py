"""
Test suite for LLM-based EscalationService

Tests the pure LLM approach for escalation decisions.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.escalation_service import EscalationService

class TestLLMEscalationService:
    """Test cases for LLM-based EscalationService"""
    
    def setup_method(self):
        """Set up test environment"""
        with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test-key'}):
            self.service = EscalationService()
    
    @patch('anthropic.Anthropic')
    def test_explicit_human_request_detection(self, mock_anthropic):
        """Test LLM detection of explicit human requests"""
        print("\n🧪 Testing LLM-based explicit human request detection...")
        
        # Mock Claude's response for explicit human request
        mock_response_text = """EXPLICIT_HUMAN_REQUEST: true
SATISFACTION_SCORE: 0.0
NEEDS_ESCALATION: true
CONFIDENCE: 0.95
REASON: explicit_human_request
EXPLANATION: User explicitly requested to speak with a human representative."""
        
        mock_response = Mock()
        mock_response.content = [Mock(text=mock_response_text)]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        service = EscalationService()
        service.client = mock_client
        
        test_queries = [
            "I want to talk to a human",
            "Can I speak to customer support?",
            "Please connect me to a real person",
            "Transfer me to an agent",
            "I need human help"
        ]
        
        for query in test_queries:
            result = service.evaluate_query_satisfaction(
                query, "Here's some information...", []
            )
            
            assert result['needs_escalation'] == True
            assert result['reason'] == 'explicit_human_request'
            print(f"  ✅ Detected explicit request: '{query[:40]}...'")
    
    @patch('anthropic.Anthropic')
    def test_satisfied_query_no_escalation(self, mock_anthropic):
        """Test LLM evaluation of satisfied queries"""
        print("\n🧪 Testing LLM evaluation of satisfied queries...")
        
        # Mock Claude's response for satisfied query
        mock_response_text = """EXPLICIT_HUMAN_REQUEST: false
SATISFACTION_SCORE: 0.9
NEEDS_ESCALATION: false
CONFIDENCE: 0.85
REASON: adequate_response
EXPLANATION: The response fully addresses the user's question with clear, actionable steps."""
        
        mock_response = Mock()
        mock_response.content = [Mock(text=mock_response_text)]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        service = EscalationService()
        service.client = mock_client
        
        user_query = "How do I reset my password?"
        rag_response = "To reset your password: 1) Go to login page 2) Click 'Forgot Password' 3) Enter your email 4) Check email for reset link"
        sources = [{"filename": "user_guide.pdf", "page": 15, "similarity_score": 0.9}]
        
        result = service.evaluate_query_satisfaction(user_query, rag_response, sources)
        
        assert result['needs_escalation'] == False
        assert result['reason'] == 'adequate_response'
        assert result['satisfaction_score'] == 0.9
        print("  ✅ Correctly identified satisfied query - no escalation needed")
    
    @patch('anthropic.Anthropic')
    def test_unsatisfied_query_escalation(self, mock_anthropic):
        """Test LLM evaluation of unsatisfied queries"""
        print("\n🧪 Testing LLM evaluation of unsatisfied queries...")
        
        # Mock Claude's response for unsatisfied query
        mock_response_text = """EXPLICIT_HUMAN_REQUEST: false
SATISFACTION_SCORE: 0.2
NEEDS_ESCALATION: true
CONFIDENCE: 0.8
REASON: incomplete_answer
EXPLANATION: The response is too vague and doesn't provide specific steps to solve the user's complex technical issue."""
        
        mock_response = Mock()
        mock_response.content = [Mock(text=mock_response_text)]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        service = EscalationService()
        service.client = mock_client
        
        user_query = "My device won't connect to Wi-Fi and shows error code 0x8007007E"
        rag_response = "Try restarting your device and check your network settings."
        sources = [{"filename": "troubleshoot.pdf", "page": 3, "similarity_score": 0.3}]
        
        result = service.evaluate_query_satisfaction(user_query, rag_response, sources)
        
        assert result['needs_escalation'] == True
        assert result['reason'] == 'incomplete_answer'
        assert result['satisfaction_score'] == 0.2
        print("  ✅ Correctly identified unsatisfied query - escalation needed")
    
    @patch('anthropic.Anthropic')
    def test_no_sources_escalation(self, mock_anthropic):
        """Test LLM evaluation when no relevant sources found"""
        print("\n🧪 Testing LLM evaluation with no relevant sources...")
        
        # Mock Claude's response for no relevant sources
        mock_response_text = """EXPLICIT_HUMAN_REQUEST: false
SATISFACTION_SCORE: 0.1
NEEDS_ESCALATION: true
CONFIDENCE: 0.9
REASON: no_relevant_sources
EXPLANATION: No relevant documentation was found to answer the user's specific question. Human support is needed."""
        
        mock_response = Mock()
        mock_response.content = [Mock(text=mock_response_text)]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        service = EscalationService()
        service.client = mock_client
        
        user_query = "How do I integrate this with my custom blockchain solution?"
        rag_response = "I don't have specific information about that integration."
        sources = []  # No sources found
        
        result = service.evaluate_query_satisfaction(user_query, rag_response, sources)
        
        assert result['needs_escalation'] == True
        assert result['reason'] == 'no_relevant_sources'
        print("  ✅ Correctly escalated when no relevant sources found")
    
    @patch('anthropic.Anthropic')
    def test_api_error_handling(self, mock_anthropic):
        """Test graceful handling of API errors"""
        print("\n🧪 Testing API error handling...")
        
        # Mock API error
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client
        
        service = EscalationService()
        service.client = mock_client
        
        result = service.evaluate_query_satisfaction(
            "Test query", "Test response", []
        )
        
        # Should not crash and provide reasonable defaults
        assert 'needs_escalation' in result
        assert 'reason' in result
        assert result['reason'] == 'evaluation_error'
        print("  ✅ Gracefully handled API error")
    
    def test_parse_evaluation_response_with_explicit_field(self):
        """Test parsing evaluation response with new EXPLICIT_HUMAN_REQUEST field"""
        print("\n🧪 Testing evaluation response parsing...")
        
        mock_response = """EXPLICIT_HUMAN_REQUEST: true
SATISFACTION_SCORE: 0.3
NEEDS_ESCALATION: true
CONFIDENCE: 0.9
REASON: explicit_human_request
EXPLANATION: User clearly requested to speak with a human agent."""
        
        result = self.service._parse_evaluation_response(mock_response)
        
        assert result['explicit_human_request'] == True
        assert result['satisfaction_score'] == 0.3
        assert result['needs_escalation'] == True
        assert result['confidence'] == 0.9
        assert result['reason'] == 'explicit_human_request'
        print("  ✅ Correctly parsed evaluation response with explicit request field")

def run_llm_escalation_tests():
    """Run all LLM escalation tests"""
    print("🧪 Testing LLM-Based EscalationService...")
    print("=" * 50)
    
    # Check API key
    if not os.getenv('CLAUDE_API_KEY'):
        print("⚠️  CLAUDE_API_KEY not found, setting mock for tests")
        os.environ['CLAUDE_API_KEY'] = 'test-mock-key'
    
    test_service = TestLLMEscalationService()
    test_service.setup_method()
    
    try:
        # Run all tests
        test_service.test_explicit_human_request_detection()
        test_service.test_satisfied_query_no_escalation()
        test_service.test_unsatisfied_query_escalation()
        test_service.test_no_sources_escalation()
        test_service.test_api_error_handling()
        test_service.test_parse_evaluation_response_with_explicit_field()
        
        print("\n" + "=" * 50)
        print("🎉 ALL LLM ESCALATION TESTS PASSED!")
        print("✅ LLM-based explicit request detection: WORKING")
        print("✅ LLM-based satisfaction evaluation: WORKING")
        print("✅ Error handling: ROBUST")
        print("✅ Response parsing: WORKING")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ LLM escalation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_llm_escalation_tests()
    sys.exit(0 if success else 1)
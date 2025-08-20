"""
Test suite for EscalationService

Tests the query satisfaction evaluation and human support detection logic.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.escalation_service import EscalationService

class TestEscalationService:
    """Test cases for EscalationService"""
    
    def setup_method(self):
        """Set up test environment"""
        # Mock the Claude API key for testing
        with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test-key'}):
            self.service = EscalationService()
    
    def test_detect_explicit_human_request_positive(self):
        """Test detection of explicit human support requests"""
        test_queries = [
            "I want to talk to human support",
            "Can I speak to a human agent?",
            "Please connect me to customer support",
            "I need to talk to someone real",
            "Transfer me to human representative"
        ]
        
        for query in test_queries:
            result = self.service._detect_explicit_human_request(query)
            assert result['is_explicit'] == True, f"Failed to detect human request in: {query}"
            assert "explanation" in result
            print(f"✅ Detected human request: '{query}' -> {result['explanation']}")
    
    def test_detect_explicit_human_request_negative(self):
        """Test queries that should NOT trigger human support"""
        test_queries = [
            "How do I install the product?",
            "What is the warranty period?",
            "My device is not working properly",
            "Can you help me with configuration?",
            "I have a question about features"
        ]
        
        for query in test_queries:
            result = self.service._detect_explicit_human_request(query)
            assert result['is_explicit'] == False, f"Incorrectly detected human request in: {query}"
            print(f"✅ Correctly identified as non-human request: '{query}'")
    
    def test_parse_evaluation_response_valid(self):
        """Test parsing of valid Claude evaluation response"""
        mock_response = """
SATISFACTION_SCORE: 0.3
NEEDS_ESCALATION: true
CONFIDENCE: 0.8
REASON: incomplete_answer
EXPLANATION: The response doesn't fully address the user's specific technical question about configuration steps.
"""
        
        result = self.service._parse_evaluation_response(mock_response)
        
        assert result['satisfaction_score'] == 0.3
        assert result['needs_escalation'] == True
        assert result['confidence'] == 0.8
        assert result['reason'] == 'incomplete_answer'
        assert 'configuration steps' in result['explanation']
        print("✅ Correctly parsed valid evaluation response")
    
    def test_parse_evaluation_response_invalid(self):
        """Test parsing of malformed response (should not crash)"""
        mock_response = "Invalid response format without proper fields"
        
        result = self.service._parse_evaluation_response(mock_response)
        
        # Should have default values and not crash
        assert 'satisfaction_score' in result
        assert 'needs_escalation' in result
        assert 'confidence' in result
        assert 'reason' in result
        assert 'explanation' in result
        print("✅ Gracefully handled malformed evaluation response")
    
    @patch('anthropic.Anthropic')
    def test_evaluate_query_satisfaction_explicit_request(self, mock_anthropic):
        """Test evaluation when user explicitly requests human support"""
        user_query = "I want to talk to customer support"
        rag_response = "Here's some information about your product..."
        sources = []
        
        result = self.service.evaluate_query_satisfaction(user_query, rag_response, sources)
        
        assert result['needs_escalation'] == True
        assert result['reason'] == 'explicit_human_request'
        assert result['confidence'] >= 0.9
        print("✅ Correctly identified explicit human support request")
    
    @patch('anthropic.Anthropic')
    def test_evaluate_query_satisfaction_api_error(self, mock_anthropic):
        """Test evaluation when Claude API fails"""
        # Mock API to raise an exception
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client
        
        service = EscalationService()
        service.client = mock_client
        
        user_query = "How do I configure my device?"
        rag_response = "To configure your device, follow these steps..."
        sources = [{'filename': 'manual.pdf', 'page': 1}]
        
        result = service.evaluate_query_satisfaction(user_query, rag_response, sources)
        
        # Should not crash and provide reasonable defaults
        assert 'needs_escalation' in result
        assert result['reason'] == 'evaluation_error'
        print("✅ Gracefully handled API error during evaluation")
    
    def test_should_escalate_query_simple(self):
        """Test simple boolean escalation check"""
        with patch.object(self.service, 'evaluate_query_satisfaction') as mock_eval:
            mock_eval.return_value = {'needs_escalation': True}
            
            result = self.service.should_escalate_query(
                "test query", "test response", []
            )
            
            assert result == True
            print("✅ Simple escalation check works correctly")

def run_escalation_tests():
    """Run all escalation service tests"""
    print("🧪 Testing EscalationService...")
    
    # Check if Claude API key is available
    if not os.getenv('CLAUDE_API_KEY'):
        print("⚠️  CLAUDE_API_KEY not found, setting mock for tests")
        os.environ['CLAUDE_API_KEY'] = 'test-mock-key'
    
    test_service = TestEscalationService()
    test_service.setup_method()
    
    try:
        # Run individual tests
        test_service.test_detect_explicit_human_request_positive()
        test_service.test_detect_explicit_human_request_negative()
        test_service.test_parse_evaluation_response_valid()
        test_service.test_parse_evaluation_response_invalid()
        test_service.test_evaluate_query_satisfaction_explicit_request()
        test_service.test_evaluate_query_satisfaction_api_error()
        test_service.test_should_escalate_query_simple()
        
        print("\n🎉 All EscalationService tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ EscalationService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_escalation_tests()
    sys.exit(0 if success else 1)
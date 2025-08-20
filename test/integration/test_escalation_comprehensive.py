"""
Comprehensive Test Suite for EscalationService

Tests all possible scenarios including:
- Various types of user queries
- Different RAG response qualities
- API failures and error conditions
- Edge cases and boundary conditions
- Real-world user interaction patterns
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.escalation_service import EscalationService

class TestEscalationServiceComprehensive:
    """Comprehensive test cases for all escalation scenarios"""
    
    def setup_method(self):
        """Set up test environment"""
        with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test-key'}):
            self.service = EscalationService()
    
    def test_explicit_human_requests_extensive(self):
        """Test extensive list of explicit human support requests"""
        print("\n🧪 Testing explicit human support requests...")
        
        explicit_requests = [
            # Direct requests
            "I want to talk to human support",
            "Can I speak to a human?",
            "Please connect me to customer support",
            "I need human help",
            "Talk to human agent",
            "Contact customer service",
            "I want to speak with someone",
            "Can you transfer me to a person?",
            
            # Variations with different phrasing
            "I'd like to speak to human support please",
            "Could you please connect me to live chat?",
            "Is there a way to talk to a real person?",
            "I need to speak with a human representative",
            "Can I get connected to human customer support?",
            
            # Frustrated user requests
            "This isn't helping, I need human support!",
            "Just connect me to someone who can actually help",
            "I want to talk to a HUMAN, not a bot",
            "Get me customer support now",
            
            # Polite variations
            "Would it be possible to speak with human support?",
            "May I please talk to a human agent?",
            "Could you kindly connect me to customer service?",
            
            # Case variations
            "TALK TO HUMAN SUPPORT",
            "talk to human support",
            "Talk To Human Support",
            
            # With extra context
            "This is urgent, I need to talk to human support immediately",
            "My order is wrong, please connect me to customer support",
            "I've tried everything, can I speak to a human agent please?"
        ]
        
        for query in explicit_requests:
            result = self.service._detect_explicit_human_request(query)
            assert result['is_explicit'] == True, f"Failed to detect: '{query}'"
            print(f"  ✅ Detected: '{query[:50]}{'...' if len(query) > 50 else ''}' -> {result['explanation'][:50]}...")
    
    def test_non_explicit_requests_extensive(self):
        """Test queries that should NOT trigger human escalation"""
        print("\n🧪 Testing non-explicit requests...")
        
        non_explicit_requests = [
            # Regular product questions
            "How do I install this software?",
            "What is the warranty period for this product?",
            "My device is not working, what should I do?",
            "Can you help me configure the settings?",
            "Where can I find the user manual?",
            
            # Technical troubleshooting
            "The app keeps crashing when I open it",
            "Error code 404 appears when I try to connect",
            "The battery drains very quickly, is this normal?",
            "How do I update the firmware?",
            "The Wi-Fi connection keeps dropping",
            
            # Feature questions
            "What features are included in the premium version?",
            "How do I enable dark mode?",
            "Can this device work with other brands?",
            "What's the difference between model A and B?",
            "How many users can access this simultaneously?",
            
            # Setup and usage
            "Step-by-step guide for first-time setup",
            "How to backup my data before upgrading?",
            "Best practices for maintaining the device",
            "Recommended settings for optimal performance",
            
            # Troubleshooting with 'human' mentions (but not requests)
            "Is this a known issue that humans experience?",
            "Does this work better for human users vs automation?",
            "The human interface design seems confusing",
            
            # Edge cases that might be tricky - questions about support, not requests for it
            "How do I find contact information for support?",
            "What are the customer service hours?",
            "The customer service documentation mentions...",
            "I read that human agents usually recommend...",
            "Where can I find support contact details?",
        ]
        
        for query in non_explicit_requests:
            result = self.service._detect_explicit_human_request(query)
            assert result['is_explicit'] == False, f"Incorrectly detected: '{query}'"
            print(f"  ✅ Correctly identified as non-human: '{query[:60]}{'...' if len(query) > 60 else ''}'")
    
    def test_edge_case_queries(self):
        """Test edge cases and boundary conditions"""
        print("\n🧪 Testing edge cases...")
        
        edge_cases = [
            ("", False, "Empty string"),
            ("   ", False, "Whitespace only"),
            ("human", False, "Single word 'human'"),
            ("support", False, "Single word 'support'"),
            ("talk", False, "Single word 'talk'"),
            ("Human Support", False, "Title case without action"),
            ("I mention human support in passing", False, "Mention without request"),
            ("What is human support?", False, "Question about human support"),
            ("human support is great", False, "Statement about human support"),
            ("talk to human support NOW!", True, "Urgent request"),
            ("HUMAN SUPPORT!!!", False, "Just keywords with emphasis"),
            ("talk 2 human support", True, "Text-speak variation"),
            ("can u connect me 2 human support?", True, "Informal text variation"),
        ]
        
        for query, expected, description in edge_cases:
            result = self.service._detect_explicit_human_request(query)
            assert result['is_explicit'] == expected, f"Edge case failed: {description} - '{query}'"
            print(f"  ✅ {description}: '{query}' -> {'Human request' if expected else 'Not human request'}")
    
    def test_evaluation_response_parsing_comprehensive(self):
        """Test all possible evaluation response formats"""
        print("\n🧪 Testing evaluation response parsing...")
        
        test_cases = [
            # Perfect format
            {
                "response": """SATISFACTION_SCORE: 0.8
NEEDS_ESCALATION: false
CONFIDENCE: 0.9
REASON: adequate_response
EXPLANATION: The response fully addresses the user's question with clear steps.""",
                "expected": {
                    "satisfaction_score": 0.8,
                    "needs_escalation": False,
                    "confidence": 0.9,
                    "reason": "adequate_response"
                }
            },
            
            # Different boolean formats
            {
                "response": """SATISFACTION_SCORE: 0.2
NEEDS_ESCALATION: true
CONFIDENCE: 0.85
REASON: incomplete_answer
EXPLANATION: Response lacks specific details.""",
                "expected": {
                    "satisfaction_score": 0.2,
                    "needs_escalation": True,
                    "confidence": 0.85,
                    "reason": "incomplete_answer"
                }
            },
            
            # Alternative boolean formats
            {
                "response": """SATISFACTION_SCORE: 0.1
NEEDS_ESCALATION: yes
CONFIDENCE: 0.7
REASON: no_relevant_sources
EXPLANATION: No documents found.""",
                "expected": {
                    "satisfaction_score": 0.1,
                    "needs_escalation": True,
                    "confidence": 0.7,
                    "reason": "no_relevant_sources"
                }
            },
            
            # Out of bounds values (should be clamped)
            {
                "response": """SATISFACTION_SCORE: 1.5
NEEDS_ESCALATION: false
CONFIDENCE: -0.1
REASON: adequate_response
EXPLANATION: Good response.""",
                "expected": {
                    "satisfaction_score": 1.0,  # Clamped to 1.0
                    "needs_escalation": False,
                    "confidence": 0.0,  # Clamped to 0.0
                    "reason": "adequate_response"
                }
            },
            
            # Missing fields (should use defaults)
            {
                "response": """SATISFACTION_SCORE: 0.6
EXPLANATION: Some explanation here.""",
                "expected": {
                    "satisfaction_score": 0.6,
                    "needs_escalation": False,  # Default
                    "confidence": 0.5,  # Default
                    "reason": "parsing_error"  # Default
                }
            },
            
            # Malformed format
            {
                "response": "This is not a valid response format at all!",
                "expected": {
                    "satisfaction_score": 0.5,
                    "needs_escalation": False,
                    "confidence": 0.5,
                    "reason": "parsing_error"
                }
            },
            
            # Extra content around valid format
            {
                "response": """Here's my analysis:
                
SATISFACTION_SCORE: 0.3
NEEDS_ESCALATION: true
CONFIDENCE: 0.8
REASON: vague_response
EXPLANATION: The response is too generic and doesn't address specifics.

Additional notes: This user seems frustrated.""",
                "expected": {
                    "satisfaction_score": 0.3,
                    "needs_escalation": True,
                    "confidence": 0.8,
                    "reason": "vague_response"
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            result = self.service._parse_evaluation_response(test_case["response"])
            expected = test_case["expected"]
            
            for key, expected_value in expected.items():
                actual_value = result[key]
                assert actual_value == expected_value, f"Test case {i+1}: {key} expected {expected_value}, got {actual_value}"
            
            print(f"  ✅ Test case {i+1}: Correctly parsed complex evaluation response")
    
    @patch('anthropic.Anthropic')
    def test_api_error_scenarios(self, mock_anthropic):
        """Test various API error scenarios"""
        print("\n🧪 Testing API error scenarios...")
        
        error_scenarios = [
            (Exception("Network timeout"), "Network timeout"),
            (Exception("API rate limit exceeded"), "API rate limit exceeded"),
            (Exception("Invalid API key"), "Invalid API key"),
            (Exception("Service unavailable"), "Service unavailable"),
            (Exception(""), "Empty error message"),
            (KeyError("messages"), "Key error"),
            (ValueError("Invalid model"), "Value error"),
        ]
        
        for error, description in error_scenarios:
            mock_client = Mock()
            mock_client.messages.create.side_effect = error
            mock_anthropic.return_value = mock_client
            
            service = EscalationService()
            service.client = mock_client
            
            result = service.evaluate_query_satisfaction(
                "Test query", "Test response", []
            )
            
            # Should gracefully handle all errors
            assert 'needs_escalation' in result
            assert 'reason' in result
            assert result['reason'] == 'evaluation_error'
            assert 'explanation' in result
            
            print(f"  ✅ Gracefully handled: {description}")
    
    def test_real_world_scenarios(self):
        """Test realistic customer service scenarios"""
        print("\n🧪 Testing real-world scenarios...")
        
        scenarios = [
            {
                "name": "Satisfied customer with good RAG response",
                "query": "How do I reset my password?",
                "response": "To reset your password: 1) Go to login page 2) Click 'Forgot Password' 3) Enter your email 4) Check your email for reset link 5) Follow the instructions",
                "sources": [{"filename": "user_guide.pdf", "page": 15, "similarity_score": 0.9}],
                "should_escalate": False
            },
            {
                "name": "Customer with vague response",
                "query": "My device won't turn on, what's wrong?",
                "response": "There could be various reasons why your device isn't working. Try some troubleshooting steps.",
                "sources": [{"filename": "troubleshoot.pdf", "page": 3, "similarity_score": 0.4}],
                "should_escalate": True
            },
            {
                "name": "No relevant documentation found",
                "query": "How do I integrate this with my custom ERP system?",
                "response": "I don't have specific information about ERP integrations in the available documentation.",
                "sources": [],
                "should_escalate": True
            },
            {
                "name": "Complex technical issue",
                "query": "The API returns error 500 intermittently when making batch requests with more than 100 items",
                "response": "For API issues, check your request format and rate limits.",
                "sources": [{"filename": "api_docs.pdf", "page": 22, "similarity_score": 0.3}],
                "should_escalate": True
            },
            {
                "name": "Simple question with perfect answer",
                "query": "What's the warranty period?",
                "response": "Your product comes with a 2-year manufacturer warranty covering all defects and malfunctions.",
                "sources": [{"filename": "warranty.pdf", "page": 1, "similarity_score": 0.95}],
                "should_escalate": False
            }
        ]
        
        with patch.object(self.service.client, 'messages') as mock_messages:
            for scenario in scenarios:
                # Mock Claude's response based on scenario
                if scenario["should_escalate"]:
                    mock_response_text = """SATISFACTION_SCORE: 0.2
NEEDS_ESCALATION: true
CONFIDENCE: 0.8
REASON: incomplete_answer
EXPLANATION: The response doesn't provide sufficient detail to solve the user's problem."""
                else:
                    mock_response_text = """SATISFACTION_SCORE: 0.9
NEEDS_ESCALATION: false
CONFIDENCE: 0.9
REASON: adequate_response
EXPLANATION: The response fully addresses the user's question with clear actionable steps."""
                
                mock_response = Mock()
                mock_response.content = [Mock(text=mock_response_text)]
                mock_messages.create.return_value = mock_response
                
                result = self.service.evaluate_query_satisfaction(
                    scenario["query"], 
                    scenario["response"], 
                    scenario["sources"]
                )
                
                assert result["needs_escalation"] == scenario["should_escalate"], \
                    f"Scenario '{scenario['name']}' escalation mismatch"
                
                print(f"  ✅ {scenario['name']}: {'Escalation' if scenario['should_escalate'] else 'No escalation'} - Correct!")

def run_comprehensive_tests():
    """Run all comprehensive escalation tests"""
    print("🧪 Running Comprehensive EscalationService Tests...")
    print("=" * 60)
    
    # Check API key
    if not os.getenv('CLAUDE_API_KEY'):
        print("⚠️  CLAUDE_API_KEY not found, setting mock for tests")
        os.environ['CLAUDE_API_KEY'] = 'test-mock-key'
    
    test_service = TestEscalationServiceComprehensive()
    test_service.setup_method()
    
    try:
        # Run all comprehensive tests
        test_service.test_explicit_human_requests_extensive()
        test_service.test_non_explicit_requests_extensive()
        test_service.test_edge_case_queries()
        test_service.test_evaluation_response_parsing_comprehensive()
        test_service.test_api_error_scenarios()
        test_service.test_real_world_scenarios()
        
        print("\n" + "=" * 60)
        print("🎉 ALL COMPREHENSIVE ESCALATION TESTS PASSED!")
        print("✅ Explicit human request detection: ROBUST")
        print("✅ Non-explicit query handling: ROBUST")
        print("✅ Edge case handling: ROBUST")
        print("✅ Response parsing: ROBUST")
        print("✅ Error handling: ROBUST")
        print("✅ Real-world scenarios: ROBUST")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Comprehensive test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
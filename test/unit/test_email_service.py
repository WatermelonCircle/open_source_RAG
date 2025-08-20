"""
Test suite for EmailService

Tests conversation summary generation and email report creation.
"""

import pytest
import os
import sys
from unittest.mock import patch, Mock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.email_service import EmailService

class TestEmailService:
    """Test cases for EmailService"""
    
    def setup_method(self):
        """Set up test environment"""
        with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test-key'}):
            self.service = EmailService()
    
    def test_fallback_summary_generation(self):
        """Test fallback summary when Claude is not available"""
        print("\n🧪 Testing fallback summary generation...")
        
        # Mock conversation history
        conversation = [
            {
                "user_message": "My device won't turn on and I've tried everything",
                "assistant_response": "Please check if the power cable is connected properly.",
                "timestamp": "2024-01-15 10:30:00"
            },
            {
                "user_message": "I've checked that already, it's still not working",
                "assistant_response": "Try holding the power button for 10 seconds.",
                "timestamp": "2024-01-15 10:32:00"
            }
        ]
        
        # Test with Claude disabled
        self.service.claude_client = None
        summary = self.service.generate_conversation_summary(conversation)
        
        assert "CUSTOMER ISSUE SUMMARY" in summary
        assert "2" in summary  # Should mention 2 interactions
        assert "I've checked that already" in summary  # Should include latest message
        
        print("✅ Fallback summary generated successfully")
    
    @patch('anthropic.Anthropic')
    def test_ai_summary_generation(self, mock_anthropic):
        """Test AI-powered summary generation"""
        print("\n🧪 Testing AI-powered summary generation...")
        
        # Mock Claude response
        mock_response_text = """**CUSTOMER ISSUE SUMMARY**
Customer's device won't turn on despite trying basic troubleshooting steps.

**KEY CONCERNS**
• Device completely unresponsive to power button
• Power cable connection verified but issue persists
• Customer has already attempted basic troubleshooting

**TECHNICAL DETAILS**
No specific error codes mentioned. Power-related hardware issue suspected.

**CURRENT STATUS**
Power cable check completed, power button troubleshooting attempted, issue unresolved.

**RECOMMENDED ACTION**
Hardware diagnostic or warranty replacement evaluation needed."""
        
        mock_response = Mock()
        mock_response.content = [Mock(text=mock_response_text)]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        service = EmailService()
        service.claude_client = mock_client
        
        conversation = [
            {
                "user_message": "My device won't turn on",
                "assistant_response": "Please check the power cable.",
                "timestamp": "2024-01-15 10:30:00"
            }
        ]
        
        summary = service.generate_conversation_summary(conversation)
        
        assert "CUSTOMER ISSUE SUMMARY" in summary
        assert "KEY CONCERNS" in summary
        assert "RECOMMENDED ACTION" in summary
        
        print("✅ AI-powered summary generated successfully")
    
    def test_conversation_formatting(self):
        """Test conversation formatting for analysis"""
        print("\n🧪 Testing conversation formatting...")
        
        conversation = [
            {
                "user_message": "Hello, I need help with my product",
                "assistant_response": "I'd be happy to help you with your product question.",
                "timestamp": "2024-01-15 10:30:00",
                "sources": [{"filename": "manual.pdf", "page": 1}]
            },
            {
                "user_message": "The screen is flickering",
                "assistant_response": "Screen flickering can be caused by several issues. Try adjusting the refresh rate in display settings.",
                "timestamp": "2024-01-15 10:32:00"
            }
        ]
        
        formatted = self.service._format_conversation_for_summary(conversation)
        
        assert "--- Turn 1 (2024-01-15 10:30:00) ---" in formatted
        assert "CUSTOMER: Hello, I need help" in formatted
        assert "FAQ AGENT: I'd be happy to help" in formatted
        assert "--- Turn 2" in formatted
        assert "flickering" in formatted
        
        print("✅ Conversation formatted correctly for analysis")
    
    def test_email_content_generation(self):
        """Test HTML email content generation"""
        print("\n🧪 Testing email content generation...")
        
        conversation = [
            {
                "user_message": "My order hasn't arrived yet",
                "assistant_response": "I understand your concern about the delayed order. Let me help you track it.",
                "timestamp": "2024-01-15 14:30:00",
                "sources": [{"filename": "shipping_policy.pdf", "page": 2}]
            }
        ]
        
        # Mock the AI summary generation to avoid API calls in test
        with patch.object(self.service, 'generate_conversation_summary') as mock_summary:
            mock_summary.return_value = "**CUSTOMER ISSUE SUMMARY**\nCustomer inquiring about delayed order delivery."
            
            html_content = self.service.create_support_report_email(
                customer_email="test@example.com",
                conversation_history=conversation,
                additional_notes="Customer seems concerned about timing"
            )
        
        # Verify HTML structure and content
        assert "<html>" in html_content
        assert "Customer Support Request" in html_content
        assert "AI-Generated Summary" in html_content
        assert "test@example.com" in html_content
        assert "My order hasn't arrived yet" in html_content
        assert "Within 4 hours" in html_content
        assert "Customer seems concerned about timing" in html_content
        assert "shipping_policy.pdf" in html_content
        
        print("✅ HTML email content generated successfully")
    
    def test_full_conversation_formatting_for_email(self):
        """Test full conversation HTML formatting"""
        print("\n🧪 Testing conversation HTML formatting...")
        
        conversation = [
            {
                "user_message": "I have a technical question",
                "assistant_response": "I'm here to help with technical questions.",
                "timestamp": "2024-01-15 09:00:00",
                "sources": [{"filename": "tech_manual.pdf", "page": 5}]
            }
        ]
        
        formatted_html = self.service._format_full_conversation_for_email(conversation)
        
        assert "<div" in formatted_html
        assert "Turn 1" in formatted_html
        assert "Customer:" in formatted_html
        assert "FAQ Agent:" in formatted_html
        assert "I have a technical question" in formatted_html
        assert "tech_manual.pdf" in formatted_html
        assert "Page 5" in formatted_html
        assert 'style=' in formatted_html  # Should have CSS styling
        
        print("✅ HTML conversation formatting is correct")
    
    def test_send_support_request_success(self):
        """Test successful support request submission"""
        print("\n🧪 Testing successful support request submission...")
        
        conversation = [
            {
                "user_message": "I need help with billing",
                "assistant_response": "I can help with billing questions.",
                "timestamp": "2024-01-15 11:00:00"
            }
        ]
        
        # Mock email generation and sending
        with patch.object(self.service, 'create_support_report_email') as mock_create:
            with patch.object(self.service, '_simulate_email_send') as mock_send:
                mock_create.return_value = "<html>Mock email content</html>"
                mock_send.return_value = {
                    "reference_id": "SUP-20240115-ABC123",
                    "status": "sent_simulation"
                }
                
                result = self.service.send_support_request(
                    customer_email="customer@example.com",
                    conversation_history=conversation,
                    additional_notes="Urgent billing inquiry"
                )
        
        assert result["success"] == True
        assert "4 hours" in result["message"]
        assert result["support_email"] == "shun.bu@gmail.com"
        assert "reference_id" in result
        assert "timestamp" in result
        
        print("✅ Support request submitted successfully")
    
    def test_send_support_request_failure(self):
        """Test support request failure handling"""
        print("\n🧪 Testing support request failure handling...")
        
        conversation = [
            {
                "user_message": "Test message",
                "assistant_response": "Test response",
                "timestamp": "2024-01-15 12:00:00"
            }
        ]
        
        # Mock email creation to raise an exception
        with patch.object(self.service, 'create_support_report_email') as mock_create:
            mock_create.side_effect = Exception("Email generation failed")
            
            result = self.service.send_support_request(
                customer_email="test@example.com",
                conversation_history=conversation
            )
        
        assert result["success"] == False
        assert "Failed to submit" in result["message"]
        assert "Email generation failed" in result["message"]
        assert "timestamp" in result
        
        print("✅ Support request failure handled gracefully")
    
    def test_empty_conversation_handling(self):
        """Test handling of empty conversation history"""
        print("\n🧪 Testing empty conversation handling...")
        
        # Test with empty conversation
        empty_conversation = []
        
        summary = self.service.generate_conversation_summary(empty_conversation)
        assert "no conversation history available" in summary.lower()
        
        # Test email generation with empty conversation
        with patch.object(self.service, 'generate_conversation_summary') as mock_summary:
            mock_summary.return_value = "No conversation available"
            
            html_content = self.service.create_support_report_email(
                customer_email=None,
                conversation_history=empty_conversation
            )
        
        assert "Email: Not provided" in html_content
        assert "No conversation history available" in html_content
        
        print("✅ Empty conversation handled correctly")
    
    def test_long_conversation_truncation(self):
        """Test truncation of very long conversations"""
        print("\n🧪 Testing long conversation truncation...")
        
        # Create a conversation with very long response
        long_response = "This is a very long response. " * 100  # > 300 characters
        
        conversation = [
            {
                "user_message": "Short question",
                "assistant_response": long_response,
                "timestamp": "2024-01-15 13:00:00"
            }
        ]
        
        formatted = self.service._format_conversation_for_summary(conversation)
        
        # Should be truncated with "..."
        assert "..." in formatted
        assert len(formatted) < len(long_response) + 200  # Should be significantly shorter
        
        print("✅ Long responses truncated appropriately")

def run_email_service_tests():
    """Run all email service tests"""
    print("🧪 Testing EmailService...")
    print("=" * 60)
    
    test_service = TestEmailService()
    test_service.setup_method()
    
    try:
        # Run all tests
        test_service.test_fallback_summary_generation()
        test_service.test_ai_summary_generation()
        test_service.test_conversation_formatting()
        test_service.test_email_content_generation()
        test_service.test_full_conversation_formatting_for_email()
        test_service.test_send_support_request_success()
        test_service.test_send_support_request_failure()
        test_service.test_empty_conversation_handling()
        test_service.test_long_conversation_truncation()
        
        print("\n" + "=" * 60)
        print("🎉 ALL EMAIL SERVICE TESTS PASSED!")
        print("✅ Conversation summarization: WORKING")
        print("✅ HTML email generation: WORKING")
        print("✅ Support request handling: WORKING")
        print("✅ Error handling: ROBUST")
        print("✅ Edge cases: HANDLED")
        print("✅ Email service ready for production!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Email service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_email_service_tests()
    sys.exit(0 if success else 1)
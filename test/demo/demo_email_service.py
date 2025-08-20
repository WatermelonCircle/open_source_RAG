"""
Demo script for EmailService

Shows what the generated email reports look like with sample conversation data.
"""

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.email_service import EmailService

def demo_email_service():
    """Demonstrate email service with realistic conversation data"""
    print("📧 Email Service Demo")
    print("=" * 50)
    
    # Initialize service
    service = EmailService()
    
    # Sample conversation that would trigger human support
    sample_conversation = [
        {
            "user_message": "Hi, I'm having trouble with my Gavasto vacuum cleaner. It won't turn on.",
            "assistant_response": "I'll help you with your vacuum issue! Let me provide some troubleshooting steps:\n\n**Please check these quick items:**\n• Power connection is firmly plugged in\n• Dust bin is properly installed\n• Filters are clean and properly installed\n• Hose is firmly connected to the cuff",
            "timestamp": "2024-01-15 14:30:00",
            "sources": [
                {"filename": "Manual.pdf", "page": 3, "similarity_score": 0.85},
                {"filename": "Quick Start Guide.pdf", "page": 1, "similarity_score": 0.78}
            ]
        },
        {
            "user_message": "I've checked all of those things already. The power light doesn't even come on when I press the button. I think there might be a hardware problem.",
            "assistant_response": "I understand you've already checked the basic troubleshooting steps and the power light isn't coming on at all. This could indicate a more serious hardware issue.\n\n**Since basic troubleshooting hasn't resolved the issue, I recommend:**\n• Checking if the issue started after any recent incidents\n• Verifying the power outlet works with other devices\n• Looking for any visible damage to the power cord",
            "timestamp": "2024-01-15 14:32:00",
            "sources": [
                {"filename": "Warranty.pdf", "page": 2, "similarity_score": 0.72}
            ]
        },
        {
            "user_message": "The power outlet works fine with other devices, and I don't see any damage to the cord. This is really frustrating because I just bought this vacuum last month and it's already broken. Can someone from your team call me to help fix this or arrange a replacement?",
            "assistant_response": "I completely understand your frustration - having a new product fail after just one month is definitely not the experience we want for our customers. Since you've already tried the standard troubleshooting steps and the unit appears to have a hardware issue, this sounds like it may be covered under warranty.\n\nFor warranty claims and hardware issues like this, our human support team can better assist you with:\n• Warranty evaluation and processing\n• Replacement or repair authorization\n• Direct phone support for immediate assistance",
            "timestamp": "2024-01-15 14:35:00",
            "sources": [
                {"filename": "Warranty.pdf", "page": 1, "similarity_score": 0.91}
            ]
        }
    ]
    
    # Generate support email
    print("🔄 Generating support request email...")
    
    try:
        html_content = service.create_support_report_email(
            customer_email="customer.smith@email.com",
            conversation_history=sample_conversation,
            additional_notes="Customer is frustrated with new product failure, requesting phone support for warranty claim"
        )
        
        # Save demo email to file
        demo_filename = "demo_support_email.html"
        with open(demo_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Demo email saved as: {demo_filename}")
        
        # Test the full support request flow
        result = service.send_support_request(
            customer_email="customer.smith@email.com",
            conversation_history=sample_conversation,
            additional_notes="Customer is frustrated with new product failure, requesting phone support for warranty claim"
        )
        
        print("\n📋 Support Request Result:")
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Support Email: {result['support_email']}")
        print(f"Response Time: {result['estimated_response_time']}")
        print(f"Reference ID: {result.get('reference_id', 'N/A')}")
        
        # Show conversation summary
        print("\n🤖 AI-Generated Summary:")
        summary = service.generate_conversation_summary(sample_conversation)
        print(summary)
        
        print("\n" + "=" * 50)
        print("🎉 Email service demo completed successfully!")
        print(f"📄 Check {demo_filename} to see the full HTML email")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_email_service()
    sys.exit(0 if success else 1)
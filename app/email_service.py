"""
Email Service for Customer Support Reports

Handles email notifications and conversation summaries.
Sends reports to human support team when customers need assistance.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any, Optional
import anthropic
from .config import settings

class EmailService:
    """Service for sending customer support emails"""
    
    # Support team email
    SUPPORT_EMAIL = "elegantthread.wp@gmail.com"
    
    # Email configuration (can be moved to settings later)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    def __init__(self):
        self.claude_client = None
        if settings.CLAUDE_API_KEY:
            self.claude_client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        print("📧 Initialized Email Service")
    
    def generate_conversation_summary(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate AI-powered summary of customer conversation
        
        Args:
            conversation_history: List of conversation turns with user/assistant messages
            
        Returns:
            Formatted summary highlighting issues and concerns
        """
        if not self.claude_client:
            return self._fallback_summary(conversation_history)
        
        # Format conversation for Claude
        conversation_text = self._format_conversation_for_summary(conversation_history)
        
        summary_prompt = f"""You are a customer support analyst. Please analyze this customer conversation and create a concise summary for the human support team.

CUSTOMER CONVERSATION:
{conversation_text}

Please provide a summary in this format:

**CUSTOMER ISSUE SUMMARY**
[Brief 1-2 sentence description of the main problem/question]

**KEY CONCERNS**
• [Primary concern or issue]
• [Secondary concerns if any]
• [Any frustration or urgency indicators]

**TECHNICAL DETAILS**
[Any specific error codes, product models, or technical information mentioned]

**CURRENT STATUS**
[What has been tried, what worked/didn't work]

**RECOMMENDED ACTION**
[Suggest what human support should focus on to help this customer]

**CUSTOMER CONTEXT**
• Conversation started: [timestamp if available]
• Number of interactions: {len(conversation_history)}
• Customer tone: [professional/frustrated/confused/etc.]

Focus on actionable information that will help human support provide targeted assistance."""

        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"❌ Error generating conversation summary: {e}")
            return self._fallback_summary(conversation_history)
    
    def _format_conversation_for_summary(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Format conversation history for Claude analysis"""
        formatted_lines = []
        
        for i, turn in enumerate(conversation_history, 1):
            user_msg = turn.get('user_message', '')
            assistant_msg = turn.get('assistant_response', '')
            timestamp = turn.get('timestamp', '')
            
            if timestamp:
                formatted_lines.append(f"--- Turn {i} ({timestamp}) ---")
            else:
                formatted_lines.append(f"--- Turn {i} ---")
            
            if user_msg:
                formatted_lines.append(f"CUSTOMER: {user_msg}")
            
            if assistant_msg:
                # Truncate very long responses for summary
                if len(assistant_msg) > 300:
                    assistant_msg = assistant_msg[:300] + "..."
                formatted_lines.append(f"FAQ AGENT: {assistant_msg}")
            
            formatted_lines.append("")  # Empty line between turns
        
        return "\n".join(formatted_lines)
    
    def _fallback_summary(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Generate basic summary when Claude is not available"""
        if not conversation_history:
            return "**CUSTOMER ISSUE SUMMARY**\nCustomer requested human support but no conversation history available."
        
        latest_turn = conversation_history[-1]
        user_message = latest_turn.get('user_message', 'No message recorded')
        
        summary = f"""**CUSTOMER ISSUE SUMMARY**
Customer requested human support after interacting with FAQ agent.

**CUSTOMER'S LATEST MESSAGE**
{user_message}

**CONVERSATION DETAILS**
• Total interactions: {len(conversation_history)}
• Customer requested human assistance after trying FAQ agent
• Please review full conversation below for context

**RECOMMENDED ACTION**
Review the conversation history and provide personalized assistance for this customer's specific needs."""
        
        return summary
    
    def create_support_report_email(
        self, 
        customer_email: Optional[str], 
        conversation_history: List[Dict[str, Any]],
        additional_notes: str = "",
        order_id: str = ""
    ) -> str:
        """
        Create formatted email for support team
        
        Args:
            customer_email: Customer's email if provided
            conversation_history: Full conversation history
            additional_notes: Any additional context
            order_id: Customer's order ID if provided
            
        Returns:
            Formatted HTML email content
        """
        # Generate AI summary
        ai_summary = self.generate_conversation_summary(conversation_history)
        
        # Format timestamp
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Customer info section
        customer_info = f"Email: {customer_email}" if customer_email else "Email: Not provided"
        order_info = f"<p><strong>Order ID:</strong> {order_id}</p>" if order_id else ""
        
        # Full conversation section
        full_conversation = self._format_full_conversation_for_email(conversation_history)
        
        # Create HTML email
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                🎯 Customer Support Request
            </h2>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin-top: 0; color: #1f2937;">📋 AI-Generated Summary</h3>
                <div style="white-space: pre-line; font-size: 14px;">
                    {ai_summary}
                </div>
            </div>
            
            <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin-top: 0; color: #1565c0;">👤 Customer Information</h3>
                <p><strong>Report Generated:</strong> {report_time}</p>
                <p><strong>{customer_info}</strong></p>
                {order_info}
                <p><strong>Response Required:</strong> Within 4 hours</p>
                {f"<p><strong>Additional Notes:</strong> {additional_notes}</p>" if additional_notes else ""}
            </div>
            
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px;">
                <h3 style="margin-top: 0; color: #7c2d12;">💬 Full Conversation History</h3>
                <div style="font-family: monospace; font-size: 13px; line-height: 1.4;">
                    {full_conversation}
                </div>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background: #f0f9ff; border-left: 4px solid #0ea5e9;">
                <p style="margin: 0; font-size: 14px; color: #0369a1;">
                    <strong>🚀 Next Steps:</strong> Please review this customer's conversation and provide personalized assistance. 
                    Aim to respond within 4 hours to maintain excellent customer service standards.
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _format_full_conversation_for_email(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Format full conversation for email display"""
        if not conversation_history:
            return "<p>No conversation history available.</p>"
        
        formatted_lines = []
        
        for i, turn in enumerate(conversation_history, 1):
            user_msg = turn.get('user_message', '')
            assistant_msg = turn.get('assistant_response', '')
            timestamp = turn.get('timestamp', '')
            sources = turn.get('sources', [])
            
            # Format timestamp
            time_display = f" ({timestamp})" if timestamp else ""
            
            formatted_lines.append(f'<div style="margin-bottom: 20px; padding: 10px; border: 1px solid #e5e7eb; border-radius: 6px;">')
            formatted_lines.append(f'<h4 style="color: #374151; margin-top: 0;">Turn {i}{time_display}</h4>')
            
            if user_msg:
                formatted_lines.append(f'<div style="margin-bottom: 10px;">')
                formatted_lines.append(f'<strong style="color: #dc2626;">Customer:</strong>')
                formatted_lines.append(f'<p style="margin: 5px 0; padding: 8px; background: #fef2f2; border-radius: 4px;">{user_msg}</p>')
                formatted_lines.append(f'</div>')
            
            if assistant_msg:
                formatted_lines.append(f'<div style="margin-bottom: 10px;">')
                formatted_lines.append(f'<strong style="color: #059669;">FAQ Agent:</strong>')
                formatted_lines.append(f'<p style="margin: 5px 0; padding: 8px; background: #ecfdf5; border-radius: 4px;">{assistant_msg}</p>')
                
                if sources:
                    source_list = ", ".join([f"{s.get('filename', 'Unknown')} (Page {s.get('page', '?')})" for s in sources[:3]])
                    formatted_lines.append(f'<small style="color: #6b7280;">Sources: {source_list}</small>')
                
                formatted_lines.append(f'</div>')
            
            formatted_lines.append(f'</div>')
        
        return "\n".join(formatted_lines)
    
    def send_support_request(
        self, 
        customer_email: Optional[str],
        order_id: str = "",
        conversation_history: List[Dict[str, Any]] = None,
        additional_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Send support request email to human support team
        
        Args:
            customer_email: Customer's email if provided
            order_id: Customer's order ID if provided
            conversation_history: Full conversation with FAQ agent
            additional_notes: Additional context from customer
            
        Returns:
            Result dictionary with success status and details
        """
        if conversation_history is None:
            conversation_history = []
            
        try:
            # Create email content
            html_content = self.create_support_report_email(
                customer_email, conversation_history, additional_notes, order_id
            )
            
            # Send actual email via SMTP
            result = self._send_real_email(html_content, customer_email)
            
            print(f"📧 Support request email generated for customer: {customer_email or 'Anonymous'}")
            
            return {
                "success": True,
                "message": "Support request submitted successfully. You will receive a response within 4 hours.",
                "support_email": self.SUPPORT_EMAIL,
                "estimated_response_time": "4 hours maximum",
                "reference_id": result.get("reference_id"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error sending support request: {e}")
            return {
                "success": False,
                "message": f"Failed to submit support request: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _send_real_email(self, html_content: str, customer_email: Optional[str]) -> Dict[str, Any]:
        """
        Send actual email via SMTP using Gmail
        """
        import uuid
        import ssl
        
        reference_id = f"SUP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Save email content to file for debugging
        try:
            debug_filename = f"debug_email_{reference_id}.html"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"📄 Debug email saved as: {debug_filename}")
        except:
            pass
        
        try:
            # Email configuration
            smtp_server = "smtp.gmail.com"
            port = 587  # For starttls
            sender_email = "elegantthread.wp@gmail.com"  # System sending email (same as support email)
            sender_password = os.getenv("GMAIL_APP_PASSWORD")  # App password for elegantthread.wp@gmail.com
            
            # For testing, we'll use a simple SMTP approach
            # In production, you would use proper authentication
            
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"Gavasto Support System <{sender_email}>"
            message["To"] = self.SUPPORT_EMAIL
            
            # Set subject and reply-to if customer email is provided
            if customer_email:
                message["Reply-To"] = customer_email
                message["Subject"] = f"🆘 Customer Support Request from {customer_email} - {reference_id}"
            else:
                message["Subject"] = f"🆘 Customer Support Request - {reference_id}"
            
            # Create HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send real email via SMTP
            if sender_password:
                try:
                    context = ssl.create_default_context()
                    with smtplib.SMTP(smtp_server, port) as server:
                        server.starttls(context=context)
                        server.login(sender_email, sender_password)
                        server.sendmail(sender_email, self.SUPPORT_EMAIL, message.as_string())
                    
                    print(f"📧 Email sent successfully to: {self.SUPPORT_EMAIL}")
                    print(f"📧 Customer: {customer_email or 'Anonymous'}")
                    
                except Exception as smtp_error:
                    print(f"❌ SMTP Error: {smtp_error}")
                    # Save email as backup if SMTP fails
                    email_filename = f"email_report_{reference_id}.eml"
                    with open(email_filename, 'w', encoding='utf-8') as f:
                        f.write(message.as_string())
                    print(f"📧 Email saved as backup: {email_filename}")
                    
            else:
                print("⚠️ No Gmail app password found - saving email instead of sending")
                email_filename = f"email_report_{reference_id}.eml"
                with open(email_filename, 'w', encoding='utf-8') as f:
                    f.write(message.as_string())
                print(f"📧 Email saved as: {email_filename}")
            
            return {
                "reference_id": reference_id,
                "recipient": self.SUPPORT_EMAIL,
                "customer_email": customer_email,
                "status": "email_generated",
                "file_saved": email_filename
            }
            
        except Exception as e:
            print(f"❌ Error preparing email: {e}")
            # Fallback to file save
            return {
                "reference_id": reference_id,
                "recipient": self.SUPPORT_EMAIL,
                "customer_email": customer_email,
                "status": "error_fallback"
            }
    
    def _simulate_email_send(self, html_content: str, customer_email: Optional[str]) -> Dict[str, Any]:
        """
        Simulate email sending for development/testing
        In production, this would be replaced with actual SMTP sending
        """
        import uuid
        
        reference_id = f"SUP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Save email content to file for debugging (optional)
        try:
            debug_filename = f"debug_email_{reference_id}.html"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"📄 Debug email saved as: {debug_filename}")
        except:
            pass  # Ignore file write errors in production
        
        return {
            "reference_id": reference_id,
            "recipient": self.SUPPORT_EMAIL,
            "customer_email": customer_email,
            "status": "sent_simulation"
        }

# Global instance
email_service = EmailService()
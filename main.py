import os
import sys

# Add error handling for imports
try:
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    from app.routes import router
    from app.config import settings
    import uvicorn
except Exception as e:
    print(f"❌ Import error in main.py: {e}")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}")
    import traceback
    traceback.print_exc()
    raise

app = FastAPI(title="RAG Webapp", description="Upload PDFs and chat with documents")

# Include API routes
app.include_router(router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Business Portal Routes
@app.get("/", response_class=HTMLResponse)
async def business_landing():
    """Serve business landing page"""
    with open("templates/landing.html", "r") as f:
        return f.read()

@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    """Serve business signup page"""
    with open("templates/signup.html", "r") as f:
        return f.read()

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve business login page"""
    with open("templates/login.html", "r") as f:
        return f.read()

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page():
    """Serve forgot password page"""
    with open("templates/forgot_password.html", "r") as f:
        return f.read()

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page():
    """Serve reset password page"""
    with open("templates/reset_password.html", "r") as f:
        return f.read()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve business dashboard page"""
    with open("templates/dashboard.html", "r") as f:
        return f.read()

# Customer Support Interface (accessible via unique agent slug)
@app.get("/support", response_class=HTMLResponse)  
async def customer_support_interface():
    """Serve customer support chat interface"""
    # This will serve the existing customer chat interface
    # Later we'll make this dynamic based on agent slug
    upload_section = '''
            <div id="upload-section" class="upload-section">
                <h3>Add Product Information</h3>
                <div class="file-input-wrapper">
                    <input type="file" id="file-input" accept=".pdf" multiple style="display: none;">
                    <button type="button" onclick="document.getElementById('file-input').click()" class="choose-file-btn" id="file-picker-btn">📁 Select PDF Files</button>
                    <div id="selected-files" style="margin-top: 8px; font-size: 14px; color: var(--gray-600);"></div>
                </div>
                <button onclick="uploadFiles()" class="upload-btn">🚀 Add Information</button>
            </div>''' if settings.ADMIN_MODE else ''
    
    title = "Selloop Support Portal" if settings.ADMIN_MODE else "Selloop Online Customer Support"  
    description = "Manage product knowledge base and test the support system" if settings.ADMIN_MODE else ""
    
    # No live support in this version
    live_support_section = ''
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            /* Modern Design System */
            :root {{
                --primary-blue: #2563eb;
                --primary-blue-light: #3b82f6;
                --gray-50: #f9fafb;
                --gray-100: #f3f4f6;
                --gray-200: #e5e7eb;
                --gray-300: #d1d5db;
                --gray-600: #4b5563;
                --gray-800: #1f2937;
                --success-green: #10b981;
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            }}

            body {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                min-height: 100vh;
                margin: 0;
            }}

            .main-container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}

            .chat-header {{
                background: white;
                padding: 20px 30px;
                border-radius: 16px 16px 0 0;
                box-shadow: var(--shadow-sm);
                border-bottom: 1px solid var(--gray-200);
            }}

            .chat-header h1 {{
                margin: 0;
                color: var(--gray-800);
                font-size: 24px;
                font-weight: 600;
            }}

            .chat-header p {{
                margin: 8px 0 0 0;
                color: var(--gray-600);
                font-size: 14px;
            }}

            .upload-section {{
                background: var(--gray-50);
                padding: 20px;
                border-bottom: 1px solid var(--gray-200);
                border-radius: 0;
            }}

            .upload-section h3 {{
                margin: 0 0 15px 0;
                color: var(--gray-800);
                font-size: 16px;
                font-weight: 600;
            }}

            .file-input-wrapper {{
                margin-bottom: 12px;
            }}

            .file-input-wrapper input[type="file"] {{
                border: 2px dashed var(--gray-300);
                border-radius: 8px;
                padding: 12px;
                width: 100%;
                background: white;
                font-size: 14px;
                cursor: pointer;
            }}

            .file-input-wrapper input[type="file"]::file-selector-button {{
                background: var(--blue-500);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                margin-right: 12px;
            }}

            .file-input-wrapper input[type="file"]::file-selector-button:hover {{
                background: var(--blue-600);
            }}

            .choose-file-btn {{
                background: var(--gray-100);
                color: var(--gray-800);
                border: 1px solid var(--gray-300);
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
                margin-bottom: 8px;
            }}

            .choose-file-btn:hover {{
                background: var(--gray-200);
            }}

            .upload-btn {{
                background: var(--primary-blue);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
            }}

            .upload-btn:hover {{
                background: var(--primary-blue-light);
            }}

            .chat-container {{
                background: white;
                border-radius: 0 0 16px 16px;
                box-shadow: var(--shadow-lg);
                overflow: hidden;
            }}

            .chat-header-section {{
                background: var(--gray-50);
                padding: 16px 20px;
                border-bottom: 1px solid var(--gray-200);
            }}

            .chat-header-section h3 {{
                margin: 0;
                color: var(--gray-800);
                font-size: 16px;
                font-weight: 600;
            }}

            .chat-messages {{
                height: 400px;
                overflow-y: auto;
                padding: 20px;
                background: #fafbfc;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}

            .message {{
                display: flex;
                max-width: 80%;
                animation: fadeIn 0.3s ease-in;
            }}

            .message.user {{
                align-self: flex-end;
                margin-left: auto;
            }}

            .message.representative {{
                align-self: flex-start;
                margin-right: auto;
            }}

            .message-bubble {{
                padding: 12px 16px;
                border-radius: 18px;
                box-shadow: var(--shadow-sm);
                line-height: 1.4;
                font-size: 14px;
                word-wrap: break-word;
            }}

            .user .message-bubble {{
                background: var(--primary-blue);
                color: white;
                border-bottom-right-radius: 4px;
            }}

            .representative .message-bubble {{
                background: white;
                color: var(--gray-800);
                border: 1px solid var(--gray-200);
                border-bottom-left-radius: 4px;
            }}

            .representative.status .message-bubble {{
                background: var(--gray-100);
                color: var(--gray-600);
                font-style: italic;
                font-size: 13px;
                padding: 8px 12px;
            }}

            .message.system {{
                align-self: center;
                margin: 0 auto;
                max-width: 60%;
            }}

            .system .message-bubble {{
                background: var(--gray-100);
                color: var(--gray-600);
                font-style: italic;
                font-size: 13px;
                padding: 8px 12px;
                text-align: center;
                border-radius: 16px;
            }}

            .system .message-sender {{
                display: none;
            }}

            .message-sender {{
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 4px;
                color: var(--gray-600);
            }}

            .user .message-sender {{
                color: rgba(255, 255, 255, 0.8);
                text-align: right;
            }}

            .bullet-point {{
                margin-left: 15px;
                margin-bottom: 0px;
                margin-top: 0px;
                color: var(--gray-700);
                line-height: 1.2;
                padding: 0;
            }}

            .typing-animation {{
                animation: pulse 1.5s infinite;
                color: var(--gray-400);
                font-size: 16px;
                padding: 4px 0;
            }}

            @keyframes pulse {{
                0%, 100% {{
                    opacity: 0.3;
                }}
                50% {{
                    opacity: 1;
                }}
            }}


            .message strong {{
                color: var(--primary-blue);
                font-weight: 600;
            }}

            .message-image {{
                max-width: 100%;
                max-height: 300px;
                border-radius: 8px;
                margin: 8px 0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                cursor: pointer;
            }}

            .message-image:hover {{
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }}

            .user .message-bubble strong {{
                color: rgba(255, 255, 255, 0.95);
            }}

            .chat-input-area {{
                padding: 20px;
                background: white;
                border-top: 1px solid var(--gray-200);
            }}

            .input-group {{
                display: flex;
                gap: 12px;
                align-items: center;
            }}

            .chat-input {{
                flex: 1;
                padding: 12px 16px;
                border: 2px solid var(--gray-200);
                border-radius: 24px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }}

            .chat-input:focus {{
                border-color: var(--primary-blue);
            }}

            .image-upload-btn {{
                background: var(--gray-100);
                color: var(--gray-600);
                border: 2px solid var(--gray-200);
                padding: 12px;
                border-radius: 20px;
                font-size: 16px;
                cursor: pointer;
                margin-right: 8px;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                min-width: 44px;
                height: 44px;
            }}

            .image-upload-btn:hover {{
                background: var(--gray-200);
                border-color: var(--gray-300);
            }}

            .send-btn {{
                background: var(--primary-blue);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
                min-width: 80px;
            }}

            .send-btn:hover {{
                background: var(--primary-blue-light);
            }}

            .typing-indicator {{
                display: flex;
                align-items: center;
                gap: 4px;
                padding: 8px 12px;
            }}

            .typing-dots {{
                display: flex;
                gap: 2px;
            }}

            .typing-dot {{
                width: 4px;
                height: 4px;
                background: var(--gray-400);
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }}

            .typing-dot:nth-child(1) {{ animation-delay: -0.32s; }}
            .typing-dot:nth-child(2) {{ animation-delay: -0.16s; }}

            @keyframes typing {{
                0%, 80%, 100% {{ transform: scale(0.8); opacity: 0.5; }}
                40% {{ transform: scale(1); opacity: 1; }}
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            /* Online Support Status Styles */
            .online-support-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 15px;
                padding: 12px 0;
                border-top: 1px solid var(--gray-200);
            }}

            .status-indicator {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .status-dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: var(--gray-400);
                transition: background-color 0.3s ease;
            }}

            .status-dot.online {{
                background: var(--success-green);
                box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
                animation: pulse-green 2s infinite;
            }}

            .status-dot.offline {{
                background: #94a3b8;
            }}

            @keyframes pulse-green {{
                0%, 100% {{ box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2); }}
                50% {{ box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.4); }}
            }}

            #status-text {{
                font-weight: 600;
                font-size: 14px;
                color: var(--gray-800);
            }}

            .support-message {{
                font-size: 12px;
                color: var(--gray-600);
            }}

            /* Email Report Section Styles */
            .email-report-section {{
                background: white;
                border-radius: 16px;
                box-shadow: var(--shadow-md);
                margin-top: 20px;
                overflow: hidden;
            }}

            .email-report-header {{
                background: var(--gray-50);
                padding: 20px 30px;
                border-bottom: 1px solid var(--gray-200);
            }}

            .email-report-header h3 {{
                margin: 0 0 8px 0;
                font-size: 18px;
                color: var(--gray-800);
                font-weight: 600;
            }}

            .email-report-header p {{
                margin: 0;
                font-size: 14px;
                color: var(--gray-600);
                line-height: 1.5;
            }}

            .email-input-group {{
                display: flex;
                gap: 12px;
                align-items: center;
                padding: 20px 30px;
                background: white;
            }}

            .email-input {{
                flex: 1;
                padding: 12px 16px;
                border: 2px solid var(--gray-200);
                border-radius: 24px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }}

            .email-input:focus {{
                border-color: var(--primary-blue);
            }}

            .send-report-btn {{
                background: var(--primary-blue);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
                white-space: nowrap;
                min-width: 100px;
            }}

            .send-report-btn:hover {{
                background: var(--primary-blue-light);
            }}

            .send-report-btn:disabled {{
                background: var(--gray-400);
                cursor: not-allowed;
            }}

            /* Responsive Design */
            @media (max-width: 768px) {{
                .main-container {{ padding: 10px; }}
                .message {{ max-width: 90%; }}
                .chat-messages {{ height: 350px; padding: 15px; }}
                .chat-header {{ padding: 15px 20px; }}
                .chat-input-area {{ padding: 15px; }}
                
            }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="chat-header">
                <h1>{title}</h1>
                {f"<p>{description}</p>" if description else ""}
            </div>
            {upload_section}
            <div class="chat-container">
                <div class="chat-header-section">
                </div>
                <div id="chat-messages" class="chat-messages"></div>
                <div class="chat-input-area">
                    <div class="input-group">
                        <input type="file" id="image-upload" accept="image/*" style="display: none;" onchange="handleImageUpload(event)">
                        <button onclick="triggerImageUpload()" class="image-upload-btn" title="Upload image">📷</button>
                        <input type="text" id="chat-input" class="chat-input" placeholder="Type your question...">
                        <button onclick="sendMessage()" class="send-btn">Send</button>
                    </div>
                </div>
            </div>
        </div>
        <script>
            window.ADMIN_MODE = {str(settings.ADMIN_MODE).lower()};
            // Set agent context for multi-tenant routing
            window.CUSTOMER_AGENT_SLUG = '';
        </script>
        <script src="/static/app.js?v=15"></script>
    </body>
    </html>
    """

@app.get("/chat/{agent_slug}", response_class=HTMLResponse)
async def customer_chat_interface(agent_slug: str):
    """Serve multi-tenant customer chat interface for specific agent"""
    # Import here to avoid circular imports
    from app.supabase_vector_store import vector_store
    
    try:
        # Get agent by slug
        agent_response = vector_store.supabase.table("support_agents").select("*").eq("slug", agent_slug).execute()
        
        if not agent_response.data:
            return HTMLResponse(content="""
                <html><head><title>Agent Not Found - Selloop</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>Support Agent Not Found</h1>
                    <p>The support agent you're looking for doesn't exist or has been deactivated.</p>
                    <p>Please check the URL or contact the business directly.</p>
                </body></html>
            """, status_code=404)
        
        agent = agent_response.data[0]
        
        # Get business info
        business_response = vector_store.supabase.table("business_accounts").select("*").eq("id", agent["business_id"]).execute()
        business = business_response.data[0] if business_response.data else None
        
        business_name = business.get("business_name", "Support") if business else "Support"
        agent_name = agent.get("agent_name", "Customer Support")
        agent_description = agent.get("agent_config", {}).get("description", "")
        
        # Create the customer chat interface using original support structure
        # No upload section for customers
        upload_section = ''
        
        # Use business and agent name for title
        title = f"{business_name} - {agent_name}"
        description = agent_description if agent_description else ""
        
        # Create chat interface with original support structure
        return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            /* Modern Design System */
            :root {{
                --primary-blue: #2563eb;
                --primary-blue-light: #3b82f6;
                --gray-50: #f9fafb;
                --gray-100: #f3f4f6;
                --gray-200: #e5e7eb;
                --gray-300: #d1d5db;
                --gray-600: #4b5563;
                --gray-800: #1f2937;
                --success-green: #10b981;
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            }}

            body {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                min-height: 100vh;
                margin: 0;
            }}

            .main-container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}

            .chat-header {{
                background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
                padding: 20px 30px;
                border-radius: 16px 16px 0 0;
                box-shadow: var(--shadow-sm);
                border-bottom: 1px solid var(--gray-200);
                text-align: center;
            }}

            .chat-header h1 {{
                margin: 0;
                color: white;
                font-size: 24px;
                font-weight: 600;
            }}

            .chat-header p {{
                margin: 8px 0 0 0;
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
            }}

            .business-name {{
                font-size: 16px;
                color: rgba(255, 255, 255, 0.95);
                font-weight: 500;
                margin-bottom: 8px;
            }}

            .chat-container {{
                background: white;
                border-radius: 0 0 16px 16px;
                box-shadow: var(--shadow-lg);
                overflow: hidden;
            }}

            .chat-header-section {{
                background: var(--gray-50);
                padding: 16px 20px;
                border-bottom: 1px solid var(--gray-200);
            }}

            .chat-header-section h3 {{
                margin: 0;
                color: var(--gray-800);
                font-size: 16px;
                font-weight: 600;
            }}

            .chat-messages {{
                height: 400px;
                overflow-y: auto;
                padding: 20px;
                background: #fafbfc;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}

            .message {{
                display: flex;
                max-width: 80%;
                animation: fadeIn 0.3s ease-in;
            }}

            .message.user {{
                align-self: flex-end;
                margin-left: auto;
            }}

            .message.representative {{
                align-self: flex-start;
                margin-right: auto;
            }}

            .message-bubble {{
                padding: 12px 16px;
                border-radius: 18px;
                box-shadow: var(--shadow-sm);
                line-height: 1.4;
                font-size: 14px;
                word-wrap: break-word;
            }}

            .user .message-bubble {{
                background: var(--primary-blue);
                color: white;
                border-bottom-right-radius: 4px;
            }}

            .representative .message-bubble {{
                background: white;
                color: var(--gray-800);
                border: 1px solid var(--gray-200);
                border-bottom-left-radius: 4px;
            }}

            .representative.status .message-bubble {{
                background: var(--gray-100);
                color: var(--gray-600);
                font-style: italic;
                font-size: 13px;
                padding: 8px 12px;
            }}

            .message.system {{
                align-self: center;
                margin: 0 auto;
                max-width: 60%;
            }}

            .system .message-bubble {{
                background: var(--gray-100);
                color: var(--gray-600);
                font-style: italic;
                font-size: 13px;
                padding: 8px 12px;
                text-align: center;
                border-radius: 16px;
            }}

            .system .message-sender {{
                display: none;
            }}

            .message-sender {{
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 4px;
                color: var(--gray-600);
            }}

            .user .message-sender {{
                color: rgba(255, 255, 255, 0.8);
                text-align: right;
            }}

            .bullet-point {{
                margin-left: 15px;
                margin-bottom: 0px;
                margin-top: 0px;
                color: var(--gray-700);
                line-height: 1.2;
                padding: 0;
            }}

            .typing-animation {{
                animation: pulse 1.5s infinite;
                color: var(--gray-400);
                font-size: 16px;
                padding: 4px 0;
            }}

            @keyframes pulse {{
                0%, 100% {{
                    opacity: 0.3;
                }}
                50% {{
                    opacity: 1;
                }}
            }}

            .message strong {{
                color: var(--primary-blue);
                font-weight: 600;
            }}

            .message-image {{
                max-width: 100%;
                max-height: 300px;
                border-radius: 8px;
                margin: 8px 0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                cursor: pointer;
            }}

            .message-image:hover {{
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }}

            .user .message-bubble strong {{
                color: rgba(255, 255, 255, 0.95);
            }}

            .chat-input-area {{
                padding: 20px;
                background: white;
                border-top: 1px solid var(--gray-200);
            }}

            .input-group {{
                display: flex;
                gap: 12px;
                align-items: center;
            }}

            .chat-input {{
                flex: 1;
                padding: 12px 16px;
                border: 2px solid var(--gray-200);
                border-radius: 24px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }}

            .chat-input:focus {{
                border-color: var(--primary-blue);
            }}

            .image-upload-btn {{
                background: var(--gray-100);
                color: var(--gray-600);
                border: 2px solid var(--gray-200);
                padding: 12px;
                border-radius: 20px;
                font-size: 16px;
                cursor: pointer;
                margin-right: 8px;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                min-width: 44px;
                height: 44px;
            }}

            .image-upload-btn:hover {{
                background: var(--gray-200);
                border-color: var(--gray-300);
            }}

            .send-btn {{
                background: var(--primary-blue);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
                min-width: 80px;
            }}

            .send-btn:hover {{
                background: var(--primary-blue-light);
            }}

            .typing-indicator {{
                display: flex;
                align-items: center;
                gap: 4px;
                padding: 8px 12px;
            }}

            .typing-dots {{
                display: flex;
                gap: 2px;
            }}

            .typing-dot {{
                width: 4px;
                height: 4px;
                background: var(--gray-400);
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }}

            .typing-dot:nth-child(1) {{ animation-delay: -0.32s; }}
            .typing-dot:nth-child(2) {{ animation-delay: -0.16s; }}

            @keyframes typing {{
                0%, 80%, 100% {{ transform: scale(0.8); opacity: 0.5; }}
                40% {{ transform: scale(1); opacity: 1; }}
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            /* Responsive Design */
            @media (max-width: 768px) {{
                .main-container {{ padding: 10px; }}
                .message {{ max-width: 90%; }}
                .chat-messages {{ height: 350px; padding: 15px; }}
                .chat-header {{ padding: 15px 20px; }}
                .chat-input-area {{ padding: 15px; }}
            }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="chat-header">
                <h1>{business_name} Online Support</h1>
            </div>
            {upload_section}
            <div class="chat-container">
                <div class="chat-header-section">
                    <h3>💬 Live Support Chat</h3>
                </div>
                <div id="chat-messages" class="chat-messages"></div>
                <div class="chat-input-area">
                    <div class="input-group">
                        <input type="file" id="image-upload" accept="image/*" style="display: none;" onchange="handleImageUpload(event)">
                        <button onclick="triggerImageUpload()" class="image-upload-btn" title="Upload image">📷</button>
                        <input type="text" id="chat-input" class="chat-input" placeholder="Type your question...">
                        <button onclick="sendMessage()" class="send-btn">Send</button>
                    </div>
                </div>
            </div>
        </div>
        <script>
            window.ADMIN_MODE = {str(settings.ADMIN_MODE).lower()};
            // Set agent context for multi-tenant routing
            window.CUSTOMER_AGENT_SLUG = '';
        </script>
        <script src="/static/app.js?v=15"></script>
    </body>
    </html>
    """
        
    except Exception as e:
        print(f"❌ Error serving customer chat: {e}")
        return HTMLResponse(content=f"""
            <html><head><title>Error - Selloop</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>⚠️ Service Temporarily Unavailable</h1>
                <p>We're experiencing technical difficulties. Please try again later.</p>
                <p>Error: {str(e)}</p>
            </body></html>
        """, status_code=500)

@app.get("/agent-dashboard", response_class=HTMLResponse)
async def agent_dashboard():
    """Serve the agent dashboard for live chat support"""
    with open("agent_dashboard.html", "r") as f:
        return f.read()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

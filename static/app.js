// Frontend JavaScript for RAG Webapp

let uploadedFiles = [];
let sessionId = null;
let supportStatus = null;

// Initialize or retrieve session
function initializeSession() {
    // Try to get existing session from localStorage
    sessionId = localStorage.getItem('rag_session_id');
    
    if (!sessionId) {
        // Create new session
        createNewSession();
    }
}

function createNewSession() {
    fetch('/session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        sessionId = data.session_id;
        localStorage.setItem('rag_session_id', sessionId);
        console.log('New session created:', sessionId);
    })
    .catch(error => {
        console.error('Error creating session:', error);
        // Continue without session - backend will create one
    });
}

function uploadFiles() {
    const fileInput = document.getElementById('file-input');
    const files = fileInput.files;
    
    if (files.length === 0) {
        alert('Please select product manuals to add');
        return;
    }
    
    // Show upload progress
    addMessage('representative', 'Adding product information...');
    
    // Create FormData for file upload
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    
    // Upload files
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addMessage('representative', `Successfully added ${data.files_processed} product manuals to the knowledge base`);
            uploadedFiles = [...uploadedFiles, ...data.filenames];
            fileInput.value = ''; // Clear input
            
            // Show any failed files if there were some
            if (data.failed_files && data.failed_files.length > 0) {
                addMessage('representative', `Failed to process: ${data.failed_files.join(', ')}`);
            }
        } else {
            const errorMsg = data.failed_files && data.failed_files.length > 0 
                ? data.failed_files.join(', ') 
                : 'Unknown processing error';
            addMessage('representative', 'Failed to add information: ' + errorMsg);
        }
    })
    .catch(error => {
        addMessage('representative', 'Processing error: ' + error.message);
    });
}

function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Note: Backend will handle cases when no documents exist in database
    
    // Add user message to chat
    addMessage('user', message);
    chatInput.value = '';
    
    // Show typing indicator
    addMessage('representative', 'Typing...');
    
    // Send message to backend with session ID
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            message: message,
            session_id: sessionId 
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove thinking indicator
        removeLastSystemMessage();
        
        // Update session ID if provided by backend
        if (data.session_id && data.session_id !== sessionId) {
            sessionId = data.session_id;
            localStorage.setItem('rag_session_id', sessionId);
        }
        
        if (data.response) {
            addMessage('representative', data.response, data.sources);
        } else {
            addMessage('representative', 'Error: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        removeLastSystemMessage();
        addMessage('representative', 'Chat error: ' + error.message);
    });
}

function formatText(text) {
    // Convert markdown-style formatting to HTML
    let formatted = text;
    
    // Convert **bold** to <strong>bold</strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert bullet points • to HTML list items (before line break conversion)
    formatted = formatted.replace(/^(\s*)•\s(.+)$/gm, '$1<div class="bullet-point">• $2</div>');
    
    // Convert line breaks to HTML breaks, but avoid adding breaks around bullet points
    formatted = formatted.replace(/\n\n/g, '<br><br>');
    // Don't add breaks right before or after bullet points
    formatted = formatted.replace(/\n(?=<div class="bullet-point">)/g, '');
    formatted = formatted.replace(/(?<=<\/div>)\n/g, '');
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

function addMessage(sender, text, sources = []) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    
    // Determine if this is a status message
    const isStatusMessage = text.includes('Typing...') || text.includes('Error:') || 
                           text.includes('Welcome') || text.includes('Successfully') || 
                           text.includes('Failed') || text.includes('Hello!') || 
                           text.includes('Adding') || text.includes('Processing');
    
    // Set CSS classes based on sender and message type
    if (sender === 'representative' && isStatusMessage) {
        messageDiv.className = 'message representative status';
    } else {
        messageDiv.className = `message ${sender}`;
    }
    
    // Format the text for better display
    const formattedText = formatText(text);
    
    // Create message bubble structure
    const messageBubble = document.createElement('div');
    messageBubble.className = 'message-bubble';
    
    // Add sender label for clarity
    const senderLabel = document.createElement('div');
    senderLabel.className = 'message-sender';
    senderLabel.textContent = sender.charAt(0).toUpperCase() + sender.slice(1);
    
    // Set bubble content
    messageBubble.innerHTML = formattedText;
    
    // Assemble message structure
    messageDiv.appendChild(senderLabel);
    messageDiv.appendChild(messageBubble);
    
    // Add sources if provided and in admin mode
    if (window.ADMIN_MODE && sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources mt-2';
        sourcesDiv.innerHTML = '<small><strong>Sources:</strong><ul>' + 
            sources.map(source => `<li>${source.filename}, Page ${source.page}</li>`).join('') + 
            '</ul></small>';
        messageBubble.appendChild(sourcesDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeLastSystemMessage() {
    const chatMessages = document.getElementById('chat-messages');
    const messages = chatMessages.children;
    
    for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].className.includes('representative')) {
            messages[i].remove();
            break;
        }
    }
}

// Allow Enter key to send messages
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initial welcome message and session setup
window.onload = function() {
    // Initialize session management
    initializeSession();
    
    // Add file input change listener to show selected files
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const selectedFilesDiv = document.getElementById('selected-files');
            if (selectedFilesDiv) {
                if (this.files.length > 0) {
                    const fileNames = Array.from(this.files).map(f => f.name).join(', ');
                    selectedFilesDiv.textContent = `Selected: ${fileNames}`;
                    selectedFilesDiv.style.color = '#10b981';
                } else {
                    selectedFilesDiv.textContent = '';
                }
            }
        });
    }
    
    // Add welcome message
    if (window.ADMIN_MODE) {
        addMessage('representative', 'Welcome to the Support Portal. Add product information and test the system.');
    } else {
        addMessage('representative', 'Hello! I\'m here to help with your Gavasto product questions. How can I assist you today?');
        
        // Initialize support status and email report section for user mode
        initializeSupportStatus();
        showEmailReportSection();
    }
};

// Support Status Functions
function initializeSupportStatus() {
    updateSupportStatus();
    // Update status every 5 minutes
    setInterval(updateSupportStatus, 5 * 60 * 1000);
}

function updateSupportStatus() {
    fetch('/support/business-hours')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                supportStatus = data;
                updateStatusUI(data);
            } else {
                console.error('Failed to get support status:', data.error);
                updateStatusUI({ 
                    is_online: false, 
                    status_message: 'Unable to check support availability' 
                });
            }
        })
        .catch(error => {
            console.error('Error checking support status:', error);
            updateStatusUI({ 
                is_online: false, 
                status_message: 'Connection error' 
            });
        });
}

function updateStatusUI(status) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const supportMessage = document.getElementById('support-message');
    
    if (statusDot && statusText && supportMessage) {
        if (status.is_online) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Online';
            statusText.style.color = '#10b981';
            supportMessage.textContent = 'Live support is available now! Click to connect.';
            supportMessage.style.cursor = 'pointer';
            supportMessage.onclick = () => connectToLiveSupport();
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Offline';
            statusText.style.color = '#6b7280';
            supportMessage.textContent = status.status_message || 'Live support is currently offline';
            supportMessage.style.cursor = 'default';
            supportMessage.onclick = null;
        }
    }
}

function connectToLiveSupport() {
    if (supportStatus && supportStatus.is_online) {
        // Start live chat
        initializeLiveChat();
    } else {
        alert('Live support is currently offline. Please use the email report feature below.');
    }
}

// Email Report Functions
function showEmailReportSection() {
    const emailSection = document.getElementById('email-report-section');
    if (emailSection) {
        emailSection.style.display = 'block';
    }
}

function sendEmailReport() {
    const emailInput = document.getElementById('customer-email');
    const orderIdInput = document.getElementById('order-id');
    const reportButton = document.querySelector('.send-report-btn');
    
    if (!emailInput || !reportButton) return;
    
    const customerEmail = emailInput.value.trim();
    const orderId = orderIdInput ? orderIdInput.value.trim() : '';
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!customerEmail || !emailRegex.test(customerEmail)) {
        alert('Please enter a valid email address.');
        emailInput.focus();
        return;
    }
    
    // Disable button and show loading
    reportButton.disabled = true;
    reportButton.textContent = 'Sending...';
    
    // Prepare request data
    const requestData = {
        customer_email: customerEmail,
        order_id: orderId,
        session_id: sessionId,
        additional_notes: orderId ? `Customer requested email support after trying FAQ chat. Order ID: ${orderId}` : 'Customer requested email support after trying FAQ chat'
    };
    
    // Send email report
    fetch('/support/email-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            addMessage('representative', 
                `✅ **Email report sent successfully!**\n\n` +
                `• Your report has been sent to our support team\n` +
                `• Response time: ${data.estimated_response_time}\n` +
                `• Reference ID: ${data.reference_id || 'Generated'}\n\n` +
                `Thank you for using our support service!`
            );
            
            // Clear email input
            emailInput.value = '';
            
            // Hide email section after successful submission
            setTimeout(() => {
                const emailSection = document.getElementById('email-report-section');
                if (emailSection) {
                    emailSection.style.display = 'none';
                }
            }, 2000);
        } else {
            addMessage('representative', `❌ **Failed to send email report:**\n${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error sending email report:', error);
        addMessage('representative', '❌ **Error sending email report.** Please try again or contact support directly.');
    })
    .finally(() => {
        // Re-enable button
        reportButton.disabled = false;
        reportButton.textContent = 'Send the report';
    });
}

// Live Chat Functions
let liveChatWebSocket = null;
let isLiveChatActive = false;

function initializeLiveChat() {
    if (isLiveChatActive) {
        return; // Already in live chat
    }
    
    // Create live chat overlay
    createLiveChatOverlay();
    
    // Connect to WebSocket
    connectToLiveChatWebSocket();
}

function createLiveChatOverlay() {
    // Create overlay HTML
    const overlay = document.createElement('div');
    overlay.id = 'live-chat-overlay';
    overlay.innerHTML = `
        <div class="live-chat-modal">
            <div class="live-chat-header">
                <h3>Live Support Chat</h3>
                <button onclick="closeLiveChat()" class="close-live-chat">✕</button>
            </div>
            <div id="live-chat-messages" class="live-chat-messages">
                <div class="live-chat-message system">
                    <span class="message-content">Connecting you to a support agent...</span>
                </div>
            </div>
            <div class="live-chat-input-area">
                <input type="text" id="live-chat-input" placeholder="Type your message..." onkeypress="handleLiveChatKeyPress(event)">
                <button onclick="sendLiveChatMessage()" class="live-chat-send-btn">Send</button>
            </div>
        </div>
    `;
    
    // Add overlay styles
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    // Style the modal
    const modalStyles = `
        <style id="live-chat-styles">
            .live-chat-modal {
                background: white;
                border-radius: 12px;
                width: 90%;
                max-width: 500px;
                height: 600px;
                display: flex;
                flex-direction: column;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            }
            
            .live-chat-header {
                background: var(--primary-blue);
                color: white;
                padding: 16px 20px;
                border-radius: 12px 12px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .live-chat-header h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .close-live-chat {
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .live-chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #fafbfc;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .live-chat-message {
                max-width: 80%;
                padding: 8px 12px;
                border-radius: 12px;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .live-chat-message.customer {
                align-self: flex-end;
                background: var(--primary-blue);
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .live-chat-message.agent {
                align-self: flex-start;
                background: white;
                border: 1px solid var(--gray-200);
                border-bottom-left-radius: 4px;
            }
            
            .live-chat-message.system {
                align-self: center;
                background: var(--gray-100);
                color: var(--gray-600);
                font-style: italic;
                border-radius: 16px;
                text-align: center;
                max-width: 90%;
            }
            
            .live-chat-input-area {
                padding: 16px 20px;
                border-top: 1px solid var(--gray-200);
                display: flex;
                gap: 12px;
                align-items: center;
            }
            
            #live-chat-input {
                flex: 1;
                padding: 10px 14px;
                border: 2px solid var(--gray-200);
                border-radius: 20px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }
            
            #live-chat-input:focus {
                border-color: var(--primary-blue);
            }
            
            .live-chat-send-btn {
                background: var(--primary-blue);
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            
            .live-chat-send-btn:hover {
                background: var(--primary-blue-light);
            }
        </style>
    `;
    
    // Add styles to document
    if (!document.getElementById('live-chat-styles')) {
        document.head.insertAdjacentHTML('beforeend', modalStyles);
    }
    
    document.body.appendChild(overlay);
    isLiveChatActive = true;
}

function connectToLiveChatWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/customer`;
    
    liveChatWebSocket = new WebSocket(wsUrl);
    
    liveChatWebSocket.onopen = function(event) {
        console.log('Connected to live chat');
        addLiveChatMessage('system', 'Connected! Waiting for an available agent...');
    };
    
    liveChatWebSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleLiveChatMessage(data);
    };
    
    liveChatWebSocket.onclose = function(event) {
        console.log('Live chat disconnected');
        if (isLiveChatActive) {
            addLiveChatMessage('system', 'Disconnected from live chat.');
        }
    };
    
    liveChatWebSocket.onerror = function(error) {
        console.error('Live chat error:', error);
        addLiveChatMessage('system', 'Connection error. Please try again.');
    };
}

function handleLiveChatMessage(data) {
    const messageType = data.type;
    const content = data.content;
    
    switch (messageType) {
        case 'agent_joined':
            addLiveChatMessage('system', 'An agent has joined the chat!');
            addLiveChatMessage('agent', content);
            break;
            
        case 'chat_message':
            const senderType = data.sender_type === 'agent' ? 'agent' : 'customer';
            addLiveChatMessage(senderType, content);
            break;
            
        case 'chat_ended':
            addLiveChatMessage('system', content);
            setTimeout(() => {
                closeLiveChat();
            }, 3000);
            break;
            
        case 'system':
            addLiveChatMessage('system', content);
            break;
            
        case 'error':
            addLiveChatMessage('system', `Error: ${content}`);
            break;
    }
}

function addLiveChatMessage(type, content) {
    const messagesContainer = document.getElementById('live-chat-messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `live-chat-message ${type}`;
    
    const messageContent = document.createElement('span');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    messageDiv.appendChild(messageContent);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function sendLiveChatMessage() {
    const input = document.getElementById('live-chat-input');
    const message = input.value.trim();
    
    if (!message || !liveChatWebSocket || liveChatWebSocket.readyState !== WebSocket.OPEN) {
        return;
    }
    
    // Send message
    liveChatWebSocket.send(JSON.stringify({
        type: 'chat_message',
        content: message
    }));
    
    // Clear input
    input.value = '';
}

function handleLiveChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendLiveChatMessage();
    }
}

function closeLiveChat() {
    // Close WebSocket connection
    if (liveChatWebSocket) {
        liveChatWebSocket.close();
        liveChatWebSocket = null;
    }
    
    // Remove overlay
    const overlay = document.getElementById('live-chat-overlay');
    if (overlay) {
        overlay.remove();
    }
    
    isLiveChatActive = false;
}
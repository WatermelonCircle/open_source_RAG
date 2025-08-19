// Frontend JavaScript for RAG Webapp

let uploadedFiles = [];
let sessionId = null;

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
    }
};
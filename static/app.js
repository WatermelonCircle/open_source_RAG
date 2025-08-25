// Frontend JavaScript for RAG Webapp

let uploadedFiles = [];
let sessionId = null;
let agentName = null;
let selectedImage = null; // Store selected image for sending with text

// Pool of American names (mix of male and female)
const agentNames = [
    'Sarah', 'Michael', 'Jessica', 'David', 'Ashley', 'Christopher', 'Amanda', 'Matthew',
    'Jennifer', 'Joshua', 'Stephanie', 'Daniel', 'Nicole', 'Anthony', 'Samantha', 'Mark',
    'Elizabeth', 'Steven', 'Rachel', 'Andrew', 'Lauren', 'Kenneth', 'Emma', 'Paul',
    'Megan', 'Joshua', 'Kayla', 'Brian', 'Brittany', 'Ryan', 'Danielle', 'Justin',
    'Michelle', 'Robert', 'Christina', 'Nicholas', 'Amy', 'Jonathan', 'Melissa', 'Tyler'
];

function getRandomAgentName() {
    const randomIndex = Math.floor(Math.random() * agentNames.length);
    const selectedName = agentNames[randomIndex];
    console.log('Selecting random agent name:', selectedName, 'from index:', randomIndex);
    return selectedName;
}

// Initialize or retrieve session
function initializeSession() {
    // Try to get existing session from localStorage
    sessionId = localStorage.getItem('rag_session_id');
    agentName = localStorage.getItem('rag_agent_name');
    
    if (!sessionId || !agentName) {
        // Create new session with new agent name
        createNewSession();
    } else {
        console.log('Existing session loaded:', sessionId, 'Agent:', agentName);
    }
}

function createNewSession() {
    // Assign random agent name for this session
    agentName = getRandomAgentName();
    localStorage.setItem('rag_agent_name', agentName);
    
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
        console.log('New session created:', sessionId, 'Agent:', agentName);
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
    addMessage(agentName, 'Adding product information...');
    
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
            addMessage(agentName, `Successfully added ${data.files_processed} product manuals to the knowledge base`);
            uploadedFiles = [...uploadedFiles, ...data.filenames];
            fileInput.value = ''; // Clear input
            
            // Show any failed files if there were some
            if (data.failed_files && data.failed_files.length > 0) {
                addMessage(agentName, `Failed to process: ${data.failed_files.join(', ')}`);
            }
        } else {
            const errorMsg = data.failed_files && data.failed_files.length > 0 
                ? data.failed_files.join(', ') 
                : 'Unknown processing error';
            addMessage(agentName, 'Failed to add information: ' + errorMsg);
        }
    })
    .catch(error => {
        addMessage(agentName, 'Processing error: ' + error.message);
    });
}

// Global flag to prevent double sending
let isSending = false;

function sendMessage() {
    // Prevent double sending
    if (isSending) {
        console.log('Already sending, ignoring duplicate call');
        return;
    }
    
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    console.log('sendMessage called - message:', message, 'selectedImage:', selectedImage);
    
    // Check if we have either text or image
    if (!message && !selectedImage) {
        console.log('No message or image to send');
        return;
    }
    
    // Set sending flag
    isSending = true;
    
    // Add explicit debugging for selectedImage state
    console.log('DEBUG: selectedImage exists?', !!selectedImage);
    console.log('DEBUG: selectedImage name:', selectedImage ? selectedImage.name : 'null');
    console.log('DEBUG: message exists?', !!message);
    
    // Determine if we're sending text with image or just text
    if (selectedImage) {
        console.log('ROUTE: Sending text + image combination');
        // Send text + image combination
        sendTextWithImage(message);
    } else {
        console.log('ROUTE: Sending text only');
        // Send text only (original functionality)
        sendTextMessage(message);
    }
    
    // Clear input
    chatInput.value = '';
    
    // Clear sending flag after a brief delay to prevent rapid double clicks
    setTimeout(() => {
        isSending = false;
    }, 1000);
}

function sendTextMessage(message) {
    // Add user message to chat
    addMessage('user', message);
    
    // Send message to backend first to get response length
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
        // Calculate delay based on response length (3-30 seconds)
        const responseText = data.response || 'Error occurred';
        const wordCount = responseText.split(' ').length;
        
        // Base delay: 3 seconds + 0.3 seconds per word, capped at 30 seconds
        const calculatedDelay = Math.min(3000 + (wordCount * 300), 30000);
        const finalDelay = Math.max(calculatedDelay, 3000); // Minimum 3 seconds
        
        console.log(`Response: ${wordCount} words, delay: ${finalDelay/1000}s`);
        
        // Show typing indicator immediately, then show response after calculated delay
        addTypingIndicator();
        
        setTimeout(() => {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Update session ID if provided by backend
            if (data.session_id && data.session_id !== sessionId) {
                sessionId = data.session_id;
                localStorage.setItem('rag_session_id', sessionId);
            }
            
            if (data.response) {
                addMessage(agentName, data.response, data.sources);
            } else {
                addMessage(agentName, 'Error: ' + (data.error || 'Unknown error'));
            }
        }, finalDelay);
    })
    .catch(error => {
        // Show typing indicator briefly even for errors
        addTypingIndicator();
        
        setTimeout(() => {
            removeTypingIndicator();
            addMessage(agentName, 'Chat error: ' + error.message);
        }, 3000); // Minimum delay for errors
    });
}

function sendTextWithImage(message) {
    console.log('sendTextWithImage called with message:', message, 'selectedImage:', selectedImage);
    
    // Store reference to image before clearing
    const imageToSend = selectedImage;
    
    // Create FormData to send both text and image
    const formData = new FormData();
    if (imageToSend) {
        formData.append('image', imageToSend);
        console.log('Added image to FormData:', imageToSend.name);
    }
    if (message) {
        formData.append('message', message);
        console.log('Added message to FormData:', message);
    }
    formData.append('session_id', sessionId);
    
    // Add combined message to chat display
    addMessageWithImage('user', message, imageToSend);
    
    // Remove image preview from input area AFTER storing reference (but keep selectedImage)
    const previewContainer = document.getElementById('image-preview-container');
    if (previewContainer) {
        previewContainer.remove();
    }
    selectedImage = null; // Clear after successful storage in imageToSend
    
    // Reset placeholder text back to default
    const chatInput = document.getElementById('chat-input');
    chatInput.placeholder = 'Type your question...';
    
    // Show typing indicator
    addTypingIndicator();
    
    console.log('Sending request to /chat/combined');
    
    // Send to backend
    fetch('/chat/combined', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Calculate delay based on response length
        const responseText = data.response || 'Error occurred';
        const wordCount = responseText.split(' ').length;
        const calculatedDelay = Math.min(3000 + (wordCount * 300), 30000);
        const finalDelay = Math.max(calculatedDelay, 3000);
        
        setTimeout(() => {
            removeTypingIndicator();
            
            // Update session ID if provided
            if (data.session_id && data.session_id !== sessionId) {
                sessionId = data.session_id;
                localStorage.setItem('rag_session_id', sessionId);
            }
            
            if (data.response) {
                addMessage(agentName, data.response, data.sources);
            } else {
                addMessage(agentName, 'Error: ' + (data.error || 'Unknown error'));
            }
        }, finalDelay);
    })
    .catch(error => {
        setTimeout(() => {
            removeTypingIndicator();
            addMessage(agentName, 'Upload error: ' + error.message);
        }, 3000);
    });
}

function addMessageWithImage(sender, text, imageFile) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const timestamp = new Date().toLocaleTimeString();
    const senderName = sender === 'user' ? 'You' : agentName;
    
    // Create image URL for display
    const imageUrl = URL.createObjectURL(imageFile);
    
    let messageContent = '';
    if (imageFile) {
        messageContent += `<img src="${imageUrl}" alt="${imageFile.name}" class="message-image" onclick="openImageModal('${imageUrl}', '${imageFile.name}')">`;
        messageContent += `<div style="font-size: 12px; color: #666; margin-top: 4px;">${imageFile.name}</div>`;
    }
    if (text) {
        messageContent += `<div style="margin-top: ${imageFile ? '8px' : '0'}">${text}</div>`;
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="sender">${senderName}</span>
            <span class="timestamp">${timestamp}</span>
        </div>
        <div class="message-bubble">
            ${messageContent}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
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
    if (agentName && sender === agentName && isStatusMessage) {
        messageDiv.className = 'message representative status';
    } else if (agentName && sender === agentName) {
        messageDiv.className = 'message representative';
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

function addTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message representative typing-indicator';
    messageDiv.id = 'typing-indicator';
    
    const senderLabel = document.createElement('div');
    senderLabel.className = 'message-sender';
    senderLabel.textContent = agentName || 'Representative';
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-animation';
    typingDiv.textContent = '•••';
    
    messageDiv.appendChild(senderLabel);
    messageDiv.appendChild(typingDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function removeLastSystemMessage() {
    const chatMessages = document.getElementById('chat-messages');
    const messages = chatMessages.children;
    
    for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].className.includes('representative') || messages[i].className.includes('system')) {
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
    
    // Add welcome message with delay for better UX
    if (window.ADMIN_MODE) {
        // Show connecting message immediately
        addMessage('system', 'Connecting to support portal...');
        
        setTimeout(() => {
            removeLastSystemMessage();
            addMessage(agentName, 'Welcome to the Support Portal. Add product information and test the system.');
        }, 3000); // 3 second delay
    } else {
        // Show connecting message immediately
        addMessage('system', 'Connecting customer support...');
        
        setTimeout(() => {
            removeLastSystemMessage();
            addMessage(agentName, 'Hello! I\'m here to help with your Gavasto product questions. How can I assist you today?');
        }, 4000); // 4 second delay
        
    }
};

// Image Upload Functions
function triggerImageUpload() {
    document.getElementById('image-upload').click();
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    console.log('handleImageUpload called with file:', file);
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file.');
        return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('Image file too large. Please select an image under 5MB.');
        return;
    }
    
    // Store the selected image
    selectedImage = file;
    console.log('selectedImage stored:', selectedImage.name);
    
    // Create file reader to display preview in input area
    const reader = new FileReader();
    reader.onload = function(e) {
        console.log('Image preview loaded, calling showImagePreview');
        showImagePreview(e.target.result, file.name);
    };
    reader.readAsDataURL(file);
    
    // Clear the input
    event.target.value = '';
}

function showImagePreview(imageDataUrl, filename) {
    // Remove any existing preview (but don't clear selectedImage)
    let previewContainer = document.getElementById('image-preview-container');
    if (previewContainer) {
        previewContainer.remove();
    }
    
    // Create image preview container above the input
    const chatInputArea = document.querySelector('.chat-input-area');
    previewContainer = document.createElement('div');
    previewContainer.id = 'image-preview-container';
    previewContainer.style.cssText = `
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
    `;
    
    previewContainer.innerHTML = `
        <img src="${imageDataUrl}" alt="${filename}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 6px;">
        <div style="flex: 1;">
            <div style="font-size: 14px; font-weight: 500; color: #343a40;">${filename}</div>
            <div style="font-size: 12px; color: #6c757d;">Ready to send with your message</div>
        </div>
        <button onclick="removeImagePreview()" style="background: #dc3545; color: white; border: none; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 12px;">Remove</button>
    `;
    
    // Insert before the input group
    chatInputArea.insertBefore(previewContainer, chatInputArea.firstChild);
    
    // Update placeholder text
    const chatInput = document.getElementById('chat-input');
    chatInput.placeholder = 'Add a message to go with your image...';
}

function removeImagePreview() {
    console.log('removeImagePreview called');
    const previewContainer = document.getElementById('image-preview-container');
    if (previewContainer) {
        previewContainer.remove();
    }
    
    // Reset variables
    selectedImage = null;
    console.log('selectedImage cleared:', selectedImage);
    
    // Reset placeholder text
    const chatInput = document.getElementById('chat-input');
    chatInput.placeholder = 'Type your question...';
}

function addImageMessage(sender, imageDataUrl, filename) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const timestamp = new Date().toLocaleTimeString();
    const senderName = sender === 'user' ? 'You' : agentName;
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="sender">${senderName}</span>
            <span class="timestamp">${timestamp}</span>
        </div>
        <div class="message-bubble">
            <img src="${imageDataUrl}" alt="${filename}" class="message-image" onclick="openImageModal('${imageDataUrl}', '${filename}')">
            <div style="font-size: 12px; color: #666; margin-top: 4px;">${filename}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


function openImageModal(imageUrl, filename) {
    // Create modal for full-size image view
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        cursor: pointer;
    `;
    
    modal.innerHTML = `
        <div style="max-width: 90%; max-height: 90%; text-align: center;">
            <img src="${imageUrl}" alt="${filename}" style="max-width: 100%; max-height: 100%; border-radius: 8px;">
            <div style="color: white; margin-top: 10px; font-size: 14px;">${filename}</div>
            <div style="color: #ccc; margin-top: 5px; font-size: 12px;">Click anywhere to close</div>
        </div>
    `;
    
    modal.onclick = function() {
        document.body.removeChild(modal);
    };
    
    document.body.appendChild(modal);
}


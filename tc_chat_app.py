#!/usr/bin/env python3
"""
Transaction Coordinator Chat App - Ready for Render
Complete 2-way chat interface with WebSocket support
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
import time
from datetime import datetime
import uuid
from collections import defaultdict

# Import existing TC modules
from modules.ai.grok_client import GrokClient
from modules.agents.orchestrator import AgentOrchestrator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tc-chat-secret-2024')
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage (replace with Redis on Render for persistence)
chat_sessions = defaultdict(list)
active_users = {}

class TCChatHandler:
    def __init__(self):
        self.grok_client = GrokClient()
        self.orchestrator = AgentOrchestrator()
        
    def process_message(self, message, session_id, user_name):
        """Process incoming chat message"""
        try:
            # Add to conversation history
            chat_sessions[session_id].append({
                'id': str(uuid.uuid4()),
                'user': user_name,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'user'
            })
            
            # Process through TC system
            response = self.orchestrator.process_message({
                'from': user_name,
                'text': message,
                'source': 'web_chat',
                'session_id': session_id,
                'history': chat_sessions[session_id][-10:]  # Last 10 messages
            })
            
            # Format response
            tc_response = {
                'id': str(uuid.uuid4()),
                'user': 'Nicki (TC)',
                'message': response.get('response', 'I need to think about that...'),
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant',
                'confidence': response.get('confidence', 0.8),
                'actions': response.get('actions', [])
            }
            
            chat_sessions[session_id].append(tc_response)
            
            return tc_response
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return {
                'id': str(uuid.uuid4()),
                'user': 'Nicki (TC)',
                'message': 'I encountered an error. Please try again.',
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant',
                'error': True
            }

# Initialize handler
tc_handler = TCChatHandler()

@app.route('/')
def index():
    """Serve the chat interface"""
    return render_template('chat.html')

@app.route('/api/health')
def health():
    """Health check for Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(chat_sessions),
        'active_users': len(active_users)
    })

@socketio.on('connect')
def handle_connect():
    """Handle new connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'Connected to TC Chat'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle disconnection"""
    print(f"Client disconnected: {request.sid}")
    if request.sid in active_users:
        del active_users[request.sid]

@socketio.on('join_chat')
def handle_join(data):
    """Handle user joining chat"""
    session_id = data.get('session_id', str(uuid.uuid4()))
    user_name = data.get('user_name', 'Guest')
    
    join_room(session_id)
    active_users[request.sid] = {
        'session_id': session_id,
        'user_name': user_name
    }
    
    # Send chat history
    history = chat_sessions.get(session_id, [])
    
    # Send welcome message if new session
    if not history:
        welcome = {
            'id': str(uuid.uuid4()),
            'user': 'Nicki (TC)',
            'message': f"👋 Hi {user_name}! I'm Nicki, your Transaction Coordinator. How can I help you today?",
            'timestamp': datetime.now().isoformat(),
            'type': 'assistant'
        }
        chat_sessions[session_id].append(welcome)
        history = [welcome]
    
    emit('chat_history', {'messages': history[-50:]})  # Last 50 messages

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming message"""
    message = data.get('message', '').strip()
    if not message:
        return
    
    user_info = active_users.get(request.sid, {})
    session_id = user_info.get('session_id', 'default')
    user_name = user_info.get('user_name', 'Guest')
    
    # Emit user message to room
    user_msg = {
        'id': str(uuid.uuid4()),
        'user': user_name,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'type': 'user'
    }
    
    socketio.emit('new_message', user_msg, room=session_id)
    
    # Show typing indicator
    socketio.emit('typing', {'user': 'Nicki (TC)'}, room=session_id)
    
    # Process message in background
    socketio.start_background_task(
        process_and_respond,
        message,
        session_id,
        user_name
    )

def process_and_respond(message, session_id, user_name):
    """Process message and send response"""
    # Simulate thinking time
    time.sleep(1)
    
    # Get TC response
    response = tc_handler.process_message(message, session_id, user_name)
    
    # Stop typing indicator
    socketio.emit('stop_typing', {'user': 'Nicki (TC)'}, room=session_id)
    
    # Send response
    socketio.emit('new_message', response, room=session_id)

# Create templates directory and chat.html
os.makedirs('templates', exist_ok=True)

chat_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Transaction Coordinator Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: #2563eb;
            color: white;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header h1 {
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .status {
            font-size: 0.875rem;
            opacity: 0.9;
            margin-top: 0.25rem;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        .message {
            max-width: 70%;
            padding: 0.75rem 1rem;
            border-radius: 1rem;
            word-wrap: break-word;
        }
        .message.user {
            align-self: flex-end;
            background: #2563eb;
            color: white;
            border-bottom-right-radius: 0.25rem;
        }
        .message.assistant {
            align-self: flex-start;
            background: white;
            border: 1px solid #e5e7eb;
            border-bottom-left-radius: 0.25rem;
        }
        .message-info {
            font-size: 0.75rem;
            opacity: 0.7;
            margin-top: 0.25rem;
        }
        .typing {
            align-self: flex-start;
            padding: 0.75rem 1rem;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 1rem;
            border-bottom-left-radius: 0.25rem;
            font-style: italic;
            opacity: 0.7;
        }
        .input-container {
            background: white;
            border-top: 1px solid #e5e7eb;
            padding: 1rem;
            display: flex;
            gap: 0.5rem;
        }
        #messageInput {
            flex: 1;
            padding: 0.75rem;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            font-size: 1rem;
            outline: none;
        }
        #messageInput:focus {
            border-color: #2563eb;
        }
        #sendButton {
            padding: 0.75rem 1.5rem;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }
        #sendButton:hover {
            background: #1d4ed8;
        }
        #sendButton:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .confidence {
            display: inline-block;
            font-size: 0.75rem;
            padding: 0.125rem 0.5rem;
            border-radius: 1rem;
            background: #10b981;
            color: white;
            margin-left: 0.5rem;
        }
        .confidence.low { background: #ef4444; }
        .confidence.medium { background: #f59e0b; }
        
        @media (max-width: 640px) {
            .message { max-width: 85%; }
            .header h1 { font-size: 1.25rem; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 Transaction Coordinator Chat</h1>
        <div class="status" id="status">Connecting...</div>
    </div>
    
    <div class="chat-container" id="chatContainer"></div>
    
    <div class="input-container">
        <input type="text" id="messageInput" placeholder="Type your message..." autofocus>
        <button id="sendButton">Send</button>
    </div>

    <script>
        const socket = io();
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const status = document.getElementById('status');
        
        // Generate or retrieve session ID
        let sessionId = localStorage.getItem('tc_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('tc_session_id', sessionId);
        }
        
        // Get user name
        let userName = localStorage.getItem('tc_user_name');
        if (!userName) {
            userName = prompt('What\'s your name?') || 'Guest';
            localStorage.setItem('tc_user_name', userName);
        }
        
        // Socket events
        socket.on('connect', () => {
            status.textContent = 'Connected - Chat with Nicki';
            socket.emit('join_chat', { session_id: sessionId, user_name: userName });
        });
        
        socket.on('disconnect', () => {
            status.textContent = 'Disconnected - Reconnecting...';
        });
        
        socket.on('chat_history', (data) => {
            chatContainer.innerHTML = '';
            data.messages.forEach(msg => addMessage(msg));
            scrollToBottom();
        });
        
        socket.on('new_message', (message) => {
            addMessage(message);
            scrollToBottom();
        });
        
        socket.on('typing', () => {
            const typingEl = document.createElement('div');
            typingEl.className = 'typing';
            typingEl.id = 'typing-indicator';
            typingEl.textContent = 'Nicki is typing...';
            chatContainer.appendChild(typingEl);
            scrollToBottom();
        });
        
        socket.on('stop_typing', () => {
            const typingEl = document.getElementById('typing-indicator');
            if (typingEl) typingEl.remove();
        });
        
        // Send message
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            socket.emit('send_message', { message });
            messageInput.value = '';
            messageInput.focus();
        }
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Add message to chat
        function addMessage(msg) {
            const messageEl = document.createElement('div');
            messageEl.className = `message ${msg.type}`;
            
            let content = `<div>${msg.message}</div>`;
            
            if (msg.confidence && msg.type === 'assistant') {
                const level = msg.confidence > 0.8 ? 'high' : msg.confidence > 0.5 ? 'medium' : 'low';
                content += `<span class="confidence ${level}">${Math.round(msg.confidence * 100)}%</span>`;
            }
            
            content += `<div class="message-info">${msg.user} • ${formatTime(msg.timestamp)}</div>`;
            
            messageEl.innerHTML = content;
            chatContainer.appendChild(messageEl);
        }
        
        function formatTime(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        
        function scrollToBottom() {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    </script>
</body>
</html>'''

# Write the HTML template
with open('templates/chat.html', 'w') as f:
    f.write(chat_html)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 TC Chat App starting on port {port}")
    socketio.run(app, host='0.0.0.0', port=port)
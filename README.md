# Transaction Coordinator AI System

Real-time chat interface and intelligent email processing for transaction coordination.

## 🚀 Quick Deploy to Render

1. **Upload all files** to GitHub repository: `https://github.com/mattmizell/transaction_coordinator.git`
2. **Connect Render** to GitHub repo
3. **Add environment variable** in Render dashboard:
   - `XAI_API_KEY`: `xai-DA52OqHFkZk9jyKmnXsPWAdD3eRQGliT6RXjXgDcV5tXS5r4Uq4aMwmR5cqOd9vBJViUYmDkZf5Ygtsf`
4. **Deploy** - Render auto-detects configuration

## 📱 Features

- **Real-time chat** with WebSocket messaging
- **Mobile responsive** interface  
- **Intelligent email processing** with Grok AI
- **Conversation history** and threading
- **Confidence scores** on AI responses
- **Typing indicators** and status updates

## 🔧 Architecture

- **Frontend**: HTML5 + WebSocket for real-time chat
- **Backend**: Flask + SocketIO for WebSocket handling
- **AI**: Grok integration for intelligent responses
- **Email**: IMAP monitoring with smart response generation

## 📞 Usage

Once deployed, visit the Render URL to access the chat interface.
Users can chat directly with Nicki, the AI Transaction Coordinator.

## 🛠️ Development

Local development:
```bash
pip install -r requirements_chat.txt
python tc_chat_app.py
```

## 🌐 Deployment

Configured for one-click Render deployment via `render.yaml`.
Includes automatic scaling and health checks.
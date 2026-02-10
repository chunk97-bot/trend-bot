// Trend Radar AI Chat Widget
// Uses Claude API via serverless backend

const ChatWidget = {
  isOpen: false,
  messages: [],
  
  // CHANGE THIS to your Cloudflare Worker URL after deployment
  API_URL: 'https://trend-bot-chat.YOUR_SUBDOMAIN.workers.dev/chat',
  
  init() {
    this.createWidget();
    this.loadHistory();
    this.bindEvents();
  },
  
  createWidget() {
    const widget = document.createElement('div');
    widget.id = 'chat-widget';
    widget.innerHTML = `
      <button class="chat-toggle" id="chat-toggle" aria-label="Open AI Chat">
        <span class="chat-icon">💬</span>
        <span class="chat-icon-close">✕</span>
      </button>
      
      <div class="chat-container" id="chat-container">
        <div class="chat-header">
          <div class="chat-header-info">
            <span class="chat-avatar">🤖</span>
            <div>
              <strong>Trend Radar AI</strong>
              <span class="chat-status">Online</span>
            </div>
          </div>
          <button class="chat-clear" id="chat-clear" title="Clear chat">🗑️</button>
        </div>
        
        <div class="chat-messages" id="chat-messages">
          <div class="chat-message bot">
            <div class="message-content">
              👋 Hi! I'm Trend Radar AI. Ask me about trending topics, meme coins, crypto, or anything else!
            </div>
          </div>
        </div>
        
        <div class="chat-input-area">
          <input type="text" id="chat-input" placeholder="Ask about trends..." autocomplete="off" />
          <button id="chat-send" aria-label="Send message">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(widget);
    
    // Add styles
    const styles = document.createElement('style');
    styles.textContent = `
      #chat-widget {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      
      .chat-toggle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(108, 92, 231, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
      }
      
      .chat-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 25px rgba(108, 92, 231, 0.5);
      }
      
      .chat-icon, .chat-icon-close {
        font-size: 24px;
        transition: all 0.3s ease;
      }
      
      .chat-icon-close {
        display: none;
      }
      
      #chat-widget.open .chat-icon { display: none; }
      #chat-widget.open .chat-icon-close { display: block; }
      
      .chat-container {
        position: absolute;
        bottom: 70px;
        right: 0;
        width: 380px;
        max-width: calc(100vw - 40px);
        height: 500px;
        max-height: calc(100vh - 100px);
        background: #1a1a2e;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        display: none;
        flex-direction: column;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
      }
      
      #chat-widget.open .chat-container {
        display: flex;
        animation: slideUp 0.3s ease;
      }
      
      @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      
      .chat-header {
        padding: 16px;
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      
      .chat-header-info {
        display: flex;
        align-items: center;
        gap: 12px;
        color: white;
      }
      
      .chat-avatar {
        font-size: 28px;
      }
      
      .chat-status {
        font-size: 12px;
        opacity: 0.9;
        display: block;
      }
      
      .chat-clear {
        background: transparent;
        border: none;
        font-size: 18px;
        cursor: pointer;
        opacity: 0.7;
        transition: opacity 0.2s;
      }
      
      .chat-clear:hover {
        opacity: 1;
      }
      
      .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      
      .chat-message {
        max-width: 85%;
        animation: fadeIn 0.3s ease;
      }
      
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      
      .chat-message.user {
        align-self: flex-end;
      }
      
      .chat-message.bot {
        align-self: flex-start;
      }
      
      .message-content {
        padding: 12px 16px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.5;
      }
      
      .chat-message.user .message-content {
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        color: white;
        border-bottom-right-radius: 4px;
      }
      
      .chat-message.bot .message-content {
        background: #2d2d44;
        color: #e0e0e0;
        border-bottom-left-radius: 4px;
      }
      
      .chat-input-area {
        padding: 16px;
        display: flex;
        gap: 8px;
        background: #16162a;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
      }
      
      #chat-input {
        flex: 1;
        padding: 12px 16px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 24px;
        background: #1a1a2e;
        color: white;
        font-size: 14px;
        outline: none;
        transition: border-color 0.2s;
      }
      
      #chat-input:focus {
        border-color: #6c5ce7;
      }
      
      #chat-input::placeholder {
        color: #888;
      }
      
      #chat-send {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        transition: transform 0.2s;
      }
      
      #chat-send:hover {
        transform: scale(1.05);
      }
      
      #chat-send:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      
      .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
      }
      
      .typing-indicator span {
        width: 8px;
        height: 8px;
        background: #6c5ce7;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
      }
      
      .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
      .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
      
      @keyframes typing {
        0%, 100% { transform: translateY(0); opacity: 0.4; }
        50% { transform: translateY(-6px); opacity: 1; }
      }
      
      @media (max-width: 480px) {
        .chat-container {
          width: calc(100vw - 20px);
          right: -10px;
          height: calc(100vh - 100px);
        }
      }
    `;
    document.head.appendChild(styles);
  },
  
  bindEvents() {
    document.getElementById('chat-toggle').addEventListener('click', () => this.toggle());
    document.getElementById('chat-send').addEventListener('click', () => this.sendMessage());
    document.getElementById('chat-clear').addEventListener('click', () => this.clearChat());
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });
  },
  
  toggle() {
    this.isOpen = !this.isOpen;
    document.getElementById('chat-widget').classList.toggle('open', this.isOpen);
    if (this.isOpen) {
      document.getElementById('chat-input').focus();
    }
  },
  
  async sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    this.addMessage(message, 'user');
    this.showTyping();
    
    try {
      const response = await fetch(this.API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message,
          history: this.messages.slice(-10) // Last 10 messages for context
        })
      });
      
      if (!response.ok) throw new Error('Failed to get response');
      
      const data = await response.json();
      this.hideTyping();
      this.addMessage(data.reply, 'bot');
    } catch (error) {
      this.hideTyping();
      this.addMessage('Sorry, I encountered an error. Please try again later.', 'bot');
      console.error('Chat error:', error);
    }
  },
  
  addMessage(text, sender) {
    const messagesEl = document.getElementById('chat-messages');
    const messageEl = document.createElement('div');
    messageEl.className = `chat-message ${sender}`;
    messageEl.innerHTML = `<div class="message-content">${this.escapeHtml(text)}</div>`;
    messagesEl.appendChild(messageEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    this.messages.push({ role: sender, content: text });
    this.saveHistory();
  },
  
  showTyping() {
    const messagesEl = document.getElementById('chat-messages');
    const typingEl = document.createElement('div');
    typingEl.className = 'chat-message bot';
    typingEl.id = 'typing-indicator';
    typingEl.innerHTML = `
      <div class="message-content typing-indicator">
        <span></span><span></span><span></span>
      </div>
    `;
    messagesEl.appendChild(typingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  },
  
  hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
  },
  
  clearChat() {
    this.messages = [];
    localStorage.removeItem('trendradar_chat');
    document.getElementById('chat-messages').innerHTML = `
      <div class="chat-message bot">
        <div class="message-content">
          👋 Hi! I'm Trend Radar AI. Ask me about trending topics, meme coins, crypto, or anything else!
        </div>
      </div>
    `;
  },
  
  saveHistory() {
    localStorage.setItem('trendradar_chat', JSON.stringify(this.messages.slice(-20)));
  },
  
  loadHistory() {
    try {
      const saved = localStorage.getItem('trendradar_chat');
      if (saved) {
        this.messages = JSON.parse(saved);
        const messagesEl = document.getElementById('chat-messages');
        this.messages.forEach(msg => {
          if (msg.content) {
            const messageEl = document.createElement('div');
            messageEl.className = `chat-message ${msg.role}`;
            messageEl.innerHTML = `<div class="message-content">${this.escapeHtml(msg.content)}</div>`;
            messagesEl.appendChild(messageEl);
          }
        });
      }
    } catch (e) {
      console.error('Failed to load chat history:', e);
    }
  },
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => ChatWidget.init());
} else {
  ChatWidget.init();
}

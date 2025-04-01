class Chatbot {
  constructor(options = {}) {
    this.botId = options.botId || "default";
    this.apiEndpoint = options.apiEndpoint || "https://api.aispirelabs.com";
    this.backendEndpoint = "https://sara-admin.aispirelabs.com/api";
    this.sessionDuration = 3600000; // 1 hour in milliseconds
    this.defaultStyles = {
      name: "Chat Support",
      backgroundColor: "#ffffff",
      primaryColor: "#2563eb",
      primaryHoverColor: "#1d4ed8",
      senderTextColor: "#ffffff",
      senderBackgroundColor: "#2563eb",
      senderFont: "Inter, system-ui, -apple-system, sans-serif",
      receiverTextColor: "#1f2937",
      receiverBackgroundColor: "#f3f4f6",
      receiverFont: "Inter, system-ui, -apple-system, sans-serif",
      chatBackground: "#ffffff",
      welcomeMessage: "Hi! I'm here to help. How can I assist you today?",
      avatar_url:
        "https://media.istockphoto.com/id/1492548051/vector/chatbot-logo-icon.jpg?s=612x612&w=0&k=20&c=oh9mrvB70HTRt0FkZqOu9uIiiJFH9FaQWW3p4M6iNno=",
      waveRadius: "15px",
      pulseSize: "30px",
      bounceHeight: "25px",
      environment: "Beta",
      powered_by_message: "Powered by AISPIRELABS",
      powered_by_target_url: "https://aispirelabs.com",
      show_powered_by: true,
      logo_url: "https://aispirelabs.com/static/logo_white.png",

    };
    this.styles = { ...this.defaultStyles };
    this.isOpen = false;
    this.isMinimized = false;
    this.initialize();
  }

  async initialize() {
    await this.loadMarked();
    this.sessionId = await this.getOrCreateSessionId();
    await this.loadStyles();
    this.createChatbotHTML();
    this.attachEventListeners();
    this.injectStyles();
  }

  async loadMarked() {
    if (typeof marked === "undefined") {
      const script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/npm/marked/marked.min.js";
      script.async = true;
      await new Promise((resolve, reject) => {
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    }
  }

  formatMarkdown(text) {
  return marked.parse(text, {
    breaks: true,
    gfm: true,
  }).replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" ');
}


  getTimestamp() {
    return new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  async getOrCreateSessionId() {
    const storageKey = `chatbot_session_${this.botId}`;
    const sessionData = localStorage.getItem(storageKey);

    if (sessionData) {
      const { sessionId, timestamp } = JSON.parse(sessionData);
      const now = Date.now();

      if (now - timestamp < this.sessionDuration) {
        return sessionId;
      }
    }

    return this.createNewSession();
  }

  createNewSession() {
    const sessionId =
      "session-" +
      this.botId +
      "-" +
      Date.now() +
      "-" +
      Math.random().toString(36).substr(2, 9);
    const sessionData = {
      sessionId,
      timestamp: Date.now(),
    };

    localStorage.setItem(
      `chatbot_session_${this.botId}`,
      JSON.stringify(sessionData)
    );
    return sessionId;
  }

  checkAndRefreshSession() {
    const storageKey = `chatbot_session_${this.botId}`;
    const sessionData = JSON.parse(localStorage.getItem(storageKey));
    const now = Date.now();

    if (now - sessionData.timestamp >= this.sessionDuration) {
      return this.createNewSession();
    }
    return sessionData.sessionId;
  }

  async loadStyles() {
    try {
      const response = await fetch(
        `${this.backendEndpoint}/assistants/get-styles/${this.botId}/`
      );
      const customStyles = await response.json();
      this.styles = { ...this.defaultStyles, ...customStyles };
      console.log(this.styles);
    } catch (error) {
      console.warn("Failed to load custom styles, using defaults:", error);
    }
  }

  createChatbotHTML() {
    const chatbot = document.createElement("div");
    chatbot.className = "cb-chatbot";

    const envTag = this.styles.environment
      ? `<span class="cb-env-tag">${this.styles.environment}</span>`
      : "";
    const poweredBy = this.styles.show_powered_by
      ? `<div class="cb-powered-by">
             <a href="${this.styles.powered_by_target_url}" target="_blank" rel="noopener noreferrer">
               ${this.styles.powered_by_message} ❤️
             </a>
           </div>`
      : "";

    chatbot.innerHTML = `
        <div class="cb-chat-container">
          <div class="cb-chat-header">
            <div class="cb-chat-header-title">
              <div class="cb-avatar">
                <img src="${this.styles.avatar_url}" alt="Bot Avatar">
              </div>
              <div>
                <span class="cb-title">${this.styles.name}</span>
                <div class="cb-status-wrapper">
                  ${envTag}
                </div>
              </div>
            </div>
            <div class="cb-chat-header-buttons">
              <button class="cb-minimize-btn" aria-label="Minimize">
                <svg class="cb-minimize-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                <svg class="cb-maximize-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display: none;">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
              </button>
              <button class="cb-close-btn" aria-label="Close">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>
          <div class="cb-chat-body">
            <div class="cb-messages">
              <div class="cb-message cb-bot-message">
                <div class="cb-message-content">
                  <p>${this.styles.welcomeMessage}</p>
                  <span class="cb-timestamp">${this.getTimestamp()}</span>
                </div>
              </div>
            </div>
            <div class="cb-typing-indicator cb-hidden">
              <div class="cb-dot"></div>
              <div class="cb-dot"></div>
              <div class="cb-dot"></div>
            </div>
            <div class="cb-suggestions-wrapper">
              <div class="cb-suggestions"></div>
            </div>
            <form class="cb-chat-input">
              <input type="text" placeholder="Type your message...">
              <button type="submit" aria-label="Send message">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 2L11 13"></path>
                  <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                </svg>
              </button>
            </form>
            ${poweredBy}
          </div>
        </div>
        <button class="cb-chat-toggle" aria-label="Open chat">
          <div class="cb-icon-wrapper">
            <div class="cb-pulse-ring"></div>
            <div class="cb-default-icon">
              <img src=${this.styles.logo_url} alt="Chat Icon" class="cb-toggle-icon">

            </div>
          </div>
        </button>
      `;
    document.body.appendChild(chatbot);
  }

  attachEventListeners() {
    const container = document.querySelector(".cb-chatbot");
    const toggle = container.querySelector(".cb-chat-toggle");
    const closeBtn = container.querySelector(".cb-close-btn");
    const minimizeBtn = container.querySelector(".cb-minimize-btn");
    const form = container.querySelector(".cb-chat-input");

    toggle.addEventListener("click", () => this.toggleChat());
    closeBtn.addEventListener("click", () => this.toggleChat());
    minimizeBtn.addEventListener("click", () => this.toggleMinimize());
    form.addEventListener("submit", (e) => this.handleSubmit(e));

    container.addEventListener("click", (e) => {
      if (e.target.classList.contains("cb-suggestion")) {
        this.handleSuggestionClick(e.target.textContent);
      }
    });
  }

  async handleSubmit(e) {
    e.preventDefault();
    const input = e.target.querySelector("input");
    const message = input.value.trim();
    if (!message) return;

    this.sessionId = this.checkAndRefreshSession();
    this.addMessage(message, false);
    input.value = "";

    try {
      this.showTypingIndicator();
      const response = await fetch(`${this.apiEndpoint}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: message,
          bot_token: this.botId,
          session_id: this.sessionId,
        }),
      });
      const data = await response.json();
      this.hideTypingIndicator();
      this.addMessage(data.answer, true);
      if (data.questions) {
        this.showSuggestions(data.questions);
      }
    } catch (error) {
      console.error("Error:", error);
      this.hideTypingIndicator();
      this.addMessage(
        "Sorry, I encountered an error. Please try again later.",
        true
      );
    }
  }

  addMessage(text, isBot) {
    const messages = document.querySelector(".cb-messages");
    const messageDiv = document.createElement("div");
    messageDiv.className = `cb-message ${
      isBot ? "cb-bot-message" : "cb-user-message"
    }`;

    const formattedText = isBot ? this.formatMarkdown(text) : text;

    messageDiv.innerHTML = `
        <div class="cb-message-content">
          ${isBot ? formattedText : `<p>${formattedText}</p>`}
          <span class="cb-timestamp">${this.getTimestamp()}</span>
        </div>
      `;

    messages.appendChild(messageDiv);

    if (isBot) {
      // Wait for the DOM to update with the new message
      setTimeout(() => {
        const messageContent = messageDiv.querySelector(".cb-message-content");
        const lineHeight =
          parseFloat(window.getComputedStyle(messageContent).lineHeight) || 16; // Get line-height or default to 16px
        const scrollTarget = messageDiv.offsetTop - lineHeight * 6; // Offset for 3 lines of content

        messages.scrollTop = scrollTarget; // Scroll to show the first 3 lines
      }, 0);
    } else {
      // For user messages, scroll to the bottom as usual
      messages.scrollTop = messages.scrollHeight;
    }
  }

  showSuggestions(questions) {
    const suggestionsDiv = document.querySelector(".cb-suggestions");
    if (!questions || questions.length === 0) {
      suggestionsDiv.style.display = "none";
      return;
    }

    suggestionsDiv.style.display = "flex";
    suggestionsDiv.innerHTML = questions
      .map((q) => `<button class="cb-suggestion">${q}</button>`)
      .join("");
  }

  handleSuggestionClick(question) {
    const input = document.querySelector(".cb-chat-input input");
    input.value = question;
    input.form.dispatchEvent(new Event("submit"));
  }

  showTypingIndicator() {
    const indicator = document.querySelector(".cb-typing-indicator");
    indicator.classList.remove("cb-hidden");
  }

  hideTypingIndicator() {
    const indicator = document.querySelector(".cb-typing-indicator");
    indicator.classList.add("cb-hidden");
  }

  toggleChat() {
    const container = document.querySelector(".cb-chat-container");
    const toggle = document.querySelector(".cb-chat-toggle");
    this.isOpen = !this.isOpen;

    if (this.isOpen) {
      container.style.display = "flex";
      container.classList.add("cb-slide-in");
      toggle.classList.add("cb-hide");
    } else {
      container.classList.remove("cb-slide-in");
      container.classList.add("cb-slide-out");
      setTimeout(() => {
        container.style.display = "none";
        container.classList.remove("cb-slide-out");
        toggle.classList.remove("cb-hide");
      }, 300);
    }
  }

  toggleMinimize() {
    const container = document.querySelector(".cb-chat-container");
    const minimizeBtn = container.querySelector(".cb-minimize-btn");
    const minimizeIcon = minimizeBtn.querySelector(".cb-minimize-icon");
    const maximizeIcon = minimizeBtn.querySelector(".cb-maximize-icon");

    this.isMinimized = !this.isMinimized;
    container.classList.toggle("cb-minimized");

    if (this.isMinimized) {
      minimizeIcon.style.display = "none";
      maximizeIcon.style.display = "block";
    } else {
      minimizeIcon.style.display = "block";
      maximizeIcon.style.display = "none";
    }
  }

  injectStyles() {
    const style = document.createElement("style");
    style.textContent = `
        @keyframes cb-wave {
          0% { transform: rotate(-8deg) scale(1); }
          50% { transform: rotate(15deg) scale(1.2); }
          100% { transform: rotate(-8deg) scale(1); }
        }
  
        @keyframes cb-pulse {
          0% { 
            box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.6);
            transform: scale(1);
          }
          70% { 
            box-shadow: 0 0 0 ${this.styles.pulseSize} rgba(37, 99, 235, 0);
            transform: scale(1.1);
          }
          100% { 
            box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
            transform: scale(1);
          }
        }
  
        @keyframes cb-bounce {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-${this.styles.bounceHeight}) rotate(5deg); }
        }
  
        @keyframes cb-attention {
          0% { transform: scale(1) rotate(0deg); }
          10% { transform: scale(1.2) rotate(-15deg); }
          20% { transform: scale(1.2) rotate(15deg); }
          30% { transform: scale(1.2) rotate(-15deg); }
          40% { transform: scale(1.2) rotate(15deg); }
          50% { transform: scale(1) rotate(0deg); }
          100% { transform: scale(1) rotate(0deg); }
        }
  
        @keyframes cb-slideIn {
          from { transform: translateY(100px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
  
        @keyframes cb-slideOut {
          from { transform: translateY(0); opacity: 1; }
          to { transform: translateY(100px); opacity: 0; }
        }
  
        .cb-chatbot {
          position: fixed;
          bottom: 2rem;
          right: 2rem;
          z-index: 1000;
          font-family: ${this.styles.senderFont};
        }
  
        .cb-chat-container {
          width: 360px;
          height: 600px;
          background: ${this.styles.chatBackground};
          border-radius: 1rem;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
          margin-bottom: 1rem;
          display: none;
          flex-direction: column;
          overflow: hidden;
          transition: all 0.3s ease;
        }
  
        .cb-chat-container.cb-minimized {
          height: 72px;
        }
  
        .cb-chat-header {
          background-color: ${this.styles.primaryColor};
          padding: 1rem 1.25rem;
          color: #ffffff;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
  
        .cb-chat-header-title {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
  
        .cb-avatar {
          width: 2.5rem;
          height: 2.5rem;
          border-radius: 50%;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #ffffff;
        }
  
        .cb-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
  
        .cb-title-wrapper {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
  
        .cb-title {
          font-weight: 600;
          font-size: 1rem;
        }
  
        .cb-env-tag {
          background: rgba(255, 255, 255, 0.2);
          padding: 0.125rem 0.5rem;
          border-radius: 1rem;
          font-size: 0.75rem;
          font-weight: 500;
          color: #ffffff;
        }
  
        .cb-status {
          font-size: 0.75rem;
          opacity: 0.8;
        }
  
        .cb-status-wrapper {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding-top: 0.5rem;
        }
  
        .cb-chat-header-buttons {
          display: flex;
          gap: 0.5rem;
        }
  
        .cb-chat-header button {
          background: rgba(255, 255, 255, 0.1);
          border: none;
          color: #ffffff;
          padding: 0.5rem;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: all 0.2s;
        }
  
        .cb-chat-header button:hover {
          background: rgba(255, 255, 255, 0.2);
        }
  
        .cb-chat-body {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
  
        .cb-messages {
          flex: 1;
          overflow-y: auto;
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          scrollbar-width: thin;
          scrollbar-color: ${this.styles.primaryColor}40 transparent;
        }
  
        .cb-messages::-webkit-scrollbar {
          width: 6px;
        }
  
        .cb-messages::-webkit-scrollbar-track {
          background: transparent;
        }
  
        .cb-messages::-webkit-scrollbar-thumb {
          background-color: ${this.styles.primaryColor}40;
          border-radius: 3px;
          border: transparent;
        }
  
        .cb-message {
          max-width: 80%;
          margin: 0.5rem 0;
        }
  
        .cb-message-content {
          padding: 0.75rem 1rem;
          border-radius: 1rem;
          font-size: 0.9375rem;
          line-height: 1.4;
        }
  
        .cb-bot-message {
          align-self: flex-start;
        }
  
        .cb-bot-message .cb-message-content {
          background-color: ${this.styles.receiverBackgroundColor};
          color: ${this.styles.receiverTextColor};
          border-bottom-left-radius: 0.25rem;
        }
  
        .cb-user-message {
          align-self: flex-end;
        }
  
        .cb-user-message .cb-message-content {
          background-color: ${this.styles.senderBackgroundColor};
          color: ${this.styles.senderTextColor};
          border-bottom-right-radius: 0.25rem;
        }
  
        .cb-timestamp {
          font-size: 0.6875rem;
          opacity: 0.7;
          margin-top: 0.25rem;
          display: block;
        }
  
        .cb-typing-indicator {
          display: flex;
          gap: 0.375rem;
          padding: 1rem 1.25rem;
          align-items: center;
        }
  
        .cb-typing-indicator.cb-hidden {
          display: none;
        }
  
        .cb-dot {
          width: 0.5rem;
          height: 0.5rem;
          background: ${this.styles.primaryColor};
          border-radius: 50%;
          animation: cb-bounce 1.4s infinite;
        }
  
        .cb-dot:nth-child(2) { animation-delay: 0.2s; }
        .cb-dot:nth-child(3) { animation-delay: 0.4s; }
  
        .cb-suggestions-wrapper {
          max-height: 20%;
          overflow-y: auto;
          border-top: 1px solid #e5e7eb;
          scrollbar-width: thin;
          scrollbar-color: ${this.styles.primaryColor}40 transparent;
        }
  
        .cb-suggestions-wrapper::-webkit-scrollbar {
          width: 6px;
        }
  
        .cb-suggestions-wrapper::-webkit-scrollbar-track {
          background: transparent;
        }
  
        .cb-suggestions-wrapper::-webkit-scrollbar-thumb {
          background-color: ${this.styles.primaryColor}40;
          border-radius: 3px;
          border: transparent;
        }
  
        .cb-suggestions {
          padding: 0.75rem;
          display: none;
          flex-wrap: wrap;
          gap: 0.5rem;
          background: #ffffff;
        }
  
        .cb-suggestion {
          background: none;
          border: 1px solid ${this.styles.primaryColor};
          color: ${this.styles.primaryColor};
          padding: 0.5rem 1rem;
          border-radius: 1rem;
          cursor: pointer;
          font-size: 0.875rem;
          transition: all 0.2s;
          white-space: nowrap;
        }
  
        .cb-suggestion:hover {
          background: ${this.styles.primaryColor};
          color: #ffffff;
        }
  
        .cb-chat-input {
          padding: 0.5rem 0.75rem;
          background-color: white;
          display: flex;
          gap: 0.75rem;
          border-top: 1px solid #e5e7eb;
        }
  
        .cb-chat-input input {
          flex: 1;
          padding: 0.75rem 1rem;
          border: 1px solid #e5e7eb;
          border-radius: 0.75rem;
          outline: none;
          font-size: 0.9375rem;
          transition: all 0.2s;
        }
  
        .cb-chat-input input:focus {
          border-color: ${this.styles.primaryColor};
          box-shadow: 0 0 0 2px ${this.styles.primaryColor}15;
        }
  
        .cb-chat-input button {
          background-color: ${this.styles.primaryColor};
          color: #ffffff;
          border: none;
          width: 2.75rem;
          height: 2.75rem;
          border-radius: 0.75rem;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
        }
  
        .cb-chat-input button:hover {
          background-color: ${this.styles.primaryHoverColor};
          transform: scale(1.05);
        }
  
        .cb-powered-by {
          text-align: center;
          padding-bottom: 0.5rem;
          font-size: 0.75rem;
        }
  
        .cb-powered-by a {
          color: ${this.styles.primaryColor};
          text-decoration: none;
          transition: color 0.2s;
        }
  
        .cb-powered-by a:hover {
          color: ${this.styles.primaryHoverColor};
          text-decoration: underline;
        }
  
        .cb-chat-toggle {
          background-color: ${this.styles.primaryColor};
          color: #ffffff;
          border: none;
          width: 4rem;
          height: 4rem;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
          transition: all 0.3s ease;
          position: relative;
          overflow: visible;
        }
  
        .cb-icon-wrapper {
          width: 100%;
          height: 100%;
          animation: cb-wave 3s ease-in-out infinite;
          transform-origin: center;
          display: flex;
          align-items: center;
          justify-content: center;
        }
  
        .cb-default-icon {
          width: 100%;
          height: 100%;
          border-radius: 50%;
          overflow: hidden;
        }
  
        .cb-toggle-icon {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
  
        .cb-pulse-ring {
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          animation: cb-pulse 2s cubic-bezier(0.455, 0.03, 0.515, 0.955) infinite;
        }
  
        .cb-chat-toggle:hover .cb-icon-wrapper {
          animation: cb-attention 0.8s ease-in-out;
        }
  
        .cb-chat-toggle.cb-hide {
          transform: scale(0);
          opacity: 0;
        }
  
        .cb-slide-in {
          animation: cb-slideIn 0.3s ease forwards;
        }
  
        .cb-slide-out {
          animation: cb-slideOut 0.3s ease forwards;
        }
  
        .cb-bot-message .cb-message-content {
          overflow-wrap: break-word;
        }
  
        .cb-bot-message .cb-message-content h1,
        .cb-bot-message .cb-message-content h2,
        .cb-bot-message .cb-message-content h3,
        .cb-bot-message .cb-message-content h4,
        .cb-bot-message .cb-message-content h5,
        .cb-bot-message .cb-message-content h6 {
          margin-top: 1em;
          margin-bottom: 0.5em;
          font-weight: 600;
          line-height: 1.25;
        }
  
        .cb-bot-message .cb-message-content h1 { font-size: 1.5em; }
        .cb-bot-message .cb-message-content h2 { font-size: 1.25em; }
        .cb-bot-message .cb-message-content h3 { font-size: 1.125em; }
  
        .cb-bot-message .cb-message-content p {
          margin-bottom: 0.75em;
        }
  
        .cb-bot-message .cb-message-content ul,
        .cb-bot-message .cb-message-content ol {
          margin: 0.5em 0;
          padding-left: 1.5em;
        }
  
        .cb-bot-message .cb-message-content li {
          margin: 0.25em 0;
        }
  
        .cb-bot-message .cb-message-content code {
          background: rgba(0, 0, 0, 0.05);
          padding: 0.2em 0.4em;
          border-radius: 3px;
          font-size: 0.9em;
          font-family: monospace;
        }
  
        .cb-bot-message .cb-message-content pre {
          background: rgba(0, 0, 0, 0.05);
          padding: 1em;
          border-radius: 5px;
          overflow-x: auto;
          margin: 0.75em 0;
        }
  
        .cb-bot-message .cb-message-content pre code {
          background: none;
          padding: 0;
          font-size: 0.9em;
        }
  
        .cb-bot-message .cb-message-content a {
          color: ${this.styles.primaryColor};
          text-decoration: none;
        }
  
        .cb-bot-message .cb-message-content a:hover {
          text-decoration: underline;
        }
  
        .cb-bot-message .cb-message-content blockquote {
          border-left: 4px solid ${this.styles.primaryColor}40;
          margin: 0.75em 0;
          padding-left: 1em;
          color: rgba(0, 0, 0, 0.7);
        }
  
        .cb-bot-message .cb-message-content table {
          border-collapse: collapse;
          width: 100%;
          margin: 0.75em 0;
        }
  
        .cb-bot-message .cb-message-content table th,
        .cb-bot-message .cb-message-content table td {
          border: 1px solid #e5e7eb;
          padding: 0.5em;
          text-align: left;
        }
  
        .cb-bot-message .cb-message-content table th {
          background: rgba(0, 0, 0, 0.05);
          font-weight: 600;
        }
  
        .cb-bot-message .cb-message-content img {
          max-width: 100%;
          height: auto;
          border-radius: 5px;
          margin: 0.75em 0;
        }
  
        .cb-bot-message .cb-message-content hr {
          border: none;
          border-top: 1px solid #e5e7eb;
          margin: 1em 0;
        }
  
        @media (max-width: 
        @media (max-width: 768px) {
          .cb-chatbot {
            bottom: 1rem;
            right: 1rem;
          }
  
          .cb-chat-container {
            width: calc(100vw - 2rem);
            height: calc(100vh - 2rem);
            margin: 0;
            position: fixed;
            bottom: 1rem;
            right: 1rem;
          }
  
          .cb-chat-toggle {
            width: 3.5rem;
            height: 3.5rem;
          }
        }
  
        @media (max-width: 480px) {
          .cb-chatbot {
            bottom: 0;
            right: 0;
          }
  
          .cb-chat-container {
            width: 100vw;
            height: 100vh;
            border-radius: 0;
            margin: 0;
            position: fixed;
            bottom: 0;
            right: 0;
          }
  
          .cb-chat-toggle {
            width: 3rem;
            height: 3rem;
            bottom: 1rem;
            right: 1rem;
          }
        }
      `;
    document.head.appendChild(style);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = Chatbot;
} else {
  window.Chatbot = Chatbot;
}

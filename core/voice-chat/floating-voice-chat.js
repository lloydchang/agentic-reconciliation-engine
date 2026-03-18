/**
 * Floating Voice Chat Widget
 * Can be embedded on any page to provide voice chat functionality
 */

class FloatingVoiceChat {
    constructor(options = {}) {
        this.options = {
            position: 'bottom-right', // bottom-right, bottom-left, top-right, top-left
            primaryColor: '#3498db',
            apiUrl: '/api/v1/rag/query',
            voiceApiUrl: '/api/v1/voice',
            ...options
        };

        this.isOpen = false;
        this.messages = [];
        this.isVoiceEnabled = false;
        this.isRecording = false;
        this.isSpeaking = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;

        this.init();
    }

    init() {
        this.createWidget();
        this.initializeSpeechRecognition();
        this.loadVoiceSettings();
        this.setupEventListeners();
    }

    createWidget() {
        // Create main container
        this.container = document.createElement('div');
        this.container.id = 'floating-voice-chat';
        this.container.className = `fvc-container fvc-${this.options.position}`;
        
        // Create CSS styles
        this.createStyles();
        
        // Create widget HTML
        this.container.innerHTML = `
            <div class="fvc-chat-bubble" id="fvcChatBubble">
                <div class="fvc-bubble-icon">🎤</div>
                <div class="fvc-bubble-text">Voice Assistant</div>
            </div>
            
            <div class="fvc-chat-window" id="fvcChatWindow">
                <div class="fvc-header">
                    <div class="fvc-title">
                        <span>🎤</span>
                        <span>GitOps Voice Assistant</span>
                        <div class="fvc-voice-indicator" id="fvcVoiceIndicator"></div>
                    </div>
                    <div class="fvc-controls">
                        <button class="fvc-btn fvc-voice-toggle" id="fvcVoiceToggle" title="Toggle Voice">
                            🔊
                        </button>
                        <button class="fvc-btn fvc-settings-toggle" id="fvcSettingsToggle" title="Settings">
                            ⚙️
                        </button>
                        <button class="fvc-btn fvc-close" id="fvcClose" title="Close">
                            ✖️
                        </button>
                    </div>
                </div>
                
                <div class="fvc-messages" id="fvcMessages">
                    <div class="fvc-empty-state">
                        <div class="fvc-empty-icon">🎤</div>
                        <div class="fvc-empty-title">Voice Assistant Ready</div>
                        <div class="fvc-empty-text">Click the microphone or type your question about GitOps infrastructure</div>
                    </div>
                    <div class="fvc-typing-indicator" id="fvcTypingIndicator" style="display: none;">
                        <div class="fvc-typing-dots">
                            <div class="fvc-dot"></div>
                            <div class="fvc-dot"></div>
                            <div class="fvc-dot"></div>
                        </div>
                        <span>Thinking...</span>
                    </div>
                </div>
                
                <div class="fvc-voice-settings" id="fvcVoiceSettings" style="display: none;">
                    <div class="fvc-settings-grid">
                        <div class="fvc-setting">
                            <label>Voice</label>
                            <select id="fvcVoiceSelect">
                                <option value="default">Default</option>
                                <option value="female">Female</option>
                                <option value="male">Male</option>
                            </select>
                        </div>
                        <div class="fvc-setting">
                            <label>Speed</label>
                            <div class="fvc-slider-container">
                                <input type="range" id="fvcSpeedSlider" min="0.5" max="2" step="0.1" value="1">
                                <span id="fvcSpeedValue">1.0</span>
                            </div>
                        </div>
                        <div class="fvc-setting">
                            <label>Pitch</label>
                            <div class="fvc-slider-container">
                                <input type="range" id="fvcPitchSlider" min="0.5" max="2" step="0.1" value="1">
                                <span id="fvcPitchValue">1.0</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="fvc-input-area">
                    <div class="fvc-voice-controls">
                        <button class="fvc-voice-btn" id="fvcVoiceBtn" title="Start Voice Input">
                            🎤
                        </button>
                    </div>
                    <div class="fvc-text-input">
                        <textarea id="fvcMessageInput" placeholder="Ask about your GitOps infrastructure..." rows="1"></textarea>
                        <button class="fvc-send-btn" id="fvcSendBtn" disabled>
                            📤
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(this.container);
        
        // Get element references
        this.chatBubble = document.getElementById('fvcChatBubble');
        this.chatWindow = document.getElementById('fvcChatWindow');
        this.messagesContainer = document.getElementById('fvcMessages');
        this.messageInput = document.getElementById('fvcMessageInput');
        this.sendBtn = document.getElementById('fvcSendBtn');
        this.voiceBtn = document.getElementById('fvcVoiceBtn');
        this.voiceToggle = document.getElementById('fvcVoiceToggle');
        this.settingsToggle = document.getElementById('fvcSettingsToggle');
        this.closeBtn = document.getElementById('fvcClose');
        this.voiceSettings = document.getElementById('fvcVoiceSettings');
        this.voiceIndicator = document.getElementById('fvcVoiceIndicator');
        this.typingIndicator = document.getElementById('fvcTypingIndicator');
    }

    createStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .fvc-container {
                position: fixed;
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .fvc-bottom-right {
                bottom: 20px;
                right: 20px;
            }
            
            .fvc-bottom-left {
                bottom: 20px;
                left: 20px;
            }
            
            .fvc-top-right {
                top: 20px;
                right: 20px;
            }
            
            .fvc-top-left {
                top: 20px;
                left: 20px;
            }
            
            .fvc-chat-bubble {
                background: linear-gradient(135deg, ${this.options.primaryColor}, ${this.adjustColor(this.options.primaryColor, -20)});
                color: white;
                border-radius: 25px;
                padding: 12px 20px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                transition: all 0.3s ease;
                margin-bottom: 10px;
            }
            
            .fvc-chat-bubble:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 30px rgba(0, 0, 0, 0.3);
            }
            
            .fvc-bubble-icon {
                font-size: 1.2em;
            }
            
            .fvc-bubble-text {
                font-size: 0.9em;
                font-weight: 500;
            }
            
            .fvc-chat-window {
                width: 380px;
                height: 500px;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                display: none;
                flex-direction: column;
                overflow: hidden;
            }
            
            .fvc-chat-window.open {
                display: flex;
            }
            
            .fvc-header {
                background: linear-gradient(135deg, ${this.options.primaryColor}, ${this.adjustColor(this.options.primaryColor, -20)});
                color: white;
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .fvc-title {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                font-size: 0.95em;
            }
            
            .fvc-voice-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #e74c3c;
                animation: fvc-pulse 2s infinite;
            }
            
            .fvc-voice-indicator.active {
                background: #e74c3c;
            }
            
            .fvc-voice-indicator.speaking {
                background: #27ae60;
            }
            
            @keyframes fvc-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .fvc-controls {
                display: flex;
                gap: 8px;
            }
            
            .fvc-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.8em;
                transition: all 0.3s ease;
            }
            
            .fvc-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: scale(1.1);
            }
            
            .fvc-messages {
                flex: 1;
                padding: 15px;
                overflow-y: auto;
                background: #f8f9fa;
            }
            
            .fvc-empty-state {
                text-align: center;
                padding: 40px 20px;
                color: #666;
            }
            
            .fvc-empty-icon {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .fvc-empty-title {
                font-weight: 600;
                margin-bottom: 5px;
            }
            
            .fvc-empty-text {
                font-size: 0.85em;
                line-height: 1.4;
            }
            
            .fvc-typing-indicator {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px;
                background: white;
                border-radius: 10px;
                margin-bottom: 10px;
                border: 1px solid #e1e8ed;
            }
            
            .fvc-typing-dots {
                display: flex;
                gap: 4px;
            }
            
            .fvc-dot {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #666;
                animation: fvc-typing 1.4s infinite;
            }
            
            .fvc-dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .fvc-dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            @keyframes fvc-typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-6px); }
            }
            
            .fvc-message {
                margin-bottom: 15px;
                display: flex;
                align-items: flex-start;
                gap: 8px;
            }
            
            .fvc-message.user {
                justify-content: flex-end;
            }
            
            .fvc-message-content {
                max-width: 75%;
                padding: 10px 14px;
                border-radius: 15px;
                font-size: 0.9em;
                line-height: 1.4;
            }
            
            .fvc-message.user .fvc-message-content {
                background: ${this.options.primaryColor};
                color: white;
                border-bottom-right-radius: 6px;
            }
            
            .fvc-message.assistant .fvc-message-content {
                background: white;
                color: #333;
                border: 1px solid #e1e8ed;
                border-bottom-left-radius: 6px;
            }
            
            .fvc-message-time {
                font-size: 0.7em;
                opacity: 0.7;
                margin-top: 4px;
            }
            
            .fvc-voice-settings {
                padding: 15px;
                background: #f8f9fa;
                border-top: 1px solid #e1e8ed;
            }
            
            .fvc-settings-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                gap: 15px;
            }
            
            .fvc-setting {
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            
            .fvc-setting label {
                font-size: 0.8em;
                font-weight: 600;
                color: #333;
            }
            
            .fvc-setting select {
                padding: 4px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 0.8em;
            }
            
            .fvc-slider-container {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .fvc-slider-container input[type="range"] {
                flex: 1;
                height: 4px;
                border-radius: 2px;
                background: #ddd;
                outline: none;
                -webkit-appearance: none;
            }
            
            .fvc-slider-container input[type="range"]::-webkit-slider-thumb {
                -webkit-appearance: none;
                appearance: none;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: ${this.options.primaryColor};
                cursor: pointer;
            }
            
            .fvc-slider-container span {
                font-size: 0.8em;
                min-width: 25px;
            }
            
            .fvc-input-area {
                padding: 15px;
                background: white;
                border-top: 1px solid #e1e8ed;
            }
            
            .fvc-voice-controls {
                margin-bottom: 10px;
            }
            
            .fvc-voice-btn {
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.9em;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .fvc-voice-btn:hover {
                transform: translateY(-1px);
            }
            
            .fvc-voice-btn.recording {
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                animation: fvc-pulse 1s infinite;
            }
            
            .fvc-text-input {
                display: flex;
                gap: 8px;
                align-items: flex-end;
            }
            
            .fvc-text-input textarea {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 15px;
                resize: none;
                outline: none;
                font-size: 0.9em;
                min-height: 36px;
                max-height: 80px;
            }
            
            .fvc-text-input textarea:focus {
                border-color: ${this.options.primaryColor};
            }
            
            .fvc-send-btn {
                background: ${this.options.primaryColor};
                color: white;
                border: none;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }
            
            .fvc-send-btn:hover:not(:disabled) {
                transform: scale(1.1);
            }
            
            .fvc-send-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            @media (max-width: 480px) {
                .fvc-chat-window {
                    width: calc(100vw - 40px);
                    height: 60vh;
                }
                
                .fvc-bottom-right,
                .fvc-bottom-left {
                    bottom: 10px;
                    right: 10px;
                    left: 10px;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    setupEventListeners() {
        // Chat bubble click
        this.chatBubble.addEventListener('click', () => this.openChat());
        
        // Close button
        this.closeBtn.addEventListener('click', () => this.closeChat());
        
        // Voice toggle
        this.voiceToggle.addEventListener('click', () => this.toggleVoice());
        
        // Settings toggle
        this.settingsToggle.addEventListener('click', () => this.toggleSettings());
        
        // Voice button
        this.voiceBtn.addEventListener('click', () => this.toggleRecording());
        
        // Send button
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Input field
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.messageInput.addEventListener('input', () => {
            this.updateSendButton();
            this.autoResizeTextarea();
        });
        
        // Voice settings
        document.getElementById('fvcVoiceSelect').addEventListener('change', () => this.saveVoiceSettings());
        document.getElementById('fvcSpeedSlider').addEventListener('input', (e) => {
            document.getElementById('fvcSpeedValue').textContent = e.target.value;
            this.saveVoiceSettings();
        });
        document.getElementById('fvcPitchSlider').addEventListener('input', (e) => {
            document.getElementById('fvcPitchValue').textContent = e.target.value;
            this.saveVoiceSettings();
        });
    }

    initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                this.isRecording = true;
                this.updateVoiceIndicator('recording');
                this.voiceBtn.classList.add('recording');
                this.voiceBtn.innerHTML = '🔴 Recording...';
            };
            
            this.recognition.onresult = (event) => {
                const transcript = Array.from(event.results)
                    .map(result => result[0].transcript)
                    .join('');
                
                this.messageInput.value = transcript;
                this.updateSendButton();
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.stopRecording();
                this.showError('Speech recognition error: ' + event.error);
            };
            
            this.recognition.onend = () => {
                this.stopRecording();
                
                // Auto-send if we have a transcript
                if (this.messageInput.value.trim()) {
                    this.sendMessage();
                }
            };
        }
    }

    openChat() {
        this.isOpen = true;
        this.chatBubble.style.display = 'none';
        this.chatWindow.classList.add('open');
        this.messageInput.focus();
    }

    closeChat() {
        this.isOpen = false;
        this.chatBubble.style.display = 'flex';
        this.chatWindow.classList.remove('open');
    }

    toggleVoice() {
        this.isVoiceEnabled = !this.isVoiceEnabled;
        this.voiceToggle.style.opacity = this.isVoiceEnabled ? '1' : '0.5';
        
        if (this.isVoiceEnabled) {
            this.voiceToggle.style.background = 'rgba(255, 255, 255, 0.3)';
        } else {
            this.voiceToggle.style.background = 'rgba(255, 255, 255, 0.2)';
        }
    }

    toggleSettings() {
        this.voiceSettings.style.display = this.voiceSettings.style.display === 'none' ? 'block' : 'none';
    }

    toggleRecording() {
        if (!this.recognition) {
            this.showError('Speech recognition not supported in this browser');
            return;
        }

        if (this.isRecording) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    stopRecording() {
        this.isRecording = false;
        this.updateVoiceIndicator('idle');
        this.voiceBtn.classList.remove('recording');
        this.voiceBtn.innerHTML = '🎤';
    }

    updateVoiceIndicator(status) {
        this.voiceIndicator.className = 'fvc-voice-indicator';
        if (status === 'recording') {
            this.voiceIndicator.classList.add('active');
        } else if (status === 'speaking') {
            this.voiceIndicator.classList.add('speaking');
        }
    }

    updateSendButton() {
        this.sendBtn.disabled = !this.messageInput.value.trim() || this.isRecording;
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 80) + 'px';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.updateSendButton();

        this.showTypingIndicator();

        try {
            const response = await fetch(this.options.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    sources: ['documentation', 'kubernetes', 'dashboard', 'k8sgpt', 'flux', 'argocd']
                })
            });

            this.hideTypingIndicator();

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            this.addMessage(data.answer, 'assistant', data.sources);

            if (this.isVoiceEnabled && data.answer) {
                this.speakResponse(data.answer);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered an error processing your request. Please try again.', 'assistant');
            this.showError('Failed to get response: ' + error.message);
        }
    }

    addMessage(content, sender, sources = null) {
        const message = {
            id: Date.now(),
            content,
            sender,
            timestamp: new Date(),
            sources
        };

        this.messages.push(message);
        this.renderMessage(message);
    }

    renderMessage(message) {
        // Remove empty state if this is the first message
        if (this.messages.length === 1) {
            const emptyState = this.messagesContainer.querySelector('.fvc-empty-state');
            if (emptyState) {
                emptyState.remove();
            }
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `fvc-message ${message.sender}`;
        
        let sourcesHtml = '';
        if (message.sources && message.sources.length > 0) {
            sourcesHtml = `<div style="margin-top: 6px; font-size: 0.7em; opacity: 0.8;"><strong>Sources:</strong> ${message.sources.map(s => s.source || s).join(', ')}</div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="fvc-message-content">
                <div>${message.content}</div>
                ${sourcesHtml}
                <div class="fvc-message-time">${message.timestamp.toLocaleTimeString()}</div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    speakResponse(text) {
        if (!this.synthesis) return;

        this.synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        const speedSlider = document.getElementById('fvcSpeedSlider');
        const pitchSlider = document.getElementById('fvcPitchSlider');
        const voiceSelect = document.getElementById('fvcVoiceSelect');
        
        utterance.rate = parseFloat(speedSlider.value);
        utterance.pitch = parseFloat(pitchSlider.value);
        
        // Select voice
        const voices = this.synthesis.getVoices();
        const selectedVoice = voiceSelect.value;
        if (selectedVoice !== 'default' && voices.length > 0) {
            const voice = voices.find(v => v.name.toLowerCase().includes(selectedVoice));
            if (voice) {
                utterance.voice = voice;
            }
        }
        
        utterance.onstart = () => {
            this.isSpeaking = true;
            this.updateVoiceIndicator('speaking');
        };
        
        utterance.onend = () => {
            this.isSpeaking = false;
            this.updateVoiceIndicator('idle');
        };
        
        this.synthesis.speak(utterance);
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            background: rgba(231, 76, 60, 0.1);
            border: 1px solid rgba(231, 76, 60, 0.2);
            color: #e74c3c;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 0.8em;
        `;
        errorDiv.textContent = message;
        this.messagesContainer.appendChild(errorDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    loadVoiceSettings() {
        const settings = JSON.parse(localStorage.getItem('fvcVoiceSettings') || '{}');
        document.getElementById('fvcVoiceSelect').value = settings.voice || 'default';
        document.getElementById('fvcSpeedSlider').value = settings.speed || 1;
        document.getElementById('fvcPitchSlider').value = settings.pitch || 1;
        document.getElementById('fvcSpeedValue').textContent = settings.speed || '1.0';
        document.getElementById('fvcPitchValue').textContent = settings.pitch || '1.0';
    }

    saveVoiceSettings() {
        const settings = {
            voice: document.getElementById('fvcVoiceSelect').value,
            speed: document.getElementById('fvcSpeedSlider').value,
            pitch: document.getElementById('fvcPitchSlider').value
        };
        localStorage.setItem('fvcVoiceSettings', JSON.stringify(settings));
    }

    adjustColor(color, amount) {
        const num = parseInt(color.replace('#', ''), 16);
        const r = Math.max(0, Math.min(255, (num >> 16) + amount));
        const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + amount));
        const b = Math.max(0, Math.min(255, (num & 0x0000FF) + amount));
        return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0');
    }

    // Public methods
    show() {
        this.openChat();
    }

    hide() {
        this.closeChat();
    }

    destroy() {
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
    }
}

// Auto-initialize if script is loaded directly
if (typeof window !== 'undefined') {
    window.FloatingVoiceChat = FloatingVoiceChat;
    
    // Auto-initialize with default options if no existing instance
    if (!window.floatingVoiceChatInstance) {
        window.floatingVoiceChatInstance = new FloatingVoiceChat();
    }
}

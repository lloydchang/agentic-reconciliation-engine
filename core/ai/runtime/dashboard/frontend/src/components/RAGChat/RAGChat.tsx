import React, { useState, useRef, useEffect } from 'react';
import './RAGChat.css';
import VoiceChat from './VoiceChat';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    source: string;
    type: string;
    content: string;
  }>;
  metadata?: {
    processing_time?: number;
    sources_queried?: string[];
    context_count?: number;
  };
}

interface RAGResponse {
  answer: string;
  sources: Array<{
    content: string;
    source: string;
    type: string;
    metadata?: any;
  }>;
  model: string;
  metadata: {
    processing_time: number;
    sources_queried: string[];
    context_count: number;
    query: string;
  };
}

const RAGChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRAGEnabled, setIsRAGEnabled] = useState(false);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const availableSources = [
    { id: 'documentation', label: 'Documentation', description: 'Static knowledge base' },
    { id: 'sqlite_memory', label: 'Agent Memory', description: 'Conversation history' },
    { id: 'kubernetes', label: 'Kubernetes', description: 'Live cluster state' },
    { id: 'dashboard', label: 'Dashboard', description: 'System metrics' },
    { id: 'k8sgpt', label: 'K8sGPT', description: 'AI cluster analysis' },
    { id: 'flux', label: 'Flux CD', description: 'GitOps status' },
    { id: 'argocd', label: 'Argo CD', description: 'Application deployment' },
    { id: 'temporal', label: 'Temporal', description: 'Workflow history' },
  ];

  // Check RAG status on component mount
  useEffect(() => {
    checkRAGStatus();
  }, []);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const checkRAGStatus = async () => {
    try {
      const response = await fetch('/api/v1/rag/status');
      if (response.ok) {
        setIsRAGEnabled(true);
      }
    } catch (error) {
      console.log('RAG not available:', error);
      setIsRAGEnabled(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputValue,
          sources: selectedSources.length > 0 ? selectedSources : undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const ragResponse: RAGResponse = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: ragResponse.answer,
        sources: ragResponse.sources.map(source => ({
          source: source.source,
          type: source.type,
          content: source.content.substring(0, 200) + '...',
        })),
        metadata: ragResponse.metadata,
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Trigger text-to-speech for the response if voice is enabled
      if (voiceEnabled && ragResponse.answer) {
        setTimeout(() => {
          if (window.speakRAGResponse) {
            window.speakRAGResponse(ragResponse.answer);
          }
        }, 1000);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle voice transcript
  const handleVoiceTranscript = (transcript: string) => {
    setInputValue(transcript);
    // Auto-send voice transcript after a short delay
    setTimeout(() => {
      if (transcript.trim()) {
        handleSendMessage();
      }
    }, 500);
  };

  // Handle voice response
  const handleVoiceResponse = (audioData: ArrayBuffer) => {
    // In a real implementation, this would play the audio
    console.log('Received audio response:', audioData.byteLength, 'bytes');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleSource = (sourceId: string) => {
    setSelectedSources(prev => 
      prev.includes(sourceId)
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    );
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const toggleVoice = () => {
    setVoiceEnabled(!voiceEnabled);
  };

  if (!isRAGEnabled) {
    return (
      <div className="rag-chat disabled">
        <div className="disabled-message">
          <h3>🤖 RAG Chat Unavailable</h3>
          <p>The RAG chat service is currently not available.</p>
          <p>Please ensure the RAG backend is running and properly configured.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rag-chat">
      <div className="chat-header">
        <h3>🤖 GitOps RAG Assistant</h3>
        <div className="header-actions">
          <button 
            onClick={toggleVoice} 
            className={`voice-toggle-btn ${voiceEnabled ? 'enabled' : ''}`}
            title={voiceEnabled ? 'Disable voice' : 'Enable voice'}
          >
            {voiceEnabled ? '🔊' : '🔇'}
          </button>
          <button onClick={clearMessages} className="clear-btn">
            Clear Chat
          </button>
        </div>
      </div>

      <div className="sources-panel">
        <h4>Data Sources</h4>
        <div className="sources-grid">
          {availableSources.map(source => (
            <div
              key={source.id}
              className={`source-item ${selectedSources.includes(source.id) ? 'selected' : ''}`}
              onClick={() => toggleSource(source.id)}
            >
              <div className="source-checkbox">
                {selectedSources.includes(source.id) && '✓'}
              </div>
              <div className="source-info">
                <div className="source-name">{source.label}</div>
                <div className="source-description">{source.description}</div>
              </div>
            </div>
          ))}
        </div>
        {selectedSources.length === 0 && (
          <div className="source-hint">All sources will be used when none are selected</div>
        )}
      </div>

      <div className="messages-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h4>👋 Welcome to GitOps RAG Assistant!</h4>
              <p>I can help you with:</p>
              <ul>
                <li>🔍 Troubleshooting cluster issues</li>
                <li>📊 Analyzing system performance</li>
                <li>🚀 Deployment status and history</li>
                <li>📚 Documentation and procedures</li>
                <li>🤖 Agent memory and learned patterns</li>
              </ul>
              <p>Ask me anything about your Agentic Reconciliation Engine!</p>
            </div>
          )}
          
          {messages.map(message => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-content">
                <div className="message-text">{message.content}</div>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <h5>📚 Sources:</h5>
                    <div className="sources-list">
                      {message.sources.map((source, index) => (
                        <div key={index} className="source-item-small">
                          <span className="source-badge">{source.source}</span>
                          <span className="source-type">{source.type}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {message.metadata && (
                  <div className="message-metadata">
                    <span className="processing-time">
                      ⏱️ {message.metadata.processing_time}ms
                    </span>
                    {message.metadata.sources_queried && (
                      <span className="sources-queried">
                        🔍 {message.metadata.sources_queried.join(', ')}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="input-container">
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={voiceEnabled ? "Speak or type your question..." : "Ask about your Agentic Reconciliation Engine..."}
            disabled={isLoading}
            className="message-input"
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
            className="send-button"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
      </div>

      {voiceEnabled && (
        <VoiceChat
          onTranscript={handleVoiceTranscript}
          onAudioResponse={handleVoiceResponse}
          isProcessing={isLoading}
        />
      )}
    </div>
  );
};

export default RAGChat;

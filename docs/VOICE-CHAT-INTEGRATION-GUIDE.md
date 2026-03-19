# 🎤 Voice Chat Integration Guide

## Overview

This guide explains how to integrate voice chat capabilities throughout the Agentic Reconciliation Engine. The voice assistant provides natural language interaction with your infrastructure using speech-to-text and text-to-speech technologies.

## 🚀 Quick Start

### 1. Standalone Voice Chatbot
Access the dedicated voice chat interface directly:
```
http://localhost:8080/voice-chatbot.html
```

### 2. Main Dashboard Integration
The voice assistant is integrated into the main dashboard:
```
http://localhost:8080/dashboard-index.html
```
Click the "🎤 Voice Assistant" button in the System Controls section.

### 3. React Dashboard
The React dashboard includes voice chat as a separate view:
```
http://localhost:8080/
```
Navigate between Dashboard and Voice Assistant using the header navigation.

### 4. Floating Widget
Add the floating voice chat widget to any page:
```html
<script src="/floating-voice-chat.js"></script>
```

## 📁 Integration Points

### 1. **Standalone Voice Chatbot** (`voice-chatbot.html`)
- **Purpose**: Dedicated voice-first interface
- **Features**: Complete voice chat UI with settings
- **Use Case**: Primary voice interaction interface
- **Access**: Direct URL or bookmark

### 2. **Main Dashboard** (`dashboard-index.html`)
- **Purpose**: Integration with existing dashboard
- **Features**: Voice chat card with controls
- **Use Case**: Quick access from system controls
- **Access**: System Controls → Voice Assistant button

### 3. **React Dashboard** (`core/ai/runtime/dashboard/frontend/`)
- **Purpose**: Modern React interface
- **Features**: Navigation between dashboard and voice chat
- **Use Case**: Seamless integration with React components
- **Access**: Header navigation toggle

### 4. **Backstage Plugin** (`core/workspace/repo/ai-agents/frontend/`)
- **Purpose**: Integration with Backstage platform
- **Features**: Voice controls in RAG AI plugin
- **Use Case**: Enterprise catalog integration
- **Access**: RAG AI Assistant page

### 5. **Floating Widget** (`floating-voice-chat.js`)
- **Purpose**: Universal embeddable widget
- **Features**: Works on any page
- **Use Case**: Add voice to existing interfaces
- **Access**: Script inclusion

## 🔧 Technical Implementation

### Backend APIs

#### Voice Service Endpoints
```bash
# Speech-to-text
POST /api/v1/voice/speech-to-text
Content-Type: multipart/form-data

# Text-to-speech  
POST /api/v1/voice/text-to-speech
Content-Type: application/json

# Available voices
GET /api/v1/voice/voices

# Voice service status
GET /api/v1/voice/status
```

#### RAG API Endpoint
```bash
# RAG query with voice support
POST /api/v1/rag/query
Content-Type: application/json
{
  "query": "string",
  "sources": ["documentation", "kubernetes", "dashboard", "k8sgpt", "flux", "argocd"]
}
```

### Frontend Components

#### VoiceChat Component
```typescript
interface VoiceChatProps {
  onTranscript: (transcript: string) => void;
  onAudioResponse: (audioData: ArrayBuffer) => void;
  isProcessing: boolean;
}
```

#### Voice Settings
```typescript
interface VoiceSettings {
  voice: 'default' | 'female' | 'male';
  speed: number; // 0.5 - 2.0
  pitch: number; // 0.5 - 2.0  
  language: 'en-US' | 'en-GB' | 'es-ES' | 'fr-FR';
}
```

## 🎨 UI/UX Features

### Voice Controls
- **Microphone Button**: Toggle speech recognition
- **Speaker Button**: Enable/disable text-to-speech
- **Settings Panel**: Voice customization options
- **Visual Indicators**: Recording/speaking status

### Voice Settings
- **Voice Selection**: Choose between male/female voices
- **Speed Control**: Adjust speaking rate (0.5x - 2.0x)
- **Pitch Control**: Modify voice pitch (0.5 - 2.0)
- **Language Support**: Multiple language options

### Real-time Feedback
- **Recording Indicator**: Visual feedback during speech input
- **Volume Meters**: Audio level visualization
- **Typing Indicators**: Show when AI is processing
- **Error Handling**: Graceful fallbacks and notifications

## 🌐 Browser Compatibility

### Supported Browsers
- ✅ Chrome 25+
- ✅ Firefox 44+
- ✅ Safari 14.1+
- ✅ Edge 79+

### Required APIs
- **Web Speech API**: Speech recognition and synthesis
- **Web Audio API**: Audio processing
- **MediaRecorder API**: Audio capture
- **Fetch API**: HTTP requests

### Fallback Support
- **No Speech Recognition**: Text input still available
- **No Speech Synthesis**: Silent text responses
- **No Audio APIs**: Basic chat functionality

## 🔗 Integration Examples

### Example 1: Add to Custom Page
```html
<!DOCTYPE html>
<html>
<head>
    <title>My Dashboard</title>
</head>
<body>
    <h1>My Infrastructure Dashboard</h1>
    
    <!-- Existing content -->
    <div class="dashboard-content">
        <!-- Your dashboard components -->
    </div>
    
    <!-- Voice Chat Widget -->
    <script src="/floating-voice-chat.js"></script>
    <script>
        // Customize widget appearance
        const voiceChat = new FloatingVoiceChat({
            position: 'bottom-right',
            primaryColor: '#3498db',
            apiUrl: '/api/v1/rag/query'
        });
    </script>
</body>
</html>
```

### Example 2: React Component Integration
```typescript
import React, { useState } from 'react';
import VoiceChat from './components/VoiceChat/VoiceChat';

const MyDashboard = () => {
  const [voiceEnabled, setVoiceEnabled] = useState(false);

  const handleVoiceTranscript = (transcript: string) => {
    // Process voice transcript
    console.log('Voice input:', transcript);
  };

  const handleVoiceResponse = (audioData: ArrayBuffer) => {
    // Play audio response
    console.log('Audio response:', audioData.byteLength, 'bytes');
  };

  return (
    <div className="dashboard">
      <h1>My Dashboard</h1>
      
      {/* Your dashboard content */}
      
      {/* Voice Chat Integration */}
      {voiceEnabled && (
        <VoiceChat
          onTranscript={handleVoiceTranscript}
          onAudioResponse={handleVoiceResponse}
          isProcessing={false}
        />
      )}
      
      <button onClick={() => setVoiceEnabled(!voiceEnabled)}>
        {voiceEnabled ? 'Disable Voice' : 'Enable Voice'}
      </button>
    </div>
  );
};
```

### Example 3: Backend Integration
```go
// main.go - Voice service initialization
func main() {
    // ... existing setup
    
    // Initialize voice handler
    voiceHandler := api.NewVoiceHandler("/tmp/voice-uploads")
    
    // Register voice routes
    voiceHandler.RegisterVoiceRoutes(router)
    
    // Initialize RAG service with voice support
    ragService := rag.NewRAGService(db, qwenClient)
    ragHandler := api.NewRAGHandler(ragService)
    
    // ... start server
}
```

## 🚀 Deployment Configuration

### Environment Variables
```yaml
# Voice Chat Configuration
VOICE_ENABLED: "true"
VOICE_UPLOAD_DIR: "/tmp/voice-uploads"
SPEECH_TO_TEXT_PROVIDER: "browser"  # browser, google, azure, aws, openai
TEXT_TO_SPEECH_PROVIDER: "browser"   # browser, google, azure, aws, openai

# RAG Configuration
RAG_ENABLED: "true"
QWEN_LLAMACPP_URL: "http://localhost:8080"
QWEN_MODEL: "qwen2.5:0.5b"
```

### Kubernetes Deployment
```yaml
# dashboard-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dashboard
spec:
  template:
    spec:
      containers:
      - name: dashboard
        env:
        - name: VOICE_ENABLED
          value: "true"
        - name: VOICE_UPLOAD_DIR
          value: "/tmp/voice-uploads"
        volumeMounts:
        - name: voice-uploads
          mountPath: /tmp/voice-uploads
      volumes:
      - name: voice-uploads
        emptyDir: {}
```

## 🔍 Troubleshooting

### Common Issues

#### Speech Recognition Not Working
```bash
# Check browser support
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  console.log('Speech recognition supported');
} else {
  console.log('Speech recognition not supported');
}
```

#### Audio Playback Issues
```bash
# Check speech synthesis
if ('speechSynthesis' in window) {
  console.log('Speech synthesis supported');
} else {
  console.log('Speech synthesis not supported');
}
```

#### API Connection Errors
```bash
# Check API endpoints
curl -X GET http://localhost:8080/api/v1/voice/status
curl -X POST http://localhost:8080/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "sources": ["documentation"]}'
```

### Debug Mode
```javascript
// Enable debug logging
window.FloatingVoiceChat.debug = true;

// Check voice chat instance
console.log(window.floatingVoiceChatInstance);
```

## 📚 API Reference

### VoiceChat Class
```typescript
class FloatingVoiceChat {
  constructor(options: VoiceChatOptions);
  
  // Public methods
  show(): void;
  hide(): void;
  destroy(): void;
  
  // Events
  onTranscript: (transcript: string) => void;
  onResponse: (response: string) => void;
  onError: (error: string) => void;
}

interface VoiceChatOptions {
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  primaryColor?: string;
  apiUrl?: string;
  voiceApiUrl?: string;
}
```

### Voice Handler API
```go
type VoiceHandler struct {
    uploadDir string
}

func NewVoiceHandler(uploadDir string) *VoiceHandler
func (h *VoiceHandler) RegisterVoiceRoutes(router *gin.Engine)
func (h *VoiceHandler) HandleSpeechToText(c *gin.Context)
func (h *VoiceHandler) HandleTextToSpeech(c *gin.Context)
func (h *VoiceHandler) HandleGetVoices(c *gin.Context)
func (h *VoiceHandler) HandleVoiceStatus(c *gin.Context)
```

## 🎯 Best Practices

### Performance Optimization
- **Lazy Loading**: Load voice APIs only when needed
- **Caching**: Cache voice responses and settings
- **Compression**: Compress audio data for transmission
- **Debouncing**: Debounce voice input events

### Security Considerations
- **Input Validation**: Validate all voice transcripts
- **Audio Sanitization**: Sanitize uploaded audio files
- **Rate Limiting**: Limit voice API requests
- **Access Control**: Restrict voice API access

### Accessibility
- **Keyboard Navigation**: Support keyboard shortcuts
- **Screen Reader**: Compatible with screen readers
- **Visual Indicators**: Clear visual feedback
- **Alternative Input**: Text input fallback

## 🔄 Future Enhancements

### Planned Features
- **Multi-language Support**: Extended language options
- **Voice Profiles**: Personalized voice settings
- **Custom Voices**: Upload custom voice models
- **Real-time Translation**: Live translation capabilities

### Integration Opportunities
- **Slack Bot**: Voice commands in Slack
- **Discord Bot**: Voice interaction in Discord
- **Mobile Apps**: Native mobile voice support
- **IoT Devices**: Voice control for infrastructure

## 📞 Support

### Documentation
- **API Docs**: `/docs/api/voice-api.md`
- **Component Docs**: `/docs/components/voice-chat.md`
- **Integration Examples**: `/examples/voice-integration/`

### Community
- **Issues**: Report bugs on GitHub
- **Discussions**: Feature requests and ideas
- **Contributions**: Pull requests welcome

---

**This voice chat integration brings natural language interaction to your Agentic Reconciliation Engine, making it more accessible and user-friendly for all users.** 🎤🚀

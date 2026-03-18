import React, { useState, useRef, useEffect, useCallback } from 'react';
import './VoiceChat.css';

// Type declaration for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: ((event: any) => void) | null;
}

interface VoiceChatProps {
  onTranscript: (text: string) => void;
  onAudioResponse: (audioData: ArrayBuffer) => void;
  isProcessing?: boolean;
}

const VoiceChat: React.FC<VoiceChatProps> = ({ 
  onTranscript, 
  onAudioResponse, 
  isProcessing = false 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [volume, setVolume] = useState(0);
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [speechRate, setSpeechRate] = useState(1.0);
  const [speechPitch, setSpeechPitch] = useState(1.0);
  const [supportedVoices, setSupportedVoices] = useState<SpeechSynthesisVoice[]>([]);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Initialize speech synthesis
  useEffect(() => {
    const updateVoices = () => {
      const voices = speechSynthesis.getVoices();
      setSupportedVoices(voices);
      
      // Select a default English voice
      const englishVoice = voices.find(voice => 
        voice.lang.startsWith('en') && voice.name.includes('Natural')
      ) || voices.find(voice => voice.lang.startsWith('en')) || voices[0];
      
      if (englishVoice) {
        setSelectedVoice(englishVoice.name);
      }
    };

    updateVoices();
    speechSynthesis.onvoiceschanged = updateVoices;

    return () => {
      speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        console.log('Speech recognition started');
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript.trim()) {
          onTranscript(finalTranscript.trim());
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        console.log('Speech recognition ended');
      };

      recognitionRef.current = recognition;
    }
  }, [onTranscript]);

  // Initialize audio context and analyser
  const initializeAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      return stream;
    } catch (error) {
      console.error('Error accessing microphone:', error);
      throw error;
    }
  };

  // Update volume meter
  const updateVolume = useCallback(() => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
    setVolume(average / 255);
    
    animationFrameRef.current = requestAnimationFrame(updateVolume);
  }, []);

  // Start recording
  const startRecording = async () => {
    try {
      const stream = await initializeAudio();
      
      // Start speech recognition if available
      if (recognitionRef.current && !isListening) {
        recognitionRef.current.start();
      }
      
      // Setup media recorder for audio capture
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      const audioChunks: Blob[] = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const audioData = await audioBlob.arrayBuffer();
        
        // Send audio to backend for processing
        await processAudioInput(audioData);
      };
      
      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      
      // Start volume monitoring
      updateVolume();
      
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    setIsRecording(false);
    setVolume(0);
    
    // Clean up audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  // Process audio input (send to backend for speech-to-text)
  const processAudioInput = async (audioData: ArrayBuffer) => {
    try {
      // In a real implementation, send to backend for speech-to-text
      console.log('Processing audio input:', audioData.byteLength, 'bytes');
      
      // For now, we'll rely on the browser's speech recognition
      // This would be where you'd send to a custom speech-to-text service
    } catch (error) {
      console.error('Error processing audio:', error);
    }
  };

  // Text-to-speech function
  const speak = async (text: string) => {
    if (!text.trim()) return;
    
    try {
      setIsSpeaking(true);
      
      // Cancel any ongoing speech
      speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = speechRate;
      utterance.pitch = speechPitch;
      
      // Set selected voice
      const voice = supportedVoices.find(v => v.name === selectedVoice);
      if (voice) {
        utterance.voice = voice;
      }
      
      utterance.onend = () => {
        setIsSpeaking(false);
      };
      
      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        setIsSpeaking(false);
      };
      
      speechSynthesis.speak(utterance);
      
    } catch (error) {
      console.error('Error speaking text:', error);
      setIsSpeaking(false);
    }
  };

  // Expose speak function to parent
  useEffect(() => {
    // This would be called by parent component when RAG response is ready
    window.speakRAGResponse = speak;
    
    return () => {
      delete (window as any).speakRAGResponse;
    };
  }, [speak]);

  // Toggle recording
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="voice-chat">
      <div className="voice-controls">
        <div className="microphone-section">
          <button
            className={`mic-button ${isRecording ? 'recording' : ''} ${isListening ? 'listening' : ''}`}
            onClick={toggleRecording}
            disabled={isProcessing}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? '🔴' : '🎤'}
          </button>
          
          {isListening && (
            <div className="listening-indicator">
              <div className="pulse"></div>
              <span>Listening...</span>
            </div>
          )}
          
          {isRecording && (
            <div className="volume-meter">
              <div 
                className="volume-bar" 
                style={{ width: `${volume * 100}%` }}
              ></div>
            </div>
          )}
        </div>

        <div className="speaker-section">
          <button
            className={`speaker-button ${isSpeaking ? 'speaking' : ''}`}
            disabled={isSpeaking}
            title="Text-to-speech settings"
          >
            🔊
          </button>
          
          {isSpeaking && (
            <div className="speaking-indicator">
              <div className="wave"></div>
              <span>Speaking...</span>
            </div>
          )}
        </div>
      </div>

      <div className="voice-settings">
        <div className="setting-group">
          <label htmlFor="voice-select">Voice:</label>
          <select
            id="voice-select"
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            className="voice-select"
          >
            {supportedVoices.map((voice, index) => (
              <option key={index} value={voice.name}>
                {voice.name} ({voice.lang})
              </option>
            ))}
          </select>
        </div>

        <div className="setting-group">
          <label htmlFor="speech-rate">Speed:</label>
          <input
            id="speech-rate"
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={speechRate}
            onChange={(e) => setSpeechRate(parseFloat(e.target.value))}
            className="speech-slider"
          />
          <span>{speechRate.toFixed(1)}x</span>
        </div>

        <div className="setting-group">
          <label htmlFor="speech-pitch">Pitch:</label>
          <input
            id="speech-pitch"
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={speechPitch}
            onChange={(e) => setSpeechPitch(parseFloat(e.target.value))}
            className="speech-slider"
          />
          <span>{speechPitch.toFixed(1)}</span>
        </div>
      </div>

      <div className="voice-status">
        <div className="status-item">
          <span className="status-label">Microphone:</span>
          <span className={`status-value ${isRecording ? 'active' : 'inactive'}`}>
            {isRecording ? 'Recording' : 'Idle'}
          </span>
        </div>
        <div className="status-item">
          <span className="status-label">Speaker:</span>
          <span className={`status-value ${isSpeaking ? 'active' : 'inactive'}`}>
            {isSpeaking ? 'Speaking' : 'Idle'}
          </span>
        </div>
      </div>
    </div>
  );
};

// Extend window interface for global function
declare global {
  interface Window {
    speakRAGResponse?: (text: string) => void;
  }
}

export default VoiceChat;

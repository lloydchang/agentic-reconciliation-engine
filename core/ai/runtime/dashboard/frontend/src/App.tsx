import React, { useEffect, useState } from 'react';
import './App.css';
import Dashboard from './components/Dashboard/Dashboard';
import RAGChat from './components/RAGChat/RAGChat';
import { WebSocketService } from './services/websocket';
import ApiService from './services/api';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [activeView, setActiveView] = useState<'dashboard' | 'chat'>('dashboard');
  // const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    // Initialize WebSocket connection
    const wsService = new WebSocketService();
    wsService.connect();
    
    wsService.on('connect', () => {
      setIsConnected(true);
    });

    wsService.on('disconnect', () => {
      setIsConnected(false);
    });

    // Fetch initial system status
    const fetchSystemStatus = async () => {
      try {
        const api = new ApiService();
        const status = await api.getSystemStatus();
        // setSystemStatus(status);
        console.log('System status:', status);
      } catch (error) {
        console.error('Failed to fetch system status:', error);
      }
    };

    fetchSystemStatus();

    return () => {
      wsService.disconnect();
    };
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>🤖 Agents Control Center</h1>
          <div className="header-nav">
            <button 
              className={`nav-btn ${activeView === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveView('dashboard')}
            >
              📊 Dashboard
            </button>
            <button 
              className={`nav-btn ${activeView === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveView('chat')}
            >
              🎤 Voice Assistant
            </button>
          </div>
          <div className="status-indicator">
            <div className={`status-dot ${isConnected ? 'online' : 'offline'}`}></div>
            <span>System {isConnected ? 'Online' : 'Offline'}</span>
          </div>
        </div>
      </header>
      <main className="App-main">
        {activeView === 'dashboard' ? <Dashboard /> : <RAGChat />}
      </main>
    </div>
  );
}

export default App;

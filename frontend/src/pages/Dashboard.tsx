import React from 'react';
import { VoiceOrb } from '../components/VoiceOrb';
import { ConversationPanel } from '../components/ConversationPanel';
import { useVoiceAgent } from '../hooks/useVoiceAgent';
import { Mic, MicOff, Trash2, Settings, Activity } from 'lucide-react';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const websocketUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/voice';
  
  const {
    state,
    messages,
    isConnected,
    isRecording,
    startConversation,
    stopConversation,
    clearConversation
  } = useVoiceAgent(websocketUrl);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="brand">
          <Activity className="brand-icon" />
          <h1>VoxAI</h1>
        </div>
        <div className="header-actions">
          <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          <button className="icon-button"><Settings size={20} /></button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="left-panel">
          <div className="orb-section">
            <VoiceOrb 
              state={state} 
              onClick={isRecording ? stopConversation : startConversation} 
            />
          </div>
          
          <div className="controls-section">
            <button 
              className={`control-button ${isRecording ? 'active' : ''}`}
              onClick={isRecording ? stopConversation : startConversation}
            >
              {isRecording ? <Mic size={24} /> : <MicOff size={24} />}
              <span>{isRecording ? 'Stop Listening' : 'Start Listening'}</span>
            </button>
            <button className="control-button secondary" onClick={clearConversation}>
              <Trash2 size={24} />
              <span>Clear</span>
            </button>
          </div>
        </div>

        <div className="right-panel">
          <ConversationPanel messages={messages} />
        </div>
      </main>
    </div>
  );
};

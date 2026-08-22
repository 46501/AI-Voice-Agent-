import React, { useState } from 'react';
import { VoiceOrb } from '../components/VoiceOrb';
import { ConversationPanel } from '../components/ConversationPanel';
import { Sidebar } from '../components/Sidebar';
import { DeveloperPanel } from '../components/DeveloperPanel';
import { useVoiceAgent } from '../hooks/useVoiceAgent';
import { Mic, MicOff, Trash2, Settings, Activity, Menu } from 'lucide-react';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const websocketUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/voice';
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDevPanelOpen, setIsDevPanelOpen] = useState(false);
  
  // Hardcoded for now until backend conversation sync is implemented on frontend
  const conversations: any[] = []; 
  
  const {
    state,
    messages,
    latencyMetrics,
    errorMessage,
    isConnected,
    isRecording,
    startConversation,
    stopConversation,
    clearConversation
  } = useVoiceAgent(websocketUrl);

  const handleStart = () => {
    startConversation();
  };

  return (
    <div className="dashboard">
      <Sidebar 
        isOpen={isSidebarOpen} 
        setIsOpen={setIsSidebarOpen}
        conversations={conversations}
        activeConversationId={null}
        onSelectConversation={(id) => console.log('Selected', id)}
        onNewConversation={clearConversation}
      />
      <DeveloperPanel 
        state={state}
        metrics={latencyMetrics}
        isConnected={isConnected}
        isVisible={isDevPanelOpen}
        toggleVisibility={() => setIsDevPanelOpen(!isDevPanelOpen)}
      />

      <div className={`main-content ${isSidebarOpen ? 'sidebar-open' : ''}`}>
        <header className="dashboard-header">
          <div className="brand">
            <button className="icon-button menu-btn" onClick={() => setIsSidebarOpen(true)}>
              <Menu size={24} />
            </button>
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
                onClick={isRecording ? stopConversation : handleStart} 
              />
            </div>
            
            {errorMessage && (
              <div className="error-banner" style={{
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                color: '#ef4444',
                padding: '12px 16px',
                borderRadius: '8px',
                marginBottom: '20px',
                textAlign: 'center',
                fontWeight: 500,
                border: '1px solid rgba(239, 68, 68, 0.2)'
              }}>
                {errorMessage}
              </div>
            )}
            
            <div className="controls-section">
              <button 
                className={`control-button ${isRecording ? 'active' : ''}`}
                onClick={isRecording ? stopConversation : handleStart}
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
    </div>
  );
};

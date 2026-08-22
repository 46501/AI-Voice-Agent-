import React from 'react';
import type { AgentState, LatencyMetrics } from '../types/voice';
import './DeveloperPanel.css';

interface DeveloperPanelProps {
  state: AgentState;
  metrics: LatencyMetrics;
  isConnected: boolean;
  isVisible: boolean;
  toggleVisibility: () => void;
}

export const DeveloperPanel: React.FC<DeveloperPanelProps> = ({ 
  state, metrics, isConnected, isVisible, toggleVisibility 
}) => {
  if (!isVisible) {
    return (
      <button className="dev-toggle-btn" onClick={toggleVisibility}>
        {'<>'}
      </button>
    );
  }

  return (
    <div className="developer-panel">
      <div className="dev-header">
        <h3>Developer View</h3>
        <button onClick={toggleVisibility}>X</button>
      </div>
      
      <div className="dev-section">
        <h4>System Status</h4>
        <div className="dev-stat">
          <span>WebSocket:</span>
          <span className={isConnected ? 'status-ok' : 'status-err'}>
            {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
        </div>
        <div className="dev-stat">
          <span>Agent State:</span>
          <span className={`state-badge ${state}`}>{state.toUpperCase()}</span>
        </div>
      </div>

      <div className="dev-section">
        <h4>Latest Turn Latency</h4>
        <div className="dev-stat">
          <span>STT Duration:</span>
          <span>{metrics.stt_ms ? `${metrics.stt_ms}ms` : '--'}</span>
        </div>
        <div className="dev-stat">
          <span>LLM First Token:</span>
          <span>{metrics.llm_first_token_ms ? `${metrics.llm_first_token_ms}ms` : '--'}</span>
        </div>
        <div className="dev-stat">
          <span>TTS Synthesis:</span>
          <span>{metrics.tts_ms ? `${metrics.tts_ms}ms` : '--'}</span>
        </div>
        <div className="dev-stat total-latency">
          <span>First Audio (TTFB):</span>
          <span>{metrics.first_audio_ms ? `${metrics.first_audio_ms}ms` : '--'}</span>
        </div>
        <div className="dev-stat">
          <span>Turn Total:</span>
          <span>{metrics.total_ms ? `${metrics.total_ms}ms` : '--'}</span>
        </div>
      </div>
    </div>
  );
};

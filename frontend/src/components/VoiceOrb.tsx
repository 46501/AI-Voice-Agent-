import React from 'react';
import type { AgentState } from '../types/voice';
import './VoiceOrb.css';

interface VoiceOrbProps {
  state: AgentState;
  onClick: () => void;
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({ state, onClick }) => {
  let label = 'Tap to Talk';
  if (state === 'listening') label = 'Listening...';
  if (state === 'processing_stt' || state === 'thinking') label = 'Thinking...';
  if (state === 'speaking') label = 'Speaking...';
  if (state === 'error') label = 'Error';

  return (
    <div className={`orb-container state-${state}`} onClick={onClick}>
      <div className="orb-core"></div>
      <div className="orb-ring ring-1"></div>
      <div className="orb-ring ring-2"></div>
      <div className="orb-label">{label}</div>
    </div>
  );
};

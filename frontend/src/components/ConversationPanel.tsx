import React, { useRef, useEffect } from 'react';
import type { Message } from '../types/voice';
import { Wrench, CheckCircle } from 'lucide-react';
import './ConversationPanel.css';

interface ConversationPanelProps {
  messages: Message[];
}

export const ConversationPanel: React.FC<ConversationPanelProps> = ({ messages }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const renderToolMessage = () => {

    return (
      <div className="tool-message">
        <div className="tool-header">
          <Wrench size={16} />
          <span>Using Tool</span>
        </div>
        <div className="tool-body">
          {/* We hide the ugly JSON by default, or just show a success mark */}
          <CheckCircle size={14} className="tool-success" />
          <span className="tool-preview">Task completed successfully.</span>
        </div>
      </div>
    );
  };

  return (
    <div className="conversation-panel" ref={scrollRef}>
      {messages.length === 0 ? (
        <div className="empty-state">No conversation history. Start speaking!</div>
      ) : (
        messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.role}`}>
            {msg.role === 'tool' ? (
              renderToolMessage()
            ) : (
              <div className={`message-bubble ${msg.role}`}>
                <span className="message-role">{msg.role === 'user' ? 'You' : 'VoxAI'}</span>
                <p className="message-text">{msg.text}</p>
                <span className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
};

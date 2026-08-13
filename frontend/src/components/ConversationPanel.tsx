import React, { useRef, useEffect } from 'react';
import { Message } from '../types/voice';
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

  return (
    <div className="conversation-panel" ref={scrollRef}>
      {messages.length === 0 ? (
        <div className="empty-state">No conversation history. Start speaking!</div>
      ) : (
        messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.role}`}>
            <div className={`message-bubble ${msg.role}`}>
              <span className="message-role">{msg.role === 'user' ? 'You' : 'VoxAI'}</span>
              <p className="message-text">{msg.text}</p>
              <span className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

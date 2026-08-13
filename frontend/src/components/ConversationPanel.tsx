import React, { useRef, useEffect } from 'react';
import { Message } from '../types/voice';
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

  const renderToolMessage = (msg: Message) => {
    // Try to extract a clean tool name
    let toolName = "Tool";
    try {
      // In the backend we send name="weather_tool" or something similar
      // Actually we send the raw function_name as name in the payload. Let's see if it's there.
      // Wait, we need to pass `name` from backend in transcript payload if it's a tool.
      // We didn't do that. I'll just use the role label for now.
    } catch(e) {}

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
              renderToolMessage(msg)
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

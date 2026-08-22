import React from 'react';
import type { Conversation } from '../types/voice';
import { MessageSquare, Plus, X } from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  isOpen,
  setIsOpen
}) => {
  return (
    <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <h2>VoxAI</h2>
        <button className="close-sidebar-btn" onClick={() => setIsOpen(false)}>
          <X size={20} />
        </button>
      </div>

      <button className="new-chat-btn" onClick={onNewConversation}>
        <Plus size={18} /> New Conversation
      </button>

      <div className="conversations-list">
        <h4>Recent</h4>
        {conversations.length === 0 ? (
          <p className="no-chats">No recent conversations.</p>
        ) : (
          conversations.map(conv => (
            <div 
              key={conv.id} 
              className={`conversation-item ${activeConversationId === conv.id ? 'active' : ''}`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <MessageSquare size={16} />
              <span className="chat-title">{conv.title}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

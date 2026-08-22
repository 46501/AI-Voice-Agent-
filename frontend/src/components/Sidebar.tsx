import React from 'react';
import type { Conversation } from '../types/voice';
import { useAuth } from '../context/AuthContext';
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
  const { user, logout } = useAuth();

  return (
    <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <h2>VoxAI</h2>
        <button className="close-sidebar-btn" onClick={() => setIsOpen(false)}>
          &times;
        </button>
      </div>

      <button className="new-chat-btn" onClick={onNewConversation}>
        + New Conversation
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
              <span className="chat-icon">💬</span>
              <span className="chat-title">{conv.title}</span>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        {user ? (
          <div className="user-profile">
            <div className="user-info">
              <span className="user-name">{user.name || 'User'}</span>
              <span className="user-email">{user.email}</span>
            </div>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        ) : (
          <div className="auth-links">
            <button className="login-btn">Login</button>
          </div>
        )}
      </div>
    </div>
  );
};

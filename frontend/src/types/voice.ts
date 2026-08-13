export type AgentState = 'idle' | 'listening' | 'processing_stt' | 'thinking' | 'speaking' | 'error';

export interface Message {
  id: string;
  role: 'user' | 'ai' | 'system' | 'tool';
  text: string;
  timestamp: number;
}

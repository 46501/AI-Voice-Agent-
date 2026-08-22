export type AgentState = 
  | 'idle' 
  | 'listening' 
  | 'processing_stt' 
  | 'thinking' 
  | 'tool_calling' 
  | 'speaking' 
  | 'interrupted' 
  | 'error';

export interface LatencyMetrics {
  stt_ms?: number;
  llm_first_token_ms?: number;
  first_audio_ms?: number;
  tts_ms?: number;
  total_ms?: number;
}

export interface Message {
  id: string;
  role: 'user' | 'ai' | 'tool' | 'system';
  text: string;
  timestamp: number;
  turn_id?: string;
  metrics?: LatencyMetrics;
  isPartial?: boolean;
}

export interface ErrorState {
  code: string;
  stage: string;
  user_message: string;
  debug_message: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at?: string;
}

export interface User {
  id: number;
  email: string;
  name?: string;
}

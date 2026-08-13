import { useState, useEffect, useRef, useCallback } from 'react';
import { AgentState } from '../types/voice';

interface WebSocketProps {
  url: string;
  onTranscript: (role: 'user' | 'ai' | 'tool' | 'system', text: string, turnId?: string, isPartial?: boolean, metrics?: any) => void;
  onAudioResponse: (audioBuffer: ArrayBuffer, turnId?: string) => void;
  onStateChange: (state: AgentState) => void;
  onError: (error: string) => void;
}

export function useWebSocket({ url, onTranscript, onAudioResponse, onStateChange, onError }: WebSocketProps) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
        console.log('WebSocket connected');
      };

      ws.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'status') {
              onStateChange(data.status as AgentState);
            } else if (data.type === 'transcript') {
              onTranscript(data.role, data.text, data.turn_id, data.partial, data.metrics);
            } else if (data.type === 'error') {
              onError(data.message);
            }
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        } else if (event.data instanceof Blob) {
          const arrayBuffer = await event.data.arrayBuffer();
          // We can't easily pass turn_id with binary data unless we prepend a header.
          // For now, the active turn_id is managed by the frontend state in useVoiceAgent.
          onAudioResponse(arrayBuffer);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;
        console.log('WebSocket disconnected');
        
        // Reconnection logic
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const timeout = Math.pow(2, reconnectAttempts.current) * 1000;
          setTimeout(() => {
            reconnectAttempts.current += 1;
            connect();
          }, timeout);
        } else {
          onError("Connection lost. Please refresh the page.");
        }
      };

      ws.onerror = () => {
        // Handled by onclose usually, but can log here
        console.error("WebSocket error occurred");
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setIsConnected(false);
    }
  }, [url, onTranscript, onAudioResponse, onStateChange, onError]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      // Prevent auto-reconnect on intentional disconnect
      reconnectAttempts.current = maxReconnectAttempts; 
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendAudio = useCallback((audioBlob: Blob) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioBlob);
    }
  }, []);

  const sendClear = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'clear' }));
    }
  }, []);

  const sendInterrupt = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { isConnected, sendAudio, sendClear, sendInterrupt };
}

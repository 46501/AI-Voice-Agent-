import { useState, useEffect, useCallback, useRef } from 'react';
import { AgentState } from '../types/voice';

interface WebSocketHookProps {
  url: string;
  onTranscript: (role: 'user' | 'ai', text: string) => void;
  onAudioResponse: (audioBuffer: ArrayBuffer) => void;
  onStateChange: (state: AgentState) => void;
  onError: (message: string) => void;
}

export function useWebSocket({ url, onTranscript, onAudioResponse, onStateChange, onError }: WebSocketHookProps) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer'; // Very important for receiving audio bytes
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        onAudioResponse(event.data);
      } else {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'status') {
            onStateChange(data.status as AgentState);
          } else if (data.type === 'transcript') {
            onTranscript(data.role, data.text);
          } else if (data.type === 'error') {
            onError(data.message);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message', e);
        }
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
      // Simple reconnect logic
      setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      onError('WebSocket connection error');
    };

    wsRef.current = ws;
  }, [url, onTranscript, onAudioResponse, onStateChange, onError]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendAudio = useCallback((audioBlob: Blob) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioBlob);
    } else {
      onError('Cannot send audio, not connected');
    }
  }, [onError]);

  const sendClear = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'clear' }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { isConnected, sendAudio, sendClear };
}

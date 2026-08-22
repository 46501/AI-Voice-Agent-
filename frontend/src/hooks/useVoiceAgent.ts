import { useState, useEffect, useRef, useCallback } from 'react';
import { useAudioRecorder } from './useAudioRecorder';
import { useWebSocket } from './useWebSocket';
import type { AgentState, Message, LatencyMetrics } from '../types/voice';

export function useVoiceAgent(websocketUrl: string) {
  const [state, setState] = useState<AgentState>('idle');
  const [messages, setMessages] = useState<Message[]>([]);
  const [latencyMetrics, setLatencyMetrics] = useState<LatencyMetrics>({});
  const [errorState, setErrorState] = useState<import('../types/voice').ErrorState | null>(null);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceTimeoutRef = useRef<number | null>(null);
  const isSpeakingRef = useRef(false);
  const stateRef = useRef<AgentState>(state);
  
  useEffect(() => {
    stateRef.current = state;
  }, [state]);
  
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const activeSourceRef = useRef<AudioBufferSourceNode | null>(null);

  // Turn ID management to discard stale audio
  const activeTurnIdRef = useRef<string | null>(null);

  const VAD_SILENCE_MS = 1500;
  const VAD_THRESHOLD = 10;

  const playNextInQueue = useCallback(async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setState((prev) => prev === 'speaking' ? 'idle' : prev);
      return;
    }

    isPlayingRef.current = true;
    const audioBuffer = audioQueueRef.current.shift()!;
    
    if (!audioContextRef.current) {
       audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    const audioCtx = audioContextRef.current;
    
    try {
      const decodedBuffer = await audioCtx.decodeAudioData(audioBuffer);
      const source = audioCtx.createBufferSource();
      source.buffer = decodedBuffer;
      source.connect(audioCtx.destination);
      source.start(0);
      activeSourceRef.current = source;
      
      source.onended = () => {
        activeSourceRef.current = null;
        playNextInQueue();
      };
    } catch (e) {
      console.error('Failed to play audio chunk', e);
      playNextInQueue();
    }
  }, []);

  const handleTranscript = useCallback((role: 'user' | 'ai' | 'tool' | 'system', text: string, turnId?: string, isPartial?: boolean, metrics?: LatencyMetrics) => {
    if (turnId) {
        activeTurnIdRef.current = turnId;
    }
    
    if (metrics) {
        setLatencyMetrics(prev => ({ ...prev, ...metrics }));
    }

    setMessages(prev => {
      const lastMsg = prev[prev.length - 1];
      if (lastMsg && lastMsg.role === role && lastMsg.turn_id === turnId) {
        return [...prev.slice(0, -1), { ...lastMsg, text, isPartial, metrics: { ...lastMsg.metrics, ...metrics } }];
      } else {
        return [...prev, { id: Date.now().toString(), role, text, timestamp: Date.now(), turn_id: turnId, isPartial, metrics }];
      }
    });
  }, []);

  const handleAudioResponse = useCallback((audioBuffer: ArrayBuffer) => {
    if (stateRef.current === 'interrupted' || stateRef.current === 'listening') return;
    
    audioQueueRef.current.push(audioBuffer);
    if (!isPlayingRef.current) {
      playNextInQueue();
    }
  }, [playNextInQueue]);

  const handleStateChange = useCallback((newState: AgentState) => {
      setState(newState);
  }, []);

  const handleError = useCallback((err: import('../types/voice').ErrorState) => {
    console.error("Voice Agent Error:", err.debug_message);
    setErrorState(err);
    setState('error');
    // We don't automatically clear the error state anymore since we want the user to click "Try Again"
  }, []);

  const { isConnected, sendAudio, sendClear, sendInterrupt } = useWebSocket({
    url: websocketUrl,
    onTranscript: handleTranscript,
    onAudioResponse: handleAudioResponse,
    onStateChange: handleStateChange,
    onError: handleError
  });

  const stopPlaybackAndClearQueue = useCallback(() => {
    if (activeSourceRef.current) {
      activeSourceRef.current.onended = null;
      try {
        activeSourceRef.current.stop();
      } catch (e) { /* ignore */ }
      activeSourceRef.current = null;
    }
    audioQueueRef.current = [];
    isPlayingRef.current = false;
  }, []);

  const handleAudioReady = useCallback((blob: Blob) => {
    if (blob.size > 0) {
      sendAudio(blob);
    } else {
      setState(prev => prev === 'listening' ? 'idle' : prev);
    }
  }, [sendAudio]);

  const { isRecording, startRecording, stopRecording, stream } = useAudioRecorder(handleAudioReady);

  useEffect(() => {
    if (!isRecording || !stream) return;

    if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    const audioCtx = audioContextRef.current;
    
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }

    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaStreamSource(stream);
    
    analyser.fftSize = 256;
    analyser.minDecibels = -60;
    source.connect(analyser);
    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    let animationFrameId: number;

    const checkVolume = () => {
      if (!isRecording) return;
      
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const average = sum / dataArray.length;

      if (average > VAD_THRESHOLD) {
        if (!isSpeakingRef.current) {
          isSpeakingRef.current = true;
          
          if (isPlayingRef.current || stateRef.current === 'speaking' || stateRef.current === 'thinking') {
            console.log("Barge-in detected! Interrupting AI...");
            stopPlaybackAndClearQueue();
            sendInterrupt();
            setState('interrupted');
            activeTurnIdRef.current = null;
            setTimeout(() => setState('listening'), 100);
          }
        }
        
        if (silenceTimeoutRef.current) {
          window.clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
      } else {
        if (isSpeakingRef.current && !silenceTimeoutRef.current) {
          silenceTimeoutRef.current = window.setTimeout(() => {
            isSpeakingRef.current = false;
            setState(currentState => {
                if (currentState === 'listening') {
                    stopRecording();
                    return 'idle'; 
                }
                return currentState;
            });
            
          }, VAD_SILENCE_MS);
        }
      }

      animationFrameId = requestAnimationFrame(checkVolume);
    };

    checkVolume();

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      if (silenceTimeoutRef.current) window.clearTimeout(silenceTimeoutRef.current);
      try { source.disconnect(); } catch (e) {}
    };
  }, [isRecording, stream, stopRecording, stopPlaybackAndClearQueue, sendInterrupt]);

  const startConversation = useCallback(() => {
    setState('listening');
    startRecording();
  }, [startRecording]);

  const stopConversation = useCallback(() => {
    setState('idle');
    stopRecording();
    stopPlaybackAndClearQueue();
    sendInterrupt();
  }, [stopRecording, stopPlaybackAndClearQueue, sendInterrupt]);

  const clearConversation = useCallback(() => {
    setMessages([]);
    setLatencyMetrics({});
    sendClear();
  }, [sendClear]);

  return {
    state,
    messages,
    latencyMetrics,
    errorState,
    isConnected,
    isRecording,
    startConversation,
    stopConversation,
    clearConversation,
    clearError: () => {
      setErrorState(null);
      setState('idle');
    }
  };
}

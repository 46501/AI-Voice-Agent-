import { useState, useEffect, useRef, useCallback } from 'react';
import { useAudioRecorder } from './useAudioRecorder';
import { useWebSocket } from './useWebSocket';
import { AgentState, Message } from '../types/voice';

export function useVoiceAgent(websocketUrl: string) {
  const [state, setState] = useState<AgentState>('idle');
  const [messages, setMessages] = useState<Message[]>([]);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceTimeoutRef = useRef<number | null>(null);
  const isSpeakingRef = useRef(false);
  
  // Audio Playback Queue
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const activeSourceRef = useRef<AudioBufferSourceNode | null>(null);

  const VAD_SILENCE_MS = 1500;
  const VAD_THRESHOLD = 10; // Adjust for sensitivity

  const playNextInQueue = useCallback(async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      // If we finished playing everything and we are still in 'speaking' state, revert to idle
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

  const handleTranscript = useCallback((role: 'user' | 'ai', text: string) => {
    // If partial update, we replace the last message if it's from the same role.
    setMessages(prev => {
      const lastMsg = prev[prev.length - 1];
      if (lastMsg && lastMsg.role === role) {
        return [...prev.slice(0, -1), { ...lastMsg, text }];
      } else {
        return [...prev, { id: Date.now().toString(), role, text, timestamp: Date.now() }];
      }
    });
  }, []);

  const handleAudioResponse = useCallback((audioBuffer: ArrayBuffer) => {
    audioQueueRef.current.push(audioBuffer);
    if (!isPlayingRef.current) {
      playNextInQueue();
    }
  }, [playNextInQueue]);

  const { isConnected, sendAudio, sendClear, sendInterrupt } = useWebSocket({
    url: websocketUrl,
    onTranscript: handleTranscript,
    onAudioResponse: handleAudioResponse,
    onStateChange: setState,
    onError: (msg) => {
      console.error(msg);
      setState('error');
      setTimeout(() => setState('idle'), 3000);
    }
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
      // If no valid audio but state was listening, revert to idle.
      setState(prev => prev === 'listening' ? 'idle' : prev);
    }
  }, [sendAudio]);

  const { isRecording, startRecording, stopRecording, stream } = useAudioRecorder(handleAudioReady);

  // VAD Logic with Barge-in Support
  useEffect(() => {
    if (!isRecording || !stream) return;

    if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    const audioCtx = audioContextRef.current;
    
    // Resume context if suspended
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
        // Voice detected!
        if (!isSpeakingRef.current) {
          isSpeakingRef.current = true;
          
          // Barge-in logic: If AI is speaking, interrupt it!
          if (isPlayingRef.current) {
            console.log("Barge-in detected! Interrupting AI...");
            stopPlaybackAndClearQueue();
            sendInterrupt();
            setState('listening');
          }
        }
        
        if (silenceTimeoutRef.current) {
          window.clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
      } else {
        // Silence detected
        if (isSpeakingRef.current && !silenceTimeoutRef.current) {
          silenceTimeoutRef.current = window.setTimeout(() => {
            isSpeakingRef.current = false;
            // Only stop recording if we are actually listening for input
            // If we barged in, state might be 'speaking', but we forced it to 'listening'.
            // If it's already 'idle', do nothing.
            setState(currentState => {
                if (currentState === 'listening') {
                    stopRecording();
                    return 'idle'; // It will switch to 'processing_stt' via backend WS soon
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
      // We don't close the audio context because we use it for playback too.
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
    sendInterrupt(); // Tell backend to stop generating if it was
  }, [stopRecording, stopPlaybackAndClearQueue, sendInterrupt]);

  const clearConversation = useCallback(() => {
    setMessages([]);
    sendClear();
  }, [sendClear]);

  return {
    state,
    messages,
    isConnected,
    isRecording,
    startConversation,
    stopConversation,
    clearConversation
  };
}

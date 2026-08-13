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

  const VAD_SILENCE_MS = 1500; // Configurable silence timeout

  const handleTranscript = useCallback((role: 'user' | 'ai', text: string) => {
    setMessages(prev => [...prev, { id: Date.now().toString(), role, text, timestamp: Date.now() }]);
  }, []);

  const handleAudioResponse = useCallback(async (audioBuffer: ArrayBuffer) => {
    // Play AI audio response
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const source = audioCtx.createBufferSource();
    
    try {
      const decodedBuffer = await audioCtx.decodeAudioData(audioBuffer);
      source.buffer = decodedBuffer;
      source.connect(audioCtx.destination);
      source.start(0);
      
      source.onended = () => {
        setState('idle');
      };
    } catch (e) {
      console.error('Failed to play audio response', e);
      setState('idle');
    }
  }, []);

  const { isConnected, sendAudio, sendClear } = useWebSocket({
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

  const handleAudioReady = useCallback((blob: Blob) => {
    if (blob.size > 0) {
      sendAudio(blob);
    } else {
      setState('idle');
    }
  }, [sendAudio]);

  const { isRecording, startRecording, stopRecording, stream } = useAudioRecorder(handleAudioReady);

  // VAD Logic
  useEffect(() => {
    if (!isRecording || !stream) return;

    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaStreamSource(stream);
    
    analyser.fftSize = 256;
    analyser.minDecibels = -60; // Adjust sensitivity
    source.connect(analyser);

    audioContextRef.current = audioCtx;
    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const checkVolume = () => {
      if (!isRecording) return;
      
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const average = sum / dataArray.length;

      if (average > 10) { // Speech detected
        if (!isSpeakingRef.current) {
          isSpeakingRef.current = true;
        }
        if (silenceTimeoutRef.current) {
          window.clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
      } else { // Silence detected
        if (isSpeakingRef.current && !silenceTimeoutRef.current) {
          silenceTimeoutRef.current = window.setTimeout(() => {
            isSpeakingRef.current = false;
            stopRecording();
          }, VAD_SILENCE_MS);
        }
      }

      requestAnimationFrame(checkVolume);
    };

    checkVolume();

    return () => {
      if (silenceTimeoutRef.current) window.clearTimeout(silenceTimeoutRef.current);
      if (audioCtx.state !== 'closed') audioCtx.close();
    };
  }, [isRecording, stream, stopRecording]);

  const startConversation = useCallback(() => {
    setState('listening');
    startRecording();
  }, [startRecording]);

  const stopConversation = useCallback(() => {
    setState('idle');
    stopRecording();
  }, [stopRecording]);

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

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export interface AnomalyEvent {
  id: string;
  anomaly_type: string;
  severity: 'subtle' | 'mild' | 'moderate' | 'intense' | 'extreme';
  target: string;
  post_id?: number;
  thread_id?: number;
  data?: Record<string, unknown>;
  duration_ms: number;
  delay_ms: number;
  timestamp: string;
}

interface RitualMessage {
  type: 'welcome' | 'anomaly' | 'pong';
  user_id?: string;
  payload?: AnomalyEvent;
}

interface UseRitualOptions {
  autoConnect?: boolean;
  onAnomaly?: (event: AnomalyEvent) => void;
}

export function useRitual(options: UseRitualOptions = {}) {
  const { autoConnect = true, onAnomaly } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [lastAnomaly, setLastAnomaly] = useState<AnomalyEvent | null>(null);
  const [anomalyQueue, setAnomalyQueue] = useState<AnomalyEvent[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);

  const getFingerprint = useCallback(() => {
    // Simple fingerprint - in production use FingerprintJS
    if (typeof window === 'undefined') return null;

    let fp = localStorage.getItem('ritual_fp');
    if (!fp) {
      fp = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('ritual_fp', fp);
    }
    return fp;
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const fp = getFingerprint();
    if (!fp) return;

    const wsUrl = `ws://localhost:8000/ws/ritual?fp=${fp}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[Ritual] Connected');
      setIsConnected(true);

      // Start heartbeat
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat' }));
        }
      }, 25000);
    };

    ws.onmessage = (event) => {
      try {
        const message: RitualMessage = JSON.parse(event.data);

        if (message.type === 'welcome') {
          setUserId(message.user_id || null);
          console.log('[Ritual] Welcome:', message.user_id);
        }

        if (message.type === 'anomaly' && message.payload) {
          console.log('[Ritual] Anomaly:', message.payload);
          setLastAnomaly(message.payload);
          setAnomalyQueue(prev => [...prev, message.payload!]);
          onAnomaly?.(message.payload);
        }
      } catch (e) {
        console.error('[Ritual] Parse error:', e);
      }
    };

    ws.onclose = () => {
      console.log('[Ritual] Disconnected');
      setIsConnected(false);

      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }

      // Reconnect after 3s
      reconnectRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('[Ritual] Error:', error);
    };

    wsRef.current = ws;
  }, [getFingerprint, onAnomaly]);

  const disconnect = useCallback(() => {
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current);
    }
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const reportActivity = useCallback((data: {
    time_spent?: number;
    viewed_thread?: number;
    viewed_post?: number;
  }) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'activity',
        data,
      }));
    }
  }, []);

  const consumeAnomaly = useCallback(() => {
    setAnomalyQueue(prev => prev.slice(1));
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    userId,
    lastAnomaly,
    anomalyQueue,
    connect,
    disconnect,
    reportActivity,
    consumeAnomaly,
  };
}

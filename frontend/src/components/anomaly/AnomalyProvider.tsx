'use client';

import React, { createContext, useContext, useCallback, useState, useEffect } from 'react';
import { useRitual, AnomalyEvent } from '@/hooks/useRitual';
import { AnomalyEffects } from './AnomalyEffects';

interface AnomalyContextType {
  isConnected: boolean;
  userId: string | null;
  activeAnomalies: AnomalyEvent[];
  triggerTestAnomaly: (type: string) => void;
}

const AnomalyContext = createContext<AnomalyContextType | null>(null);

export function useAnomaly() {
  const context = useContext(AnomalyContext);
  if (!context) {
    throw new Error('useAnomaly must be used within AnomalyProvider');
  }
  return context;
}

interface AnomalyProviderProps {
  children: React.ReactNode;
}

export function AnomalyProvider({ children }: AnomalyProviderProps) {
  const [activeAnomalies, setActiveAnomalies] = useState<AnomalyEvent[]>([]);

  const handleAnomaly = useCallback((event: AnomalyEvent) => {
    // Add to active list
    setActiveAnomalies(prev => [...prev, event]);

    // Remove after duration
    setTimeout(() => {
      setActiveAnomalies(prev => prev.filter(a => a.id !== event.id));
    }, event.duration_ms + event.delay_ms + 500);
  }, []);

  const { isConnected, userId } = useRitual({
    autoConnect: true,
    onAnomaly: handleAnomaly,
  });

  // Test anomaly trigger (for development)
  const triggerTestAnomaly = useCallback(async (type: string) => {
    const fp = localStorage.getItem('ritual_fp');
    if (!fp) return;

    try {
      // First ensure state exists
      await fetch(`http://localhost:8000/admin/ritual/state/${fp}/reset`, {
        method: 'POST',
      });

      // Trigger anomaly
      await fetch(`http://localhost:8000/admin/ritual/anomaly/${fp}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          anomaly_type: type,
          severity: 'moderate',
        }),
      });
    } catch (e) {
      console.error('Failed to trigger anomaly:', e);
    }
  }, []);

  return (
    <AnomalyContext.Provider value={{
      isConnected,
      userId,
      activeAnomalies,
      triggerTestAnomaly,
    }}>
      {children}
      <AnomalyEffects anomalies={activeAnomalies} />
    </AnomalyContext.Provider>
  );
}

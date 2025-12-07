'use client';

import React, { useState } from 'react';
import { useAnomaly } from './AnomalyProvider';
import styles from './AnomalyTestPanel.module.css';

const ANOMALY_TYPES = [
  { type: 'glitch', label: 'Glitch', icon: '📺' },
  { type: 'static', label: 'Static', icon: '📡' },
  { type: 'whisper', label: 'Whisper', icon: '👄' },
  { type: 'presence', label: 'Presence', icon: '👤' },
  { type: 'shadow', label: 'Shadow', icon: '🌑' },
  { type: 'eyes', label: 'Eyes', icon: '👁' },
  { type: 'flicker', label: 'Flicker', icon: '💡' },
  { type: 'scroll', label: 'Scroll', icon: '📜' },
  { type: 'cursor', label: 'Cursor', icon: '🖱' },
];

export function AnomalyTestPanel() {
  const { isConnected, userId, triggerTestAnomaly } = useAnomaly();
  const [isOpen, setIsOpen] = useState(false);
  const [lastTriggered, setLastTriggered] = useState<string | null>(null);

  const handleTrigger = (type: string) => {
    triggerTestAnomaly(type);
    setLastTriggered(type);
    setTimeout(() => setLastTriggered(null), 2000);
  };

  return (
    <div className={styles.panel}>
      <button
        className={styles.toggleBtn}
        onClick={() => setIsOpen(!isOpen)}
        title="Anomaly Test Panel"
      >
        {isOpen ? '✕' : '👻'}
      </button>

      {isOpen && (
        <div className={styles.content}>
          <div className={styles.header}>
            <span className={styles.title}>Anomaly Control</span>
            <span className={`${styles.status} ${isConnected ? styles.connected : ''}`}>
              {isConnected ? '● Connected' : '○ Disconnected'}
            </span>
          </div>

          {userId && (
            <div className={styles.userId}>
              ID: {userId.slice(0, 20)}...
            </div>
          )}

          <div className={styles.buttons}>
            {ANOMALY_TYPES.map(({ type, label, icon }) => (
              <button
                key={type}
                className={`${styles.anomalyBtn} ${lastTriggered === type ? styles.triggered : ''}`}
                onClick={() => handleTrigger(type)}
                disabled={!isConnected}
              >
                <span className={styles.icon}>{icon}</span>
                <span className={styles.label}>{label}</span>
              </button>
            ))}
          </div>

          <div className={styles.hint}>
            Click to trigger anomaly effect
          </div>
        </div>
      )}
    </div>
  );
}

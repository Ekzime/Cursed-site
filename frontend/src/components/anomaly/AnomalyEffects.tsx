'use client';

import React, { useEffect, useState } from 'react';
import { AnomalyEvent } from '@/hooks/useRitual';
import styles from './AnomalyEffects.module.css';

interface AnomalyEffectsProps {
  anomalies: AnomalyEvent[];
}

export function AnomalyEffects({ anomalies }: AnomalyEffectsProps) {
  const [glitchActive, setGlitchActive] = useState(false);
  const [staticActive, setStaticActive] = useState(false);
  const [presenceActive, setPresenceActive] = useState(false);
  const [whisperText, setWhisperText] = useState<string | null>(null);
  const [eyesActive, setEyesActive] = useState(false);
  const [flickerActive, setFlickerActive] = useState(false);
  const [corruptionLevel, setCorruptionLevel] = useState(0);

  useEffect(() => {
    anomalies.forEach(anomaly => {
      const delay = anomaly.delay_ms || 0;
      const duration = anomaly.duration_ms || 1000;

      setTimeout(() => {
        switch (anomaly.anomaly_type) {
          case 'glitch':
            setGlitchActive(true);
            setTimeout(() => setGlitchActive(false), duration);
            break;

          case 'static':
            setStaticActive(true);
            setTimeout(() => setStaticActive(false), duration);
            break;

          case 'presence':
          case 'shadow':
            setPresenceActive(true);
            setTimeout(() => setPresenceActive(false), duration);
            break;

          case 'whisper':
            const messages = [
              'ты видишь это?',
              'мы здесь',
              'не уходи',
              'они смотрят',
              'помоги нам',
              'ты один из нас',
              'слышишь?',
            ];
            setWhisperText(messages[Math.floor(Math.random() * messages.length)]);
            setTimeout(() => setWhisperText(null), duration);
            break;

          case 'eyes':
            setEyesActive(true);
            setTimeout(() => setEyesActive(false), duration);
            break;

          case 'flicker':
            setFlickerActive(true);
            setTimeout(() => setFlickerActive(false), duration);
            break;

          case 'post_corrupt':
          case 'corruption':
            setCorruptionLevel(prev => Math.min(prev + 1, 5));
            setTimeout(() => setCorruptionLevel(prev => Math.max(prev - 1, 0)), duration * 2);
            break;

          case 'scroll':
            // Random scroll
            window.scrollBy({
              top: Math.random() * 200 - 100,
              behavior: 'smooth',
            });
            break;

          case 'cursor':
            document.body.style.cursor = 'none';
            setTimeout(() => {
              document.body.style.cursor = '';
            }, duration);
            break;
        }
      }, delay);
    });
  }, [anomalies]);

  return (
    <>
      {/* Glitch overlay */}
      {glitchActive && (
        <div className={styles.glitchOverlay}>
          <div className={styles.glitchLine1} />
          <div className={styles.glitchLine2} />
          <div className={styles.glitchLine3} />
        </div>
      )}

      {/* Static noise */}
      {staticActive && <div className={styles.staticOverlay} />}

      {/* Presence shadow */}
      {presenceActive && (
        <div className={styles.presenceOverlay}>
          <div className={styles.shadowFigure} />
        </div>
      )}

      {/* Whisper text */}
      {whisperText && (
        <div className={styles.whisperOverlay}>
          <span className={styles.whisperText}>{whisperText}</span>
        </div>
      )}

      {/* Eyes watching */}
      {eyesActive && (
        <div className={styles.eyesOverlay}>
          <div className={styles.eye} style={{ left: '20%', top: '30%' }}>👁</div>
          <div className={styles.eye} style={{ right: '15%', top: '45%' }}>👁</div>
          <div className={styles.eye} style={{ left: '40%', bottom: '20%' }}>👁</div>
        </div>
      )}

      {/* Flicker effect */}
      {flickerActive && <div className={styles.flickerOverlay} />}

      {/* Corruption vignette */}
      {corruptionLevel > 0 && (
        <div
          className={styles.corruptionOverlay}
          style={{ opacity: corruptionLevel * 0.15 }}
        />
      )}
    </>
  );
}

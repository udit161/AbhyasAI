import { useState, useEffect, useRef, useCallback } from 'react';

const TOTAL_DURATION = 3600; // 60:00 in seconds

function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

export default function VideoPlayer() {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [hovered, setHovered] = useState(null); // 'play' | 'bar' | null
  const intervalRef = useRef(null);
  const progressRef = useRef(null);

  const tick = useCallback(() => {
    setCurrentTime(t => {
      if (t >= TOTAL_DURATION) { setIsPlaying(false); return TOTAL_DURATION; }
      return t + 1;
    });
  }, []);

  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(tick, 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [isPlaying, tick]);

  const seek = useCallback((e) => {
    const bar = progressRef.current;
    if (!bar) return;
    const rect = bar.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    setCurrentTime(Math.round(ratio * TOTAL_DURATION));
  }, []);

  useEffect(() => {
    if (!isDragging) return;
    const onMove = (e) => seek(e);
    const onUp = () => setIsDragging(false);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, [isDragging, seek]);

  const progress = currentTime / TOTAL_DURATION;
  const progressPct = `${(progress * 100).toFixed(2)}%`;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-start',
      padding: '0 0 0 48px',
      pointerEvents: 'none',
      zIndex: 10,
    }}>
      {/* Glass card — half the screen wide */}
      <div style={{
        width: '48vw',
        maxWidth: 780,
        pointerEvents: 'auto',
        borderRadius: 28,
        background: 'linear-gradient(135deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.04) 100%)',
        border: '1px solid rgba(255,255,255,0.18)',
        backdropFilter: 'blur(32px) saturate(180%)',
        WebkitBackdropFilter: 'blur(32px) saturate(180%)',
        boxShadow: '0 8px 64px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.22), inset 0 -1px 0 rgba(255,255,255,0.06)',
        overflow: 'hidden',
        userSelect: 'none',
      }}>

        {/* ── Video area ── */}
        <div style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '16/9',
          background: 'linear-gradient(160deg, rgba(20,20,35,0.85) 0%, rgba(5,5,15,0.92) 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}>
          {/* Simulated lecture content */}
          <div style={{ textAlign: 'center', padding: 32 }}>
            <div style={{
              fontSize: 11,
              letterSpacing: '0.18em',
              color: 'rgba(255,255,255,0.35)',
              fontFamily: 'ui-monospace, monospace',
              marginBottom: 12,
              textTransform: 'uppercase',
            }}>
              Machine Learning · System Design
            </div>
            <div style={{
              fontSize: 22,
              fontWeight: 600,
              color: 'rgba(255,255,255,0.85)',
              letterSpacing: '-0.01em',
              lineHeight: 1.3,
            }}>
              Sample Video Lecture
            </div>
            <div style={{
              marginTop: 18,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 14px',
              borderRadius: 999,
              background: 'rgba(255,255,255,0.07)',
              border: '1px solid rgba(255,255,255,0.12)',
              fontSize: 12,
              color: 'rgba(255,255,255,0.5)',
              fontFamily: 'ui-monospace, monospace',
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: isPlaying ? '#4ade80' : 'rgba(255,255,255,0.3)', display: 'inline-block', boxShadow: isPlaying ? '0 0 6px #4ade80' : 'none', transition: 'all 0.3s' }} />
              {isPlaying ? 'Playing' : 'Paused'}
            </div>
          </div>

          {/* Timestamp chip — top left */}
          <div style={{
            position: 'absolute',
            top: 14,
            left: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 7,
            padding: '5px 12px',
            borderRadius: 999,
            background: 'rgba(0,0,0,0.55)',
            border: '1px solid rgba(255,255,255,0.12)',
            backdropFilter: 'blur(12px)',
            fontSize: 12,
            fontFamily: 'ui-monospace, monospace',
            color: 'rgba(255,255,255,0.75)',
            letterSpacing: '0.04em',
          }}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.7 }}>
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
            Context window: 00:00 – {formatTime(currentTime)}
          </div>
        </div>

        {/* ── Controls bar ── */}
        <div style={{
          padding: '20px 24px 24px',
          background: 'linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.06) 100%)',
        }}>

          {/* ── Big timestamp display ── */}
          <div style={{
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'center',
            gap: 6,
            marginBottom: 16,
          }}>
            <span style={{
              fontSize: 48,
              fontWeight: 700,
              fontFamily: 'ui-monospace, monospace',
              color: '#fff',
              letterSpacing: '-0.02em',
              lineHeight: 1,
              textShadow: '0 0 32px rgba(255,255,255,0.25)',
            }}>
              {formatTime(currentTime)}
            </span>
            <span style={{
              fontSize: 18,
              fontFamily: 'ui-monospace, monospace',
              color: 'rgba(255,255,255,0.35)',
              letterSpacing: '-0.01em',
            }}>
              / {formatTime(TOTAL_DURATION)}
            </span>
          </div>

          {/* ── Progress bar ── */}
          <div
            ref={progressRef}
            onMouseDown={(e) => { setIsDragging(true); seek(e); }}
            onClick={seek}
            onMouseEnter={() => setHovered('bar')}
            onMouseLeave={() => setHovered(null)}
            style={{
              position: 'relative',
              height: hovered === 'bar' ? 8 : 5,
              borderRadius: 999,
              background: 'rgba(255,255,255,0.12)',
              cursor: 'pointer',
              marginBottom: 22,
              transition: 'height 0.15s ease',
            }}
          >
            {/* Filled track */}
            <div style={{
              position: 'absolute',
              left: 0, top: 0, bottom: 0,
              width: progressPct,
              borderRadius: 999,
              background: 'linear-gradient(90deg, rgba(255,255,255,0.9), rgba(180,200,255,0.85))',
              boxShadow: '0 0 10px rgba(180,200,255,0.6)',
              transition: isDragging ? 'none' : 'width 0.5s linear',
            }} />
            {/* Thumb */}
            <div style={{
              position: 'absolute',
              top: '50%',
              left: progressPct,
              transform: 'translate(-50%, -50%)',
              width: hovered === 'bar' || isDragging ? 14 : 0,
              height: hovered === 'bar' || isDragging ? 14 : 0,
              borderRadius: '50%',
              background: '#fff',
              boxShadow: '0 0 12px rgba(255,255,255,0.8)',
              transition: 'width 0.15s, height 0.15s',
              pointerEvents: 'none',
            }} />
          </div>

          {/* ── Playback controls ── */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
          }}>
            {/* Rewind 10s */}
            <ControlBtn
              title="-10s"
              onClick={() => setCurrentTime(t => Math.max(0, t - 10))}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
                <text x="8" y="15" fontSize="5" fill="currentColor" fontFamily="sans-serif">10</text>
              </svg>
            </ControlBtn>

            {/* Play / Pause — big */}
            <button
              id="video-play-pause"
              onClick={() => setIsPlaying(p => !p)}
              onMouseEnter={() => setHovered('play')}
              onMouseLeave={() => setHovered(null)}
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                border: '1.5px solid rgba(255,255,255,0.35)',
                background: hovered === 'play'
                  ? 'linear-gradient(135deg, rgba(255,255,255,0.28), rgba(255,255,255,0.12))'
                  : 'linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.07))',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                boxShadow: hovered === 'play'
                  ? '0 0 32px rgba(255,255,255,0.25), inset 0 1px 0 rgba(255,255,255,0.4)'
                  : '0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.25)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                transition: 'all 0.2s cubic-bezier(0.22,1,0.36,1)',
                transform: hovered === 'play' ? 'scale(1.08)' : 'scale(1)',
                flexShrink: 0,
              }}
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="4" width="4" height="16" rx="1"/>
                  <rect x="14" y="4" width="4" height="16" rx="1"/>
                </svg>
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              )}
            </button>

            {/* Skip 10s */}
            <ControlBtn
              title="+10s"
              onClick={() => setCurrentTime(t => Math.min(TOTAL_DURATION, t + 10))}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 5V1l5 5-5 5V7c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6h2c0 4.42-3.58 8-8 8s-8-3.58-8-8 3.58-8 8-8z"/>
                <text x="8" y="15" fontSize="5" fill="currentColor" fontFamily="sans-serif">10</text>
              </svg>
            </ControlBtn>
          </div>

          {/* ── Pause-to-ask hint ── */}
          <div style={{
            marginTop: 16,
            textAlign: 'center',
            fontSize: 11,
            color: 'rgba(255,255,255,0.28)',
            letterSpacing: '0.08em',
            fontFamily: 'ui-monospace, monospace',
          }}>
            PAUSE ANYTIME TO ASK THE AI ASSISTANT
          </div>
        </div>
      </div>
    </div>
  );
}

function ControlBtn({ onClick, children, title }) {
  const [hov, setHov] = useState(false);
  return (
    <button
      onClick={onClick}
      title={title}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        width: 44,
        height: 44,
        borderRadius: '50%',
        border: '1px solid rgba(255,255,255,0.15)',
        background: hov ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.06)',
        color: 'rgba(255,255,255,0.75)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all 0.18s ease',
        transform: hov ? 'scale(1.1)' : 'scale(1)',
        backdropFilter: 'blur(8px)',
        flexShrink: 0,
      }}
    >
      {children}
    </button>
  );
}

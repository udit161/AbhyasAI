import { useState, useEffect, useRef, useCallback } from 'react';
import LearningAssistant from '../assistant/LearningAssistant';
import TranscriptView from './TranscriptView';

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
  const [rightTab, setRightTab] = useState('assistant'); // 'assistant' | 'transcript'
  const intervalRef = useRef(null);
  const progressRef = useRef(null);
  const fileInputRef = useRef(null);
  const [videoSrc, setVideoSrc] = useState(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setVideoSrc(url);
    }
  };

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
      alignItems: 'stretch', /* stretch to match heights */
      justifyContent: 'flex-start',
      padding: '48px',
      gap: '40px', /* space between video and assistant */
      pointerEvents: 'none',
      zIndex: 10,
    }}>
      {/* ── Left Column: Video Player ── */}
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
          {videoSrc ? (
            <video 
              src={videoSrc}
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              controls
            />
          ) : (
            <div style={{ textAlign: 'center', padding: 32 }}>
              {/* Simulated lecture content */}
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
          )}

          {/* Upload Button — top right */}
          <div style={{
            position: 'absolute',
            top: 14,
            right: 16,
            zIndex: 20
          }}>
            <input 
              type="file" 
              accept="video/*" 
              ref={fileInputRef} 
              style={{ display: 'none' }} 
              onChange={handleFileUpload} 
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 14px',
                borderRadius: 999,
                background: 'rgba(255,255,255,0.15)',
                border: '1px solid rgba(255,255,255,0.25)',
                backdropFilter: 'blur(12px)',
                fontSize: 12,
                fontWeight: 600,
                color: '#fff',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.25)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.15)'; }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
              Upload Video
            </button>
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

      {/* ── Right Column: AI Assistant / Transcript ── */}
      <div style={{
        flex: 1,
        maxWidth: 580,
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        pointerEvents: 'auto',
      }}>
        
        {/* Tab Switcher & Abstract Logo Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          {/* Tab Switcher */}
          <div style={{
            display: 'flex', gap: '6px',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '16px', padding: '6px',
            backdropFilter: 'blur(20px)',
            width: 'fit-content'
          }}>
          <button
            onClick={() => setRightTab('assistant')}
            style={{
              padding: '8px 20px', borderRadius: '12px', fontSize: '0.85rem', fontWeight: 600,
              background: rightTab === 'assistant' ? 'rgba(255,255,255,0.15)' : 'transparent',
              color: rightTab === 'assistant' ? '#fff' : 'rgba(255,255,255,0.5)',
              border: 'none', cursor: 'pointer', transition: 'all 0.2s',
              boxShadow: rightTab === 'assistant' ? '0 2px 12px rgba(0,0,0,0.2)' : 'none'
            }}
          >
            AI Assistant
          </button>
          <button
            onClick={() => setRightTab('transcript')}
            style={{
              padding: '8px 20px', borderRadius: '12px', fontSize: '0.85rem', fontWeight: 600,
              background: rightTab === 'transcript' ? 'rgba(255,255,255,0.15)' : 'transparent',
              color: rightTab === 'transcript' ? '#fff' : 'rgba(255,255,255,0.5)',
              border: 'none', cursor: 'pointer', transition: 'all 0.2s',
              boxShadow: rightTab === 'transcript' ? '0 2px 12px rgba(0,0,0,0.2)' : 'none'
            }}
          >
            Transcript
          </button>
          </div>

          {/* Abstract Floating Logo */}
          <div style={{
            position: 'relative',
            top: '-20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '192px',
            height: '88px',
            animation: 'floatBob 6s ease-in-out infinite',
            marginBottom: '-20px', // Prevent the shifted height from pushing content down
          }}>
            {/* Morphing Abstract Blob Background */}
            <div style={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.02))',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              animation: 'morphShape 8s ease-in-out infinite',
              zIndex: 1,
              backdropFilter: 'blur(8px)',
            }} />
            
            {/* The Logo Image */}
            <img 
              src="/favicon.png" 
              alt="AbhyasAI Logo" 
              style={{
                position: 'relative',
                zIndex: 2,
                width: '90%',
                height: '90%',
                objectFit: 'contain',
                mixBlendMode: 'screen',
              }} 
            />
          </div>
        </div>

        {/* Content Area */}
        <div style={{
          flex: 1,
          borderRadius: 28,
          background: 'linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%)',
          border: '1px solid rgba(255,255,255,0.12)',
          backdropFilter: 'blur(32px) saturate(180%)',
          WebkitBackdropFilter: 'blur(32px) saturate(180%)',
          boxShadow: '0 8px 64px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          {rightTab === 'assistant' ? (
            <LearningAssistant currentTime={currentTime} onOpenQuiz={() => console.log('quiz')} />
          ) : (
            <TranscriptView currentTime={currentTime} onSeek={setCurrentTime} />
          )}
        </div>
      </div>

      {/* Abstract Logo Animations */}
      <style>{`
        @keyframes morphShape {
          0%, 100% { border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; }
          34% { border-radius: 70% 30% 50% 50% / 30% 30% 70% 70%; }
          67% { border-radius: 100% 60% 60% 100% / 100% 100% 60% 60%; }
        }
        @keyframes floatBob {
          0%, 100% { transform: translateY(0) rotate(-2deg); }
          50% { transform: translateY(-12px) rotate(4deg); }
        }
      `}</style>
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

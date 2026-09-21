import React from 'react';
import { Play, Pause, FastForward, Rewind, Clock } from 'lucide-react';

export default function VideoPlayer({ currentTime, setCurrentTime, isPlaying, setIsPlaying, onPauseAndAsk }) {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSeek = (e) => {
    setCurrentTime(parseFloat(e.target.value));
  };

  const handlePause = () => {
    setIsPlaying(false);
    onPauseAndAsk();
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Video Viewport Container */}
      <div style={{
        position: 'relative',
        width: '100%',
        aspectRatio: '16/9',
        backgroundColor: '#000',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '1px solid var(--border-color)',
        overflow: 'hidden'
      }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <Clock size={48} style={{ marginBottom: '12px', color: 'var(--accent-blue)' }} />
          <p style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>Sample Video Lecture: Machine Learning System Design</p>
          <p style={{ fontSize: '0.85rem' }}>Current Playhead: <span style={{ color: 'var(--accent-cyan)', fontWeight: 'bold' }}>{formatTime(currentTime)}</span> / 60:00</p>
        </div>

        {/* Timestamp Boundary Indicator Banner */}
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          background: 'rgba(15, 23, 42, 0.85)',
          padding: '6px 12px',
          borderRadius: '6px',
          fontSize: '0.75rem',
          border: '1px solid rgba(59, 130, 246, 0.4)',
          color: '#60a5fa'
        }}>
          Timestamp Constraint: 00:00 - {formatTime(currentTime)}
        </div>
      </div>

      {/* Playhead Controls & Scrubber */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <input
          type="range"
          min="0"
          max="3600"
          value={currentTime}
          onChange={handleSeek}
          style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--accent-blue)' }}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              style={{ background: 'var(--accent-blue)', color: '#fff', padding: '8px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              {isPlaying ? 'Pause' : 'Play'}
            </button>

            <button
              onClick={handlePause}
              style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.4)', padding: '8px 14px', borderRadius: '6px', fontSize: '0.85rem', fontWeight: '500' }}
            >
              Pause & Ask AI
            </button>
          </div>

          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            {formatTime(currentTime)} / 60:00
          </div>
        </div>
      </div>
    </div>
  );
}

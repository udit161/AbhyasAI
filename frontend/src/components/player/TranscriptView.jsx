import React, { useEffect, useRef } from 'react';
import { AlignLeft, PlayCircle } from 'lucide-react';

const TRANSCRIPT = [
  { start: 0, end: 300, text: "Welcome to Machine Learning Systems Design. Today we discuss timestamp-aware vector retrieval and multi-resource grounding." },
  { start: 300, end: 1122, text: "When building interactive learning assistants, timestamp boundary enforcement prevents revealing future lecture content. The retriever filters documents where start_time <= current_time (e.g. 18:42)." },
  { start: 1122, end: 1800, text: "Next section: Advanced graph retrieval, AWS Neptune integration, and cost optimization techniques for enterprise scale." },
  // Adding a few mock lines to fill out the view
  { start: 1800, end: 2400, text: "Let's dive into the specifics of how vector embeddings are generated for video frames and audio segments. We use a multimodal model to project both into the same latent space." },
  { start: 2400, end: 3000, text: "This allows us to perform semantic searches across both visual and textual content simultaneously, ensuring high precision in our RAG pipeline." },
  { start: 3000, end: 3600, text: "Finally, we will look at how to deploy this architecture on Kubernetes with GPU nodes to handle real-time inference at scale." }
];

function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

export default function TranscriptView({ currentTime, onSeek }) {
  const scrollRef = useRef(null);

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: '520px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlignLeft size={20} color="var(--accent-blue)" />
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Interactive Transcript</h2>
        </div>
      </div>

      {/* Transcript Scroll Area */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '12px' }}>
        {TRANSCRIPT.map((segment, idx) => {
          const isActive = currentTime >= segment.start && currentTime < segment.end;
          const isPast = currentTime >= segment.end;
          
          return (
            <div
              key={idx}
              onClick={() => onSeek && onSeek(segment.start)}
              style={{
                padding: '12px 16px',
                borderRadius: '12px',
                background: isActive ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                border: '1px solid',
                borderColor: isActive ? 'rgba(255,255,255,0.15)' : 'transparent',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                gap: '12px',
                opacity: isPast ? 0.6 : 1,
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <div style={{ 
                color: isActive ? 'var(--accent-blue)' : 'rgba(255,255,255,0.4)', 
                fontFamily: 'ui-monospace, monospace', 
                fontSize: '0.75rem',
                paddingTop: '3px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                minWidth: '50px'
              }}>
                {isActive && <PlayCircle size={12} />}
                {formatTime(segment.start)}
              </div>
              <div style={{ 
                fontSize: '0.9rem', 
                lineHeight: '1.6',
                color: isActive ? '#fff' : 'rgba(255,255,255,0.7)',
                fontWeight: isActive ? 500 : 400
              }}>
                {segment.text}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

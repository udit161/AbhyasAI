import React from 'react';
import { UploadCloud, FileText, Video, Presentation } from 'lucide-react';

export default function ResourceUploader() {
  return (
    <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <UploadCloud size={20} color="var(--accent-cyan)" />
        <div>
          <h3 style={{ fontSize: '0.88rem', fontWeight: '600' }}>Active Learning Resources</h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>1 Video Transcript + 1 PDF Guide + 1 PPT Deck loaded</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <span style={{ fontSize: '0.75rem', background: 'rgba(59, 130, 246, 0.1)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '4px 8px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Video size={12} /> Video Transcript (18:42 limit)
        </span>
        <span style={{ fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '4px 8px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <FileText size={12} /> Architecture_Notes.pdf
        </span>
        <span style={{ fontSize: '0.75rem', background: 'rgba(251, 191, 36, 0.1)', color: '#fbbf24', border: '1px solid rgba(251, 191, 36, 0.3)', padding: '4px 8px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Presentation size={12} /> System_Design_Slides.ppt
        </span>
      </div>
    </div>
  );
}

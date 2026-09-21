import React from 'react';
import { Video, FileText, Presentation } from 'lucide-react';

export default function CitationBadge({ citation }) {
  const getIcon = () => {
    switch (citation.source_type) {
      case 'video': return <Video size={12} color="#60a5fa" />;
      case 'pdf': return <FileText size={12} color="#f87171" />;
      case 'ppt': return <Presentation size={12} color="#fbbf24" />;
      default: return <FileText size={12} color="#94a3b8" />;
    }
  };

  const formatLabel = () => {
    if (citation.source_type === 'video') {
      const minsStart = Math.floor(citation.timestamp_start / 60);
      const secsStart = Math.floor(citation.timestamp_start % 60);
      const minsEnd = Math.floor(citation.timestamp_end / 60);
      const secsEnd = Math.floor(citation.timestamp_end % 60);
      return `Video ${minsStart}:${secsStart.toString().padStart(2, '0')}-${minsEnd}:${secsEnd.toString().padStart(2, '0')}`;
    } else if (citation.page_number) {
      return `${citation.source_type.toUpperCase()} Page/Slide ${citation.page_number}`;
    }
    return citation.title;
  };

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
      background: 'rgba(255, 255, 255, 0.05)',
      border: '1px solid var(--border-color)',
      padding: '2px 8px',
      borderRadius: '12px',
      fontSize: '0.75rem',
      color: 'var(--text-muted)'
    }}>
      {getIcon()}
      {formatLabel()}
    </span>
  );
}

import React from 'react';
import { BookOpen, UserCheck, Sparkles } from 'lucide-react';

export default function Header({ activeTab, setActiveTab }) {
  return (
    <header className="glass-panel" style={{ margin: '16px', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', padding: '10px', borderRadius: '10px', display: 'flex' }}>
          <Sparkles size={24} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: '700', background: 'linear-gradient(90deg, #60a5fa, #c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            EduMind AI Platform
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Timestamp-Aware Learning Assistant & AI Mock Interviewer</p>
        </div>
      </div>

      <nav style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => setActiveTab('learning')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            background: activeTab === 'learning' ? 'var(--accent-blue)' : 'transparent',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.9rem',
            fontWeight: '500'
          }}
        >
          <BookOpen size={16} /> Interactive Lecture
        </button>
        <button
          onClick={() => setActiveTab('interview')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            background: activeTab === 'interview' ? 'var(--accent-purple)' : 'transparent',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.9rem',
            fontWeight: '500'
          }}
        >
          <UserCheck size={16} /> AI Mock Interview
        </button>
      </nav>
    </header>
  );
}

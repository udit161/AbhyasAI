import React, { useState } from 'react';
import { Send, Bot, HelpCircle, ShieldAlert, Zap } from 'lucide-react';
import { askQuestion } from '../../services/api';
import CitationBadge from './CitationBadge';

export default function LearningAssistant({ currentTime, onOpenQuiz }) {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'Hello! I am your timestamp-aware AI Learning Assistant. Pause the video anytime and ask questions grounded strictly in the material you have watched so far.',
      citations: [],
      timestampRange: '00:00 - 00:00'
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const userQ = inputQuery;
    setInputQuery('');
    
    setMessages(prev => [...prev, { sender: 'user', text: userQ }]);
    setLoading(true);

    try {
      const res = await askQuestion('video_sample_1', currentTime, userQ);
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: res.answer,
          citations: res.citations,
          timestampRange: res.timestamp_range_used,
          isRefusal: res.is_refusal,
          latency: res.latency_ms
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: 'Error connecting to the backend service. Make sure FastAPI server is running.',
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    'Explain this concept in simpler words.',
    'Give me an example or analogy.',
    'What did the instructor mean here?',
    'Summarize what I have learned so far.'
  ];

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: '520px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Bot size={20} color="var(--accent-blue)" />
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Context Assistant</h2>
        </div>
        <button
          onClick={onOpenQuiz}
          style={{ 
            background: 'rgba(255,255,255,0.92)', 
            color: '#0a0a0f', 
            padding: '6px 14px', 
            borderRadius: '8px', 
            fontSize: '0.8rem', 
            fontWeight: 600,
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px',
            boxShadow: '0 0 16px rgba(255,255,255,0.25)',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          <Zap size={14} /> Generate Quiz
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '4px' }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              background: msg.sender === 'user' ? 'var(--accent-blue)' : 'rgba(15, 23, 42, 0.6)',
              border: msg.sender === 'bot' ? '1px solid var(--border-color)' : 'none',
              borderRadius: '10px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}
          >
            <p style={{ fontSize: '0.88rem', lineHeight: '1.4' }}>{msg.text}</p>

            {msg.citations && msg.citations.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Sources:</span>
                {msg.citations.map((c, idx) => (
                  <CitationBadge key={idx} citation={c} />
                ))}
              </div>
            )}

            {msg.timestampRange && msg.sender === 'bot' && (
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                <span>Context boundary: {msg.timestampRange}</span>
                {msg.latency && <span>{msg.latency.toFixed(0)}ms</span>}
              </div>
            )}
          </div>
        ))}
        {loading && <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>AI reasoning from watched context...</div>}
      </div>

      {/* Quick Prompts */}
      <div className="no-scrollbar" style={{ display: 'flex', gap: '6px', overflowX: 'auto', padding: '8px 0' }}>
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => { setInputQuery(p); }}
            style={{ whiteSpace: 'nowrap', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', color: 'var(--text-muted)', padding: '4px 10px', borderRadius: '14px', fontSize: '0.75rem' }}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
        <input
          type="text"
          placeholder="Ask a question about content up to current timestamp..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          style={{
            flex: 1,
            background: 'rgba(15, 23, 42, 0.8)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '10px 14px',
            color: '#fff',
            fontSize: '0.88rem',
            outline: 'none'
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{ background: 'var(--accent-blue)', color: '#fff', padding: '10px 16px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}

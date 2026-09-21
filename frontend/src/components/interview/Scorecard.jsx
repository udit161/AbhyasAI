import React from 'react';
import { Award, CheckCircle, AlertTriangle, Lightbulb, DollarSign } from 'lucide-react';

export default function Scorecard({ scorecard, onRestart }) {
  if (!scorecard) return null;

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-cyan)' }}>Interview Evaluation Scorecard</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Session ID: {scorecard.session_id}</p>
        </div>
        <div style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid var(--accent-blue)', padding: '12px 20px', borderRadius: '12px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#60a5fa' }}>{scorecard.overall_score}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>OVERALL SCORE</div>
        </div>
      </div>

      {/* Breakdown Grids */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ color: 'var(--accent-cyan)', fontWeight: '700', fontSize: '1.2rem' }}>{scorecard.technical_knowledge_score}%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Technical Depth</div>
        </div>
        <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ color: 'var(--accent-blue)', fontWeight: '700', fontSize: '1.2rem' }}>{scorecard.communication_score}%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Communication</div>
        </div>
        <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ color: 'var(--accent-purple)', fontWeight: '700', fontSize: '1.2rem' }}>{scorecard.problem_solving_score}%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Problem Solving</div>
        </div>
        <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ color: '#f59e0b', fontWeight: '700', fontSize: '1.2rem' }}>{scorecard.answer_structure_score}%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Structure</div>
        </div>
      </div>

      {/* Strengths & Improvement */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={{ background: 'rgba(34, 197, 94, 0.05)', border: '1px solid rgba(34, 197, 94, 0.2)', padding: '16px', borderRadius: '8px' }}>
          <h3 style={{ fontSize: '0.95rem', color: '#4ade80', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <CheckCircle size={16} /> Key Strengths
          </h3>
          <ul style={{ listStyleType: 'disc', paddingLeft: '20px', fontSize: '0.85rem', color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {scorecard.strengths.map((s, idx) => <li key={idx}>{s}</li>)}
          </ul>
        </div>

        <div style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '16px', borderRadius: '8px' }}>
          <h3 style={{ fontSize: '0.95rem', color: '#f87171', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <AlertTriangle size={16} /> Growth Areas
          </h3>
          <ul style={{ listStyleType: 'disc', paddingLeft: '20px', fontSize: '0.85rem', color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {scorecard.improvement_areas.map((a, idx) => <li key={idx}>{a}</li>)}
          </ul>
        </div>
      </div>

      {/* Recommendations & Cost */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15, 23, 42, 0.6)', padding: '14px 18px', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <DollarSign size={16} color="var(--accent-cyan)" />
          Estimated Session Operating Cost: <strong style={{ color: '#fff' }}>{scorecard.estimated_operating_cost}</strong>
        </div>
        <button
          onClick={onRestart}
          style={{ background: 'var(--accent-blue)', color: '#fff', padding: '8px 16px', borderRadius: '6px', fontSize: '0.85rem' }}
        >
          Start New Interview
        </button>
      </div>
    </div>
  );
}

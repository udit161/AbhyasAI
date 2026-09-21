import React, { useState } from 'react';
import { User, Bot, Send, Award, PlayCircle } from 'lucide-react';
import { startInterview, submitInterviewAnswer, getInterviewScorecard } from '../../services/api';
import Scorecard from './Scorecard';

export default function MockInterview() {
  const [initForm, setInitForm] = useState({
    candidate_name: 'Alex Johnson',
    target_role: 'Senior AI System Engineer',
    skill_level: 'Intermediate',
    interview_type: 'Technical System Design'
  });

  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [candidateAnswer, setCandidateAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [scorecard, setScorecard] = useState(null);

  const handleStart = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await startInterview(initForm);
      setSessionId(res.session_id);
      setMessages([{ sender: 'bot', text: res.question, qNum: res.question_number }]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendAnswer = async (e) => {
    e.preventDefault();
    if (!candidateAnswer.trim() || loading) return;

    const ansText = candidateAnswer;
    setCandidateAnswer('');
    setMessages(prev => [...prev, { sender: 'candidate', text: ansText }]);
    setLoading(true);

    try {
      const res = await submitInterviewAnswer(sessionId, ansText);
      if (res.is_complete) {
        setMessages(prev => [...prev, { sender: 'bot', text: res.next_question }]);
        const sc = await getInterviewScorecard(sessionId);
        setScorecard(sc);
      } else {
        setMessages(prev => [...prev, { sender: 'bot', text: res.next_question, qNum: res.question_number }]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (scorecard) {
    return <Scorecard scorecard={scorecard} onRestart={() => { setScorecard(null); setSessionId(null); setMessages([]); }} />;
  }

  if (!sessionId) {
    return (
      <div className="glass-panel" style={{ padding: '32px', maxWidth: '640px', margin: '0 auto' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '8px', background: 'linear-gradient(90deg, #c084fc, #60a5fa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          AI Adaptive Mock Interview Suite
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '24px' }}>
          Configure candidate role profile for dynamic follow-up questioning and explainable scorecard feedback.
        </p>

        <form onSubmit={handleStart} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Candidate Name</label>
            <input
              type="text"
              value={initForm.candidate_name}
              onChange={(e) => setInitForm({ ...initForm, candidate_name: e.target.value })}
              style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '10px', color: '#fff' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Target Role</label>
            <input
              type="text"
              value={initForm.target_role}
              onChange={(e) => setInitForm({ ...initForm, target_role: e.target.value })}
              style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '10px', color: '#fff' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Skill Level</label>
              <select
                value={initForm.skill_level}
                onChange={(e) => setInitForm({ ...initForm, skill_level: e.target.value })}
                style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '10px', color: '#fff' }}
              >
                <option value="Entry">Entry Level</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Senior">Senior / Principal</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Interview Type</label>
              <select
                value={initForm.interview_type}
                onChange={(e) => setInitForm({ ...initForm, interview_type: e.target.value })}
                style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '10px', color: '#fff' }}
              >
                <option value="Technical System Design">Technical System Design</option>
                <option value="Behavioral">Behavioral STAR</option>
                <option value="RAG Architecture">RAG Architecture & ML</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{ marginTop: '12px', background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)', color: '#fff', padding: '12px', borderRadius: '8px', fontWeight: '600', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            <PlayCircle size={18} /> Start Interactive Interview
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '620px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: '600' }}>Live Interview: {initForm.target_role}</h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Adaptive Session ID: {sessionId}</p>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '4px' }}>
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: m.sender === 'candidate' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              background: m.sender === 'candidate' ? 'var(--accent-purple)' : 'rgba(15, 23, 42, 0.6)',
              border: m.sender === 'bot' ? '1px solid var(--border-color)' : 'none',
              borderRadius: '10px',
              padding: '12px',
              fontSize: '0.9rem',
              lineHeight: '1.4'
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              {m.sender === 'bot' ? 'AI Interviewer' : 'Candidate (You)'}
            </div>
            {m.text}
          </div>
        ))}
      </div>

      <form onSubmit={handleSendAnswer} style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
        <input
          type="text"
          placeholder="Type your response to the interviewer..."
          value={candidateAnswer}
          onChange={(e) => setCandidateAnswer(e.target.value)}
          style={{ flex: 1, background: 'rgba(15, 23, 42, 0.8)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '12px', color: '#fff', outline: 'none' }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{ background: 'var(--accent-purple)', color: '#fff', padding: '12px 20px', borderRadius: '8px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Send size={16} /> Submit
        </button>
      </form>
    </div>
  );
}

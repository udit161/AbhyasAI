import React, { useState, useEffect } from 'react';
import { X, CheckCircle2, AlertCircle } from 'lucide-react';
import { generateQuiz } from '../../services/api';

export default function QuizModal({ isOpen, onClose, currentTime }) {
  const [questions, setQuestions] = useState([]);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchQuiz();
    }
  }, [isOpen]);

  const fetchQuiz = async () => {
    setLoading(true);
    setSubmitted(false);
    setSelectedAnswers({});
    try {
      const data = await generateQuiz('video_sample_1', currentTime, 3);
      setQuestions(data.questions);
    } catch (err) {
      console.error("Quiz generation error", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      backdropFilter: 'blur(4px)'
    }}>
      <div className="glass-panel" style={{ width: '90%', maxWidth: '600px', padding: '24px', maxHeight: '85vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700' }}>Context Check Quiz</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Generated strictly from material covered up to current timestamp</p>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', color: 'var(--text-muted)' }}>
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>Generating questions from watched transcript...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {questions.map((q, idx) => (
              <div key={q.id} style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <p style={{ fontWeight: '600', marginBottom: '12px', fontSize: '0.92rem' }}>{idx + 1}. {q.question}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {q.options.map((opt, oIdx) => (
                    <button
                      key={oIdx}
                      onClick={() => !submitted && setSelectedAnswers({ ...selectedAnswers, [q.id]: oIdx })}
                      style={{
                        textAlign: 'left',
                        padding: '10px 14px',
                        borderRadius: '6px',
                        background: selectedAnswers[q.id] === oIdx ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.03)',
                        border: selectedAnswers[q.id] === oIdx ? '1px solid var(--accent-blue)' : '1px solid transparent',
                        color: '#fff',
                        fontSize: '0.85rem'
                      }}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
                {submitted && (
                  <div style={{ marginTop: '10px', fontSize: '0.8rem', color: '#60a5fa' }}>
                    <strong>Explanation:</strong> {q.explanation}
                  </div>
                )}
              </div>
            ))}

            {!submitted ? (
              <button
                onClick={() => setSubmitted(true)}
                style={{ background: 'var(--accent-blue)', color: '#fff', padding: '12px', borderRadius: '8px', fontWeight: '600' }}
              >
                Submit Answers
              </button>
            ) : (
              <button
                onClick={fetchQuiz}
                style={{ background: 'var(--accent-purple)', color: '#fff', padding: '12px', borderRadius: '8px', fontWeight: '600' }}
              >
                Regenerate New Quiz
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

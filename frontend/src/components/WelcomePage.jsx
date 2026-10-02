import React, { useState } from 'react';
import { BookOpen, Mic, Zap, ChevronRight, X, Mail, Lock, User } from 'lucide-react';

/* ─── tiny modal for Login / Signup ─── */
function AuthModal({ mode, onClose }) {
  const isLogin = mode === 'login';

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)',
      animation: 'fadeIn 0.2s ease'
    }}>
      <div className="glass-panel" style={{
        width: '100%', maxWidth: '400px', padding: '36px 32px',
        position: 'relative', animation: 'slideUp 0.25s ease'
      }}>
        {/* close */}
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', color: 'var(--text-muted)' }}
        >
          <X size={18} />
        </button>

        {/* logo mark */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
          <div style={{
            width: 36, height: 36, borderRadius: '10px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Zap size={18} color="#fff" />
          </div>
          <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>AbhyasAI</span>
        </div>

        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '6px' }}>
          {isLogin ? 'Welcome back' : 'Create account'}
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '28px' }}>
          {isLogin ? 'Sign in to continue your learning journey.' : 'Start your personalised AI learning experience.'}
        </p>

        <form style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}
          onSubmit={e => e.preventDefault()}>

          {!isLogin && (
            <InputField icon={<User size={15} />} placeholder="Full name" type="text" />
          )}
          <InputField icon={<Mail size={15} />} placeholder="Email address" type="email" />
          <InputField icon={<Lock size={15} />} placeholder="Password" type="password" />

          {isLogin && (
            <div style={{ textAlign: 'right', marginTop: '-6px' }}>
              <a href="#" style={{ fontSize: '0.78rem', color: 'var(--accent-blue)', textDecoration: 'none' }}>
                Forgot password?
              </a>
            </div>
          )}

          <button
            type="submit"
            style={{
              marginTop: '8px',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              color: '#fff', padding: '12px', borderRadius: '10px',
              fontWeight: 600, fontSize: '0.95rem',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
              boxShadow: '0 4px 24px rgba(59,130,246,0.35)'
            }}
          >
            {isLogin ? 'Sign In' : 'Get Started'} <ChevronRight size={16} />
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          {isLogin ? "Don't have an account? " : 'Already have an account? '}
          <a href="#" style={{ color: 'var(--accent-blue)', textDecoration: 'none', fontWeight: 500 }}
            onClick={e => { e.preventDefault(); onClose(isLogin ? 'signup' : 'login'); }}>
            {isLogin ? 'Sign up' : 'Sign in'}
          </a>
        </p>
      </div>
    </div>
  );
}

function InputField({ icon, placeholder, type }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '10px',
      background: 'rgba(15,23,42,0.7)', border: '1px solid var(--border-color)',
      borderRadius: '10px', padding: '11px 14px'
    }}>
      <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>{icon}</span>
      <input
        type={type}
        placeholder={placeholder}
        style={{
          background: 'transparent', border: 'none', outline: 'none',
          color: 'var(--text-main)', fontSize: '0.88rem', width: '100%'
        }}
      />
    </div>
  );
}

/* ─── feature pill ─── */
function FeaturePill({ icon, label }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '7px',
      background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border-color)',
      borderRadius: '999px', padding: '6px 14px', fontSize: '0.8rem',
      color: 'var(--text-muted)'
    }}>
      {icon}
      <span>{label}</span>
    </div>
  );
}

/* ─── main welcome page ─── */
export default function WelcomePage({ onEnter }) {
  const [modal, setModal] = useState(null); // 'login' | 'signup' | null

  const handleModalClose = (switchTo) => {
    if (switchTo === 'login' || switchTo === 'signup') {
      setModal(switchTo);
    } else {
      setModal(null);
    }
  };

  return (
    <>
      {/* ── hero section ── */}
      <div style={{
        position: 'relative', zIndex: 10,
        minHeight: '100vh',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '24px'
      }}>

        {/* nav bar */}
        <nav style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 20,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 40px',
          background: 'rgba(15,23,42,0.55)',
          backdropFilter: 'blur(14px)',
          borderBottom: '1px solid var(--border-color)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: 32, height: 32, borderRadius: '8px',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Zap size={16} color="#fff" />
            </div>
            <span style={{ fontWeight: 700, fontSize: '1rem', letterSpacing: '-0.3px' }}>AbhyasAI</span>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              id="nav-login-btn"
              onClick={() => setModal('login')}
              style={{
                background: 'transparent',
                border: '1px solid var(--border-color)',
                color: 'var(--text-main)', padding: '8px 20px',
                borderRadius: '8px', fontSize: '0.85rem', fontWeight: 500
              }}
            >
              Log In
            </button>
            <button
              id="nav-signup-btn"
              onClick={() => setModal('signup')}
              style={{
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                color: '#fff', padding: '8px 20px',
                borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600,
                boxShadow: '0 2px 16px rgba(59,130,246,0.4)'
              }}
            >
              Sign Up
            </button>
          </div>
        </nav>

        {/* hero card */}
        <div className="glass-panel" style={{
          maxWidth: '680px', width: '100%',
          padding: '52px 48px',
          textAlign: 'center',
          boxShadow: '0 8px 48px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.06)',
          animation: 'slideUp 0.4s ease'
        }}>
          {/* badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            background: 'linear-gradient(90deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))',
            border: '1px solid rgba(139,92,246,0.35)',
            borderRadius: '999px', padding: '4px 14px',
            fontSize: '0.75rem', color: '#a78bfa', fontWeight: 500,
            marginBottom: '28px', letterSpacing: '0.5px'
          }}>
            <Zap size={12} /> AI-POWERED LEARNING
          </div>

          <h1 style={{
            fontSize: 'clamp(2rem, 5vw, 3rem)',
            fontWeight: 800, lineHeight: 1.15,
            background: 'linear-gradient(135deg, #f8fafc 30%, #8b5cf6)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            marginBottom: '18px'
          }}>
            Learn Smarter,<br />Not Harder
          </h1>

          <p style={{
            fontSize: '1rem', color: 'var(--text-muted)',
            lineHeight: 1.7, maxWidth: '480px', margin: '0 auto 36px'
          }}>
            AbhyasAI combines timestamp-aware AI tutoring with mock interview practice —
            all inside a single, beautiful learning environment.
          </p>

          {/* feature pills */}
          <div style={{
            display: 'flex', flexWrap: 'wrap', gap: '10px',
            justifyContent: 'center', marginBottom: '40px'
          }}>
            <FeaturePill icon={<BookOpen size={13} />} label="Context-aware Q&A" />
            <FeaturePill icon={<Zap size={13} />} label="AI-generated Quizzes" />
            <FeaturePill icon={<Mic size={13} />} label="Mock Interviews" />
          </div>

          {/* CTA buttons */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              id="hero-signup-btn"
              onClick={() => setModal('signup')}
              style={{
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                color: '#fff', padding: '14px 32px',
                borderRadius: '12px', fontWeight: 700, fontSize: '0.95rem',
                display: 'flex', alignItems: 'center', gap: '8px',
                boxShadow: '0 4px 24px rgba(59,130,246,0.4)'
              }}
            >
              Get Started Free <ChevronRight size={16} />
            </button>
            <button
              id="hero-login-btn"
              onClick={() => setModal('login')}
              style={{
                background: 'rgba(255,255,255,0.07)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-main)', padding: '14px 32px',
                borderRadius: '12px', fontWeight: 600, fontSize: '0.95rem'
              }}
            >
              Log In
            </button>
          </div>

          {/* enter app link */}
          {onEnter && (
            <p style={{ marginTop: '24px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Already set up?{' '}
              <a href="#" style={{ color: 'var(--accent-cyan)', textDecoration: 'none' }}
                onClick={e => { e.preventDefault(); onEnter(); }}>
                Go to the app →
              </a>
            </p>
          )}
        </div>

        {/* subtle bottom glow */}
        <div style={{
          position: 'fixed', bottom: 0, left: '50%', transform: 'translateX(-50%)',
          width: '600px', height: '200px', pointerEvents: 'none',
          background: 'radial-gradient(ellipse at center bottom, rgba(59,130,246,0.18) 0%, transparent 70%)'
        }} />
      </div>

      {/* auth modal */}
      {modal && <AuthModal mode={modal} onClose={handleModalClose} />}

      <style>{`
        @keyframes fadeIn  { from { opacity: 0 } to { opacity: 1 } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(24px) } to { opacity: 1; transform: translateY(0) } }
      `}</style>
    </>
  );
}

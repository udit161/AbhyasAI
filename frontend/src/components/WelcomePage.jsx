import React, { useState } from 'react';
import { Mail, Lock, User, ArrowRight } from 'lucide-react';
import HangingCard from './HangingCard';

/* ── Bitcount Grid Double font style (reused everywhere) ── */
const BITCOUNT = {
  fontFamily: '"Bitcount Grid Double", system-ui',
  fontOpticalSizing: 'auto',
  fontStyle: 'normal',
  fontVariationSettings: '"slnt" 0, "CRSV" 0.5, "ELSH" 0, "ELXP" 0',
};

/* ─── reusable input ─── */
function InputField({ icon, placeholder, type, id }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '10px',
      background: 'rgba(255,255,255,0.05)',
      border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: '10px', padding: '11px 14px',
      transition: 'border-color 0.2s',
    }}
      onFocus={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.45)'}
      onBlur={e  => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)'}
    >
      <span style={{ color: 'rgba(255,255,255,0.4)', flexShrink: 0 }}>{icon}</span>
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        style={{
          background: 'transparent', border: 'none', outline: 'none',
          color: '#fff', fontSize: '0.88rem', width: '100%',
        }}
      />
    </div>
  );
}

/* ─── artistic numbered feature row ─── */
const FEATURES = [
  { n: '01', title: 'Context-aware Q&A',    sub: 'Ask anything, grounded in what you watched' },
  { n: '02', title: 'AI-generated Quizzes', sub: 'Test yourself at the perfect moment'          },
  { n: '03', title: 'Mock Interviews',      sub: 'Practise until confidence becomes instinct'   },
];

function FeatureRow({ n, title, sub }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: '16px',
      padding: '10px 0',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
    }}>
      {/* big dim counter */}
      <span style={{
        ...BITCOUNT,
        fontWeight: 900,
        fontSize: '1.6rem',
        lineHeight: 1,
        color: 'rgba(255,255,255,0.10)',
        minWidth: '36px',
        paddingTop: '2px',
        userSelect: 'none',
      }}>{n}</span>

      <div>
        <div style={{
          ...BITCOUNT,
          fontWeight: 700,
          fontSize: '0.95rem',
          color: 'rgba(255,255,255,0.85)',
          letterSpacing: '0.2px',
          marginBottom: '3px',
        }}>{title}</div>
        <div style={{
          fontStyle: 'italic',
          fontSize: '0.75rem',
          color: 'rgba(255,255,255,0.35)',
          letterSpacing: '0.1px',
        }}>{sub}</div>
      </div>
    </div>
  );
}

/* ─── main component ─── */
export default function WelcomePage({ onEnter }) {
  const [mode, setMode] = useState('signup'); // 'signup' | 'login'
  const isLogin = mode === 'login';

  return (
    <>
      {/* ── physics hanging card ── */}
      <HangingCard />

      {/* ── full-height centred wrapper ── */}
      <div style={{
        position: 'relative', zIndex: 10,
        minHeight: '100vh',
        display: 'flex', alignItems: 'center',
        justifyContent: 'flex-end',   /* push card to the right */
        padding: '24px 5vw 24px 420px', /* left pad clears the shifted hanging card */
      }}>

        {/* ── split card ── */}
        <div style={{
          display: 'flex',
          width: '100%', maxWidth: '900px',
          minHeight: '560px',
          /* very transparent glass */
          background: 'rgba(15, 23, 42, 0.30)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.10)',
          borderRadius: '20px',
          overflow: 'hidden',
          boxShadow: '0 24px 80px rgba(0,0,0,0.45)',
          animation: 'slideUp 0.4s ease 0.2s both',
        }}>

          {/* ════ LEFT PANEL — branding ════ */}
          <div style={{
            flex: '1 1 50%',
            padding: '48px 40px',
            display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
            borderRight: '1px solid rgba(255,255,255,0.07)',
          }}>


            {/* centre content */}
            <div>


              <h1 style={{
                ...BITCOUNT,
                fontWeight: 700,
                fontSize: 'clamp(1.8rem, 3.5vw, 2.8rem)',
                lineHeight: 1.18,
                color: '#ffffff',
                textShadow: '0 0 40px rgba(255,255,255,0.45), 0 0 80px rgba(255,255,255,0.15)',
                marginBottom: '16px',
                letterSpacing: '0.5px',
              }}>
                Learn Smarter,<br />Not Harder
              </h1>

              <p style={{
                fontSize: '0.9rem', color: 'rgba(255,255,255,0.5)',
                lineHeight: 1.7, marginBottom: '32px',
              }}>
                Timestamp-aware AI tutoring + mock interview practice — all in one
                beautiful environment.
              </p>

              {/* artistic feature list */}
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {FEATURES.map(f => <FeatureRow key={f.n} {...f} />)}
              </div>
            </div>

            {/* dev shortcut */}
            {onEnter && (
              <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.3)', marginTop: '8px' }}>
                Already set up?{' '}
                <a href="#" style={{ color: 'rgba(255,255,255,0.6)', textDecoration: 'none' }}
                  onClick={e => { e.preventDefault(); onEnter(); }}>
                  Go to app →
                </a>
              </p>
            )}
          </div>

          {/* ════ RIGHT PANEL — auth form ════ */}
          <div style={{
            flex: '1 1 50%',
            padding: '48px 40px',
            display: 'flex', flexDirection: 'column', justifyContent: 'center',
          }}>

            {/* tab switcher */}
            <div style={{
              display: 'flex', gap: '0',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.10)',
              borderRadius: '10px', padding: '4px',
              marginBottom: '32px',
            }}>
              {['signup', 'login'].map(m => (
                <button
                  key={m}
                  id={`tab-${m}`}
                  onClick={() => setMode(m)}
                  style={{
                    flex: 1, padding: '9px',
                    borderRadius: '7px', fontSize: '0.85rem', fontWeight: 600,
                    background: mode === m
                      ? 'rgba(255,255,255,0.14)'
                      : 'transparent',
                    border: `1px solid ${mode === m ? 'rgba(255,255,255,0.35)' : 'transparent'}`,
                    color: mode === m ? '#fff' : 'rgba(255,255,255,0.38)',
                    boxShadow: mode === m ? '0 0 18px rgba(255,255,255,0.12), 0 2px 8px rgba(0,0,0,0.3)' : 'none',
                    transition: 'all 0.2s',
                  }}
                >
                  {m === 'signup' ? 'Create Account' : 'Log In'}
                </button>
              ))}
            </div>

            <h2 style={{ ...BITCOUNT, fontWeight: 700, fontSize: '1.5rem', marginBottom: '6px', letterSpacing: '0.3px' }}>
              {isLogin ? 'Welcome back 👋' : 'Get started free'}
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.4)', marginBottom: '28px' }}>
              {isLogin
                ? 'Sign in to continue your learning journey.'
                : 'No credit card required. Start learning in seconds.'}
            </p>

            {/* form */}
            <form style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}
              onSubmit={e => e.preventDefault()}>

              {!isLogin && (
                <InputField id="inp-name" icon={<User size={15} />} placeholder="Full name" type="text" />
              )}
              <InputField id="inp-email" icon={<Mail size={15} />} placeholder="Email address" type="email" />
              <InputField id="inp-password" icon={<Lock size={15} />} placeholder="Password" type="password" />

              {isLogin && (
                <div style={{ textAlign: 'right', marginTop: '-4px' }}>
                  <a href="#" style={{ fontSize: '0.77rem', color: 'rgba(255,255,255,0.55)', textDecoration: 'none' }}>
                    Forgot password?
                  </a>
                </div>
              )}

              <button
                id="form-submit-btn"
                type="submit"
                style={{
                  marginTop: '8px',
                  background: 'rgba(255,255,255,0.92)',
                  color: '#0a0a0f', padding: '13px',
                  borderRadius: '10px', fontWeight: 700, fontSize: '0.95rem',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                  boxShadow: '0 0 32px rgba(255,255,255,0.20), 0 4px 20px rgba(0,0,0,0.4)',
                }}
              >
                {isLogin ? 'Sign In' : 'Create Account'}
                <ArrowRight size={16} />
              </button>
            </form>

            <p style={{ textAlign: 'center', marginTop: '22px', fontSize: '0.81rem', color: 'rgba(255,255,255,0.35)' }}>
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <a href="#"
                style={{ color: 'rgba(255,255,255,0.65)', textDecoration: 'none', fontWeight: 600 }}
                onClick={e => { e.preventDefault(); setMode(isLogin ? 'signup' : 'login'); }}>
                {isLogin ? 'Sign up free' : 'Sign in'}
              </a>
            </p>
          </div>
        </div>

        {/* ambient glow */}
        <div style={{
          position: 'fixed', bottom: 0, left: '50%', transform: 'translateX(-50%)',
          width: '700px', height: '220px', pointerEvents: 'none',
          background: 'radial-gradient(ellipse at center bottom, rgba(255,255,255,0.06) 0%, transparent 70%)',
        }} />
      </div>

      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(28px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        input::placeholder { color: rgba(255,255,255,0.28); }
      `}</style>
    </>
  );
}

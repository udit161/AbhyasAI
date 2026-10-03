/**
 * HangingCard.jsx
 *
 * A physics-based ID card that hangs from the left edge of the screen
 * via an animated swirly lanyard.
 *
 * Physics model:
 *   - Pendulum with spring/damping on the swing angle (theta)
 *   - Mouse / touch drag sets the target angle in real-time
 *   - Idle: gentle sinusoidal sway keeps it alive
 *   - Lanyard: SVG cubic-bezier whose control-points oscillate → swirly look
 */

import React, { useRef, useEffect, useCallback } from 'react';

/* ── Bitcount Grid Double font style ── */
const BITCOUNT = {
  fontFamily: '"Bitcount Grid Double", system-ui',
  fontOpticalSizing: 'auto',
  fontStyle: 'normal',
  fontVariationSettings: '"slnt" 0, "CRSV" 0.5, "ELSH" 0, "ELXP" 0',
};

/* ── layout constants ── */
const CARD_W   = 336;          // 240 × 1.4
const CARD_H   = 476;          // 340 × 1.4
const ANC_X    = 60;
const ANC_Y    = -8;
const ROPE_LEN = 380;
const REST_ANG = 0.42;         // shifted ~20% right (was 0.20)

/* ── spring constants ── */
const STIFFNESS  = 0.042;    // snappier drag response
const DAMPING    = 0.88;     // less damped → natural overshoot after release

/* multi-sine idle — superposition makes motion feel organic */
const idleTarget = (t) =>
  REST_ANG
  + 0.13 * Math.sin(t * 0.55)               // slow primary sway
  + 0.045 * Math.sin(t * 1.80 + 0.8)       // mid wobble
  + 0.018 * Math.sin(t * 3.60 + 1.4);      // quick micro-jitter

/* extra rotational twist independent of pendulum angle */
const twistDeg = (t) =>
    3.5 * Math.sin(t * 1.30)
  + 1.2 * Math.sin(t * 2.90 + 0.5)
  + 0.6 * Math.sin(t * 5.10 + 2.1);

/* ── helpers ── */
const toCard = (theta) => ({
  cx: ANC_X + ROPE_LEN * Math.sin(theta),
  cy: ANC_Y + ROPE_LEN * Math.cos(theta),
});

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/* ═══════════════════════════════════════════════════ */
export default function HangingCard() {
  const cardRef  = useRef(null);
  const svgRef   = useRef(null);
  const state    = useRef({
    theta    : REST_ANG,
    omega    : 0.04,
    time     : 0,
    dragging : false,
    targTheta: REST_ANG,
    raf      : null,
  });

  /* ── animation loop ── */
  useEffect(() => {
    const s = state.current;

    const tick = () => {
      s.time += 0.016;

      /* target angle */
      const targ = s.dragging ? s.targTheta : idleTarget(s.time);

      /* spring physics */
      const alpha = -STIFFNESS * (s.theta - targ);
      s.omega    += alpha;
      s.omega    *= DAMPING;
      s.theta    += s.omega;

      /* clamp so card doesn't fly off screen */
      s.theta = clamp(s.theta, -0.9, 1.1);

      /* pendulum rotation + independent twist wobble */
      const rotDeg = s.theta * (180 / Math.PI) + twistDeg(s.time);
      const { cx, cy } = toCard(s.theta);

      /* ── update card DOM ── */
      if (cardRef.current) {
        const el = cardRef.current;
        el.style.left            = `${cx - CARD_W / 2}px`;
        el.style.top             = `${cy - CARD_H / 2}px`;
        el.style.transform       = `rotate(${rotDeg}deg)`;
        el.style.transformOrigin = `${CARD_W / 2}px 0px`; // pivot at lanyard hole
      }

      /* ── update SVG lanyard ── */
      if (svgRef.current) {
        // card top-centre (lanyard attachment)
        const tx = cx;
        const ty = cy - CARD_H / 2 + 6; // just inside the hole

        // smooth, calm lanyard oscillation — scales gently with speed
        const speed   = Math.abs(s.omega) * 40;        // damped multiplier
        const wiggle1 = Math.sin(s.time * 1.6) * (5 + speed * 1.8);
        const wiggle2 = Math.sin(s.time * 1.1 + 1.0) * (3 + speed * 1.0);

        const cp1x = ANC_X + (tx - ANC_X) * 0.30 + wiggle1;
        const cp1y = ANC_Y + 120 + Math.sin(s.time * 0.9) * 4;
        const cp2x = tx - 28 + wiggle2;
        const cp2y = ty - 100;

        const d = `M ${ANC_X} ${ANC_Y} C ${cp1x} ${cp1y} ${cp2x} ${cp2y} ${tx} ${ty}`;

        /* shadow */
        const sh = svgRef.current.querySelector('#lp-sh');
        if (sh) sh.setAttribute('d', d);
        /* main */
        const lp = svgRef.current.querySelector('#lp');
        if (lp) lp.setAttribute('d', d);
        /* glow */
        const gl = svgRef.current.querySelector('#lp-gl');
        if (gl) gl.setAttribute('d', d);
      }

      s.raf = requestAnimationFrame(tick);
    };

    s.raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(s.raf);
  }, []);

  /* ── pointer interaction ── */
  const onPointerDown = useCallback((e) => {
    state.current.dragging = true;
    cardRef.current?.setPointerCapture(e.pointerId);
    if (cardRef.current) cardRef.current.style.cursor = 'grabbing';
  }, []);

  const onPointerMove = useCallback((e) => {
    if (!state.current.dragging) return;
    const dx = e.clientX - ANC_X;
    const dy = Math.max(e.clientY - ANC_Y, 20); // avoid flipping
    state.current.targTheta = clamp(Math.atan2(dx, dy), -0.85, 1.05);
  }, []);

  const onPointerUp = useCallback(() => {
    state.current.dragging  = false;
    state.current.targTheta = REST_ANG;
    if (cardRef.current) cardRef.current.style.cursor = 'grab';
  }, []);

  /* ── render ── */
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 50, pointerEvents: 'none', animation: 'dropIn 1.0s cubic-bezier(0.22, 1, 0.36, 1) 1.2s both' }}>

      {/* ═══ SVG lanyard ═══ */}
      <svg
        ref={svgRef}
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', overflow: 'visible', pointerEvents: 'none' }}
      >
        <defs>
          {/* lanyard gradient */}
          <linearGradient id="lanyardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   stopColor="#d4d4d8" stopOpacity="0.9" />
            <stop offset="45%"  stopColor="#ffffff" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#a1a1aa" stopOpacity="0.9" />
          </linearGradient>
          {/* glow filter */}
          <filter id="lanyardGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* wall mount bracket */}
        <rect x={ANC_X - 8} y={-2} width={16} height={28} rx={5}
          fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.28)" strokeWidth="1.5" />
        <circle cx={ANC_X} cy={24} r={7}
          fill="rgba(10,10,15,0.85)" stroke="rgba(255,255,255,0.35)" strokeWidth="2" />

        {/* shadow */}
        <path id="lp-sh" stroke="rgba(0,0,0,0.4)" strokeWidth="7"
          fill="none" strokeLinecap="round" />
        {/* main lanyard */}
        <path id="lp" stroke="url(#lanyardGrad)" strokeWidth="3.5"
          fill="none" strokeLinecap="round" filter="url(#lanyardGlow)" />
        {/* bright glow line on top */}
        <path id="lp-gl" stroke="rgba(255,255,255,0.55)" strokeWidth="1.2"
          fill="none" strokeLinecap="round" />
      </svg>

      {/* ═══ Card ═══ */}
      <div
        ref={cardRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        style={{
          position     : 'absolute',
          top          : 0, left: 0,
          width        : CARD_W,
          height       : CARD_H,
          cursor       : 'grab',
          pointerEvents: 'all',
          userSelect   : 'none',
          willChange   : 'transform',
          touchAction  : 'none',
        }}
      >
        {/* lanyard hole */}
        <div style={{
          position   : 'absolute',
          top        : -7,
          left       : '50%',
          transform  : 'translateX(-50%)',
          width      : 18,
          height     : 18,
          borderRadius: '50%',
          background : 'rgba(0,0,0,0.85)',
          border     : '2px solid rgba(255,255,255,0.35)',
          zIndex     : 2,
          boxShadow  : 'inset 0 1px 3px rgba(0,0,0,0.8)',
        }} />

        {/* card body */}
        <div style={{
          width          : '100%',
          height         : '100%',
          background     : 'rgba(10, 16, 36, 0.52)',
          backdropFilter : 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border         : '1px solid rgba(255,255,255,0.16)',
          borderRadius   : '22px',
          overflow       : 'hidden',
          boxShadow      : `
            0 32px 80px rgba(0,0,0,0.65),
            0  8px 24px rgba(0,0,0,0.40),
            inset 0 1px 0 rgba(255,255,255,0.12)
          `,
          display        : 'flex',
          flexDirection  : 'column',
          alignItems     : 'center',
          padding        : '36px 25px 22px',
          position       : 'relative',
        }}>

          {/* top colour stripe — white glow */}
          <div style={{
            position  : 'absolute',
            top       : 0, left: 0, right: 0,
            height    : 6,
            background: 'linear-gradient(90deg, #71717a, #ffffff, #71717a)',
            boxShadow : '0 0 16px rgba(255,255,255,0.35)',
          }} />

          {/* shimmer overlay */}
          <div style={{
            position  : 'absolute',
            inset     : 0,
            background: 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%)',
            pointerEvents: 'none',
          }} />

          {/* brand text — logo removed, text is the hero */}
          <div style={{
            marginTop   : '36px',
            marginBottom: '6px',
            textAlign   : 'center',
          }}>
            <div style={{ ...BITCOUNT, fontWeight: 900, fontSize: '2.6rem', letterSpacing: '1px', lineHeight: 1.1 }}>
              AbhyasAI
            </div>
            <div style={{
              ...BITCOUNT,
              fontWeight: 400,
              fontSize: '0.95rem',
              color       : 'rgba(255,255,255,0.38)',
              letterSpacing: '3px',
              textTransform: 'uppercase',
              marginTop: '8px',
              marginBottom: '24px',
            }}>
              Learning Platform
            </div>
          </div>

          {/* divider */}
          <div style={{
            width     : '100%',
            height    : '1px',
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.14), transparent)',
            marginBottom: '17px',
          }} />

          {/* info rows */}
          {[
            ['ROLE',   'AI Tutor & Coach'],
            ['ACCESS', 'Full Platform'],
            ['TIER',   'Pro Student'],
            ['VALID',  '2025 – 2026'],
          ].map(([k, v]) => (
            <div key={k} style={{
              width          : '100%',
              display        : 'flex',
              justifyContent : 'space-between',
              marginBottom   : '13px',
              fontSize       : '1.05rem',
            }}>
              <span style={{ color: 'rgba(255,255,255,0.32)', fontWeight: 700, letterSpacing: '0.5px' }}>{k}</span>
              <span style={{ color: 'rgba(255,255,255,0.82)', fontWeight: 500 }}>{v}</span>
            </div>
          ))}

          {/* barcode */}
          <div style={{ marginTop: 'auto', display: 'flex', gap: '3px', paddingTop: '17px' }}>
            {Array.from({ length: 28 }, (_, i) => (
              <div key={i} style={{
                width       : i % 5 === 0 ? 5.5 : i % 3 === 0 ? 3.5 : 2,
                height      : 39,
                background  : 'rgba(255,255,255,0.28)',
                borderRadius: '1px',
              }} />
            ))}
          </div>
          <div style={{
            fontSize     : '0.73rem',
            color        : 'rgba(255,255,255,0.22)',
            letterSpacing: '2px',
            marginTop    : '6px',
          }}>
            ABHYAS-ID-2025
          </div>
        </div>
      </div>

      {/* keyframes for card entrance only */}
      <style>{`
        @keyframes dropIn {
          from { opacity: 0; transform: translateY(-30px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

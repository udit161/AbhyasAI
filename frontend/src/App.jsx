import { useState } from 'react';
import { SparkBadge } from './shaders/spark-badge/SparkBadge';
import './shaders/threeui.css';
import VideoPlayer from './components/player/VideoPlayer';
import WelcomePage from './components/WelcomePage';

export default function App() {
  const [page, setPage] = useState('welcome'); // 'welcome' | 'app'

  return (
    <>
      {/* ── rain background ── */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0 }}>
        <SparkBadge
          speed={0.40}
          particleAmount={0.01}
          rainAmount={0.004}
          turbulence={0.20}
          spread={0.85}
        />
      </div>

      {page === 'welcome' ? (
        <WelcomePage onEnter={() => setPage('app')} />
      ) : (
        /* Liquid glass video player — sits above background */
        <VideoPlayer />
      )}
    </>
  );
}

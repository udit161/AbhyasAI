import { useState } from 'react';
import { SparkBadge } from './shaders/spark-badge/SparkBadge';
import './shaders/threeui.css';
import VideoPlayer from './components/player/VideoPlayer';
import WelcomePage from './components/WelcomePage';

export default function App() {
  const [page, setPage] = useState('welcome'); // 'welcome' | 'app'

  return (
    <>
      {/* Full-viewport animated background — always visible */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0 }}>
        <SparkBadge
          speed={1.00}
          particleAmount={1.00}
          rainAmount={1.00}
          turbulence={1.00}
          spread={1.00}
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

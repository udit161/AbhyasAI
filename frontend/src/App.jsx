import { SparkBadge } from './shaders/spark-badge/SparkBadge';
import './shaders/threeui.css';
import VideoPlayer from './components/player/VideoPlayer';

export default function App() {
  return (
    <>
      {/* Full-viewport animated background */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0 }}>
        <SparkBadge
          speed={1.00}
          particleAmount={1.00}
          rainAmount={1.00}
          turbulence={1.00}
          spread={1.00}
        />
      </div>
      {/* Liquid glass video player — sits above background */}
      <VideoPlayer />
    </>
  );
}

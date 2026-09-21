import React, { useState } from 'react';
import Header from './components/common/Header';
import VideoPlayer from './components/player/VideoPlayer';
import LearningAssistant from './components/assistant/LearningAssistant';
import QuizModal from './components/assistant/QuizModal';
import MockInterview from './components/interview/MockInterview';
import ResourceUploader from './components/common/ResourceUploader';

export default function App() {
  const [activeTab, setActiveTab] = useState('learning');
  const [currentTime, setCurrentTime] = useState(1122.0); // Default set to 18:42
  const [isPlaying, setIsPlaying] = useState(false);
  const [isQuizOpen, setIsQuizOpen] = useState(false);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      <main style={{ flex: 1, padding: '0 16px 24px 16px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        {activeTab === 'learning' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <ResourceUploader />
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '16px' }}>
              <VideoPlayer
                currentTime={currentTime}
                setCurrentTime={setCurrentTime}
                isPlaying={isPlaying}
                setIsPlaying={setIsPlaying}
                onPauseAndAsk={() => setIsPlaying(false)}
              />
              <LearningAssistant
                currentTime={currentTime}
                onOpenQuiz={() => setIsQuizOpen(true)}
              />
            </div>
          </div>
        ) : (
          <MockInterview />
        )}
      </main>

      <QuizModal
        isOpen={isQuizOpen}
        onClose={() => setIsQuizOpen(false)}
        currentTime={currentTime}
      />
    </div>
  );
}

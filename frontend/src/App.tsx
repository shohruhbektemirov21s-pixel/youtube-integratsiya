import { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/common/Navbar';
import { ChannelList } from './components/channels/ChannelList';
import { VideoList } from './components/videos/VideoList';
import { SyncJobList } from './components/sync/SyncJobList';
import { SystemStatus } from './components/system/SystemStatus';
import { AuthModal } from './components/auth/AuthModal';
import { youtubeService } from './services/youtubeService';
import './App.css';

function MainLayout() {
  const [activeTab, setActiveTab] = useState<'channels' | 'videos' | 'sync' | 'system'>('channels');
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [backendOnline, setBackendOnline] = useState<boolean>(false);

  const checkInitialHealth = async () => {
    try {
      const res = await youtubeService.checkHealth();
      setBackendOnline(res.status === 'online');
    } catch {
      setBackendOnline(false);
    }
  };

  useEffect(() => {
    checkInitialHealth();
    const interval = setInterval(checkInitialHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f1f5f9', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        backendOnline={backendOnline}
      />

      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1.5rem' }}>
        {activeTab === 'channels' && <ChannelList onOpenAuth={() => setIsAuthModalOpen(true)} />}
        {activeTab === 'videos' && <VideoList />}
        {activeTab === 'sync' && <SyncJobList />}
        {activeTab === 'system' && <SystemStatus />}
      </main>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}

export default App;

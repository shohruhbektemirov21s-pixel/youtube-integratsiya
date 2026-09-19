import { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import { Navbar, type NavTab } from './components/common/Navbar';
import { ChannelList } from './components/channels/ChannelList';
import { PlaylistList } from './components/playlists/PlaylistList';
import { VideoList } from './components/videos/VideoList';
import { SyncJobList } from './components/sync/SyncJobList';
import { SystemStatus } from './components/system/SystemStatus';
import { AutomationDashboard } from './components/automation/AutomationDashboard';
import { AuthModal } from './components/auth/AuthModal';
import { youtubeService } from './services/youtubeService';
import './App.css';

function MainLayout() {
  const [activeTab, setActiveTab] = useState<NavTab>('automation');
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
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        backendOnline={backendOnline}
      />

      <main className="main-content">
        {activeTab === 'automation' && <AutomationDashboard />}
        {activeTab === 'channels' && <ChannelList onOpenAuth={() => setIsAuthModalOpen(true)} />}
        {activeTab === 'playlists' && <PlaylistList />}
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

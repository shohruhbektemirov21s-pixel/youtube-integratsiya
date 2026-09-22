import { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './context/useAuth';
import { AuthModal } from './components/auth/AuthModal';
import { Spinner } from './components/common/Spinner';
import { Navbar, type NavTab } from './components/common/Navbar';
import { ChannelList } from './components/channels/ChannelList';
import { PlaylistList } from './components/playlists/PlaylistList';
import { VideoList } from './components/videos/VideoList';
import { SyncJobList } from './components/sync/SyncJobList';
import { SystemStatus } from './components/system/SystemStatus';
import { AutomationDashboard } from './components/automation/AutomationDashboard';
import { AccountManagement } from './components/accounts/AccountManagement';
import { youtubeService } from './services/youtubeService';
import './App.css';

function MainLayout() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>('automation');
  const [backendOnline, setBackendOnline] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;

    const checkHealth = async () => {
      // Fon tabda so'rov yubormaymiz (mobil trafik va batareya)
      if (document.visibilityState !== 'visible') return;
      try {
        const res = await youtubeService.checkHealth();
        if (!cancelled) setBackendOnline(res.status === 'online');
      } catch {
        if (!cancelled) setBackendOnline(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        backendOnline={backendOnline}
        username={user?.username}
        onLogout={() => { void logout(); }}
      />

      <main className="main-content">
        {activeTab === 'automation' && <AutomationDashboard />}
        {activeTab === 'accounts' && <AccountManagement />}
        {activeTab === 'channels' && <ChannelList />}
        {activeTab === 'playlists' && <PlaylistList />}
        {activeTab === 'videos' && <VideoList />}
        {activeTab === 'sync' && <SyncJobList />}
        {activeTab === 'system' && <SystemStatus />}
      </main>
    </div>
  );
}

/**
 * Auth darvozasi.
 *
 * Backend `AllowAny` bo'lgani uchun bu qatlam ilgari umuman ulanmagan edi:
 * AuthModal yozilgan, lekin hech qayerdan chaqirilmasdi. Endi API
 * autentifikatsiya talab qiladi, shuning uchun darvoza majburiy.
 */
function AuthGate() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Spinner />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
          padding: '1.5rem',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '2.5rem' }}>📺</div>
        <h1 style={{ margin: 0, fontSize: '1.35rem' }}>YouTube AI Studio</h1>
        <p style={{ margin: 0, opacity: 0.7, maxWidth: '28rem' }}>
          Boshqaruv paneliga kirish uchun tizimga kiring.
        </p>
        {/* Darvoza modali yopilmaydi — yopish tugmasi hech narsa qilmaydi */}
        <AuthModal isOpen onClose={() => {}} />
      </div>
    );
  }

  return <MainLayout />;
}

export function App() {
  return (
    <AuthProvider>
      <AuthGate />
    </AuthProvider>
  );
}

export default App;

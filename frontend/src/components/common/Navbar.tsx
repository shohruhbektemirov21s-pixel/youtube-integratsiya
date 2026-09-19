import { useAuth } from '../../context/useAuth';

export type NavTab = 'channels' | 'playlists' | 'videos' | 'sync' | 'system';

interface NavbarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  onOpenAuth: () => void;
  backendOnline: boolean;
}

export function Navbar({ activeTab, onTabChange, onOpenAuth, backendOnline }: NavbarProps) {
  const { user, isAuthenticated, logout } = useAuth();

  const navItemStyle = (tab: NavTab) => ({
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    border: 'none',
    backgroundColor: activeTab === tab ? '#2563eb' : 'transparent',
    color: activeTab === tab ? '#ffffff' : '#475569',
    fontWeight: 500,
    cursor: 'pointer',
    fontSize: '0.9rem',
    transition: 'all 0.15s ease',
  });

  return (
    <header
      style={{
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        padding: '0.75rem 1.5rem',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div
        style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.75rem' }}>📺</span>
          <div>
            <h1 style={{ fontSize: '1.2rem', margin: 0, color: '#0f172a', fontWeight: 700 }}>
              YouTube Integratsiya
            </h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.1rem' }}>
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: backendOnline ? '#16a34a' : '#ef4444',
                }}
              />
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                {backendOnline ? 'API Online' : 'API Ulanmagan'}
              </span>
            </div>
          </div>
        </div>

        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button type="button" style={navItemStyle('channels')} onClick={() => onTabChange('channels')}>
            Kanallar
          </button>
          <button type="button" style={navItemStyle('playlists')} onClick={() => onTabChange('playlists')}>
            Playlistlar
          </button>
          <button type="button" style={navItemStyle('videos')} onClick={() => onTabChange('videos')}>
            Videolar
          </button>
          <button type="button" style={navItemStyle('sync')} onClick={() => onTabChange('sync')}>
            Audit Jurnali
          </button>
          <button type="button" style={navItemStyle('system')} onClick={() => onTabChange('system')}>
            Tizim Holati
          </button>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {isAuthenticated && user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>
                  {user.first_name || user.username}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{user.email}</div>
              </div>
              <button
                type="button"
                onClick={logout}
                style={{
                  padding: '0.4rem 0.8rem',
                  backgroundColor: '#f1f5f9',
                  color: '#475569',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  fontWeight: 500,
                }}
              >
                Chiqish
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={onOpenAuth}
              style={{
                padding: '0.45rem 1rem',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              Kirish / Ro'yxatdan o'tish
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export type NavTab = 'automation' | 'accounts' | 'channels' | 'playlists' | 'videos' | 'sync' | 'system';

interface NavbarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  backendOnline: boolean;
  username?: string;
  onLogout?: () => void;
}

export function Navbar({ activeTab, onTabChange, backendOnline, username, onLogout }: NavbarProps) {
  return (
    <>
      {/* Top Glassmorphic Navigation Bar */}
      <header className="app-header">
        <div className="app-header-inner">
          <div className="brand-section">
            <div className="brand-logo">📺</div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <h1 className="brand-title">YouTube AI Studio</h1>
                <div className="brand-badge">
                  <span className="pulse-dot" />
                  <span>{backendOnline ? '24/7 Server Faol' : 'Oflayn'}</span>
                </div>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                Hermes Agent • Flow AI 4x • Gemini 3.8 Flash • 19:00 Drop
              </div>
            </div>
          </div>

          {/* Desktop Nav Pills */}
          <nav className="desktop-nav">
            <button
              type="button"
              className={`nav-pill-btn ${activeTab === 'automation' ? 'active' : ''}`}
              onClick={() => onTabChange('automation')}
            >
              <span>⚡️</span> Boshqaruv & Flow AI
            </button>
            <button
              type="button"
              className={`nav-pill-btn ${activeTab === 'accounts' ? 'active' : ''}`}
              onClick={() => onTabChange('accounts')}
            >
              <span>👥</span> Akkauntlar (Kredit & Kanal)
            </button>
            <button
              type="button"
              className={`nav-pill-btn ${activeTab === 'channels' ? 'active' : ''}`}
              onClick={() => onTabChange('channels')}
            >
              <span>📺</span> Kanallar
            </button>
            <button
              type="button"
              className={`nav-pill-btn ${activeTab === 'playlists' ? 'active' : ''}`}
              onClick={() => onTabChange('playlists')}
            >
              <span>📑</span> Playlistlar
            </button>
            <button
              type="button"
              className={`nav-pill-btn ${activeTab === 'videos' ? 'active' : ''}`}
              onClick={() => onTabChange('videos')}
            >
              <span>🎬</span> Videolar
            </button>
            <button
              type="button"
              className={`nav-pill-btn ${activeTab === 'sync' ? 'active' : ''}`}
              onClick={() => onTabChange('sync')}
            >
              <span>📋</span> Audit
            </button>
            <button
              type="button"
              className={`nav-pill-btn ${activeTab === 'system' ? 'active' : ''}`}
              onClick={() => onTabChange('system')}
            >
              <span>⚙️</span> Tizim
            </button>
          </nav>

          {/* Right Status Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.35rem 0.75rem',
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.25)',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.78rem',
                fontWeight: 600,
                color: '#60a5fa',
              }}
            >
              <span>👤</span>
              <span>{username ?? 'Mehmon'}</span>
            </div>
            {onLogout && (
              <button
                type="button"
                onClick={onLogout}
                title="Tizimdan chiqish"
                style={{
                  marginLeft: '0.5rem',
                  padding: '0.35rem 0.75rem',
                  background: 'transparent',
                  border: '1px solid var(--border-color, rgba(148,163,184,0.3))',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--text-secondary, #94a3b8)',
                  cursor: 'pointer',
                }}
              >
                Chiqish
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Bottom Navigation Dock (Telegram Mini App Friendly) */}
      <nav className="mobile-bottom-nav">
        <button
          type="button"
          className={`bottom-nav-item ${activeTab === 'automation' ? 'active' : ''}`}
          onClick={() => onTabChange('automation')}
        >
          <span className="icon">⚡️</span>
          <span>Boshqaruv</span>
        </button>
        <button
          type="button"
          className={`bottom-nav-item ${activeTab === 'accounts' ? 'active' : ''}`}
          onClick={() => onTabChange('accounts')}
        >
          <span className="icon">👥</span>
          <span>Akkauntlar</span>
        </button>
        <button
          type="button"
          className={`bottom-nav-item ${activeTab === 'channels' ? 'active' : ''}`}
          onClick={() => onTabChange('channels')}
        >
          <span className="icon">📺</span>
          <span>Kanallar</span>
        </button>
        <button
          type="button"
          className={`bottom-nav-item ${activeTab === 'videos' ? 'active' : ''}`}
          onClick={() => onTabChange('videos')}
        >
          <span className="icon">🎬</span>
          <span>Videolar</span>
        </button>
        <button
          type="button"
          className={`bottom-nav-item ${activeTab === 'system' ? 'active' : ''}`}
          onClick={() => onTabChange('system')}
        >
          <span className="icon">⚙️</span>
          <span>Tizim</span>
        </button>
      </nav>
    </>
  );
}
export default Navbar;

import { useState, useEffect } from 'react';
import { youtubeService } from '../../services/youtubeService';
import type { FlowAIAccount, DetectedProfile } from '../../types/youtube';

type AccountFilter = 'all' | 'credits' | 'channels';

export function AccountManagement() {
  const [accounts, setAccounts] = useState<FlowAIAccount[]>([]);
  const [detectedProfiles, setDetectedProfiles] = useState<DetectedProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [inspectingId, setInspectingId] = useState<number | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [editingAccount, setEditingAccount] = useState<FlowAIAccount | null>(null);
  const [activeFilter, setActiveFilter] = useState<AccountFilter>('all');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [profileDir, setProfileDir] = useState('Profile 1');
  const [hasFlowCredits, setHasFlowCredits] = useState(true);
  const [creditsRemaining, setCreditsRemaining] = useState(1000);
  const [hasYoutubeChannel, setHasYoutubeChannel] = useState(false);
  const [youtubeChannelName, setYoutubeChannelName] = useState('');
  const [youtubeChannelId, setYoutubeChannelId] = useState('');

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [accRes, profRes] = await Promise.all([
        youtubeService.getFlowAccounts(),
        youtubeService.getDetectedChromeProfiles(),
      ]);
      setAccounts(accRes.results || []);
      setDetectedProfiles(profRes.profiles || []);
    } catch (err) {
      console.error('Failed to load accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: Partial<FlowAIAccount> = {
        name,
        email,
        profile_dir: profileDir,
        has_flow_credits: hasFlowCredits,
        credits_remaining: Number(creditsRemaining),
        has_youtube_channel: hasYoutubeChannel,
        youtube_channel_name: hasYoutubeChannel ? youtubeChannelName : '',
        youtube_channel_id: hasYoutubeChannel ? youtubeChannelId : '',
        is_active: true,
      };

      if (editingAccount) {
        await youtubeService.updateFlowAccount(editingAccount.id, payload);
        showToast(`✓ '${name}' muvaffaqiyatli tahrirlandi!`);
      } else {
        await youtubeService.createFlowAccount(payload);
        showToast(`✓ Yangi akkaunt '${name}' qo'shildi!`);
      }

      setIsAddModalOpen(false);
      setEditingAccount(null);
      resetForm();
      await loadData();
    } catch (err) {
      showToast('Xatolik: ' + (err as Error).message);
    }
  };

  const handleQuickAddFromDetected = async (p: DetectedProfile) => {
    try {
      await youtubeService.createFlowAccount({
        name: `${p.name} (${p.profile_dir})`,
        email: p.email,
        profile_dir: p.profile_dir,
        has_flow_credits: true,
        credits_remaining: 1000,
        initial_credits: 1000,
        has_youtube_channel: false,
        is_active: true,
      });
      showToast(`✓ Chrome profili (${p.profile_dir}) ulandi!`);
      await loadData();
    } catch (err) {
      showToast('Xatolik: ' + (err as Error).message);
    }
  };

  const handleInspect = async (acc: FlowAIAccount) => {
    setInspectingId(acc.id);
    try {
      await youtubeService.inspectAccount(acc.id, {
        credits_remaining: acc.credits_remaining,
        has_flow_credits: acc.credits_remaining > 0,
        has_youtube_channel: acc.has_youtube_channel,
      });
      showToast(`✓ '${acc.name}' brauzer holati yangilandi!`);
      await loadData();
    } catch (err) {
      showToast('Tekshirishda xatolik: ' + (err as Error).message);
    } finally {
      setInspectingId(null);
    }
  };

  const handleDelete = async (id: number, accName: string) => {
    if (!confirm(`'${accName}' akkauntini o'chirishni tasdiqlaysizmi?`)) return;
    try {
      await youtubeService.deleteFlowAccount(id);
      showToast(`🗑 '${accName}' o'chirildi.`);
      await loadData();
    } catch (err) {
      showToast('Oʻchirishda xatolik: ' + (err as Error).message);
    }
  };

  const openEdit = (acc: FlowAIAccount) => {
    setEditingAccount(acc);
    setName(acc.name);
    setEmail(acc.email);
    setProfileDir(acc.profile_dir);
    setHasFlowCredits(acc.has_flow_credits);
    setCreditsRemaining(acc.credits_remaining);
    setHasYoutubeChannel(acc.has_youtube_channel);
    setYoutubeChannelName(acc.youtube_channel_name || '');
    setYoutubeChannelId(acc.youtube_channel_id || '');
    setIsAddModalOpen(true);
  };

  const resetForm = () => {
    setName('');
    setEmail('');
    setProfileDir('Profile 1');
    setHasFlowCredits(true);
    setCreditsRemaining(1000);
    setHasYoutubeChannel(false);
    setYoutubeChannelName('');
    setYoutubeChannelId('');
  };

  // Filter accounts
  const filteredAccounts = accounts.filter((acc) => {
    if (activeFilter === 'credits') return acc.has_flow_credits && acc.credits_remaining > 0;
    if (activeFilter === 'channels') return acc.has_youtube_channel;
    return true;
  });

  const totalCredits = accounts.reduce((sum, a) => sum + (a.credits_remaining || 0), 0);
  const channelsCount = accounts.filter((a) => a.has_youtube_channel).length;

  return (
    <div>
      {/* Toast Alert */}
      {toastMessage && (
        <div className="senior-toast">
          <span>✨</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Cockpit Hero Banner */}
      <div className="cockpit-banner">
        <div className="cockpit-header">
          <div className="cockpit-title-group">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <span style={{ fontSize: '1.4rem' }}>👥</span>
              <h2>Mening Akkauntlarim & Profillar</h2>
            </div>
            <p>
              Qaysi akkauntda Flow AI krediti mavjudligi va qaysi birida YouTube kanal borligini to'liq nazorat qiling. Ro'yxatdan o'tishsiz to'g'ridan-to'g'ri ishlang.
            </p>
          </div>

          <div className="cockpit-actions">
            <button
              type="button"
              className="btn-senior-primary"
              onClick={() => {
                resetForm();
                setEditingAccount(null);
                setIsAddModalOpen(true);
              }}
            >
              <span>➕</span> Yangi Akkaunt Kiritish
            </button>
          </div>
        </div>
      </div>

      {/* Quick KPI Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.75rem' }}>
        <div
          className="senior-card"
          onClick={() => setActiveFilter('all')}
          style={{ cursor: 'pointer', border: activeFilter === 'all' ? '1px solid var(--accent-primary)' : undefined }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>JAMI AKKAUNTLAR</span>
            <span style={{ fontSize: '1.25rem' }}>📁</span>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#ffffff', margin: '0.35rem 0' }}>
            {accounts.length} ta
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--accent-success)' }}>Barchasi tizimga ulangan</div>
        </div>

        <div
          className="senior-card"
          onClick={() => setActiveFilter('credits')}
          style={{ cursor: 'pointer', border: activeFilter === 'credits' ? '1px solid #3b82f6' : undefined }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>FLOW AI KREDITLARI</span>
            <span style={{ fontSize: '1.25rem' }}>⚡️</span>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#38bdf8', margin: '0.35rem 0' }}>
            {totalCredits} kredit
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {accounts.filter((a) => a.has_flow_credits && a.credits_remaining > 0).length} ta akkauntda mavjud
          </div>
        </div>

        <div
          className="senior-card"
          onClick={() => setActiveFilter('channels')}
          style={{ cursor: 'pointer', border: activeFilter === 'channels' ? '1px solid #ef4444' : undefined }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>YOUTUBE KANALLAR</span>
            <span style={{ fontSize: '1.25rem' }}>📺</span>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#f87171', margin: '0.35rem 0' }}>
            {channelsCount} ta kanal
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            19:00 avto-yuklashga sozlangan
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
        <button
          type="button"
          className={`nav-pill-btn ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          Barchasi ({accounts.length})
        </button>
        <button
          type="button"
          className={`nav-pill-btn ${activeFilter === 'credits' ? 'active' : ''}`}
          onClick={() => setActiveFilter('credits')}
        >
          ⚡️ Kredit Bor ({accounts.filter((a) => a.has_flow_credits && a.credits_remaining > 0).length})
        </button>
        <button
          type="button"
          className={`nav-pill-btn ${activeFilter === 'channels' ? 'active' : ''}`}
          onClick={() => setActiveFilter('channels')}
        >
          📺 YouTube Kanal Ulangan ({channelsCount})
        </button>
      </div>

      {/* Account Cards Grid */}
      <div style={{ marginBottom: '2.5rem' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Akkauntlar yuklanmoqda...
          </div>
        ) : filteredAccounts.length === 0 ? (
          <div style={{ padding: '2.5rem', textAlign: 'center', background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
            Tanlangan filtr bo'yicha akkaunt topilmadi.
          </div>
        ) : (
          <div className="senior-grid">
            {filteredAccounts.map((acc) => {
              const initialLetter = acc.name ? acc.name.charAt(0).toUpperCase() : 'A';
              const percent = Math.round((acc.credits_remaining / (acc.initial_credits || 1000)) * 100);

              return (
                <div key={acc.id} className="senior-card">
                  <div>
                    {/* Top Identity Row */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div className="account-avatar">{initialLetter}</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '1rem', color: '#ffffff' }}>
                            {acc.name}
                          </div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            {acc.email || 'Email biriktirilmagan'}
                          </div>
                        </div>
                      </div>

                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          padding: '0.2rem 0.55rem',
                          borderRadius: 'var(--radius-full)',
                          background: 'rgba(255, 255, 255, 0.06)',
                          color: 'var(--text-secondary)',
                          border: '1px solid var(--border-color)',
                        }}
                      >
                        📁 {acc.profile_dir}
                      </span>
                    </div>

                    {/* Flow AI Credit Meter */}
                    <div
                      style={{
                        background: 'rgba(15, 23, 42, 0.6)',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-md)',
                        padding: '0.85rem',
                        marginBottom: '0.75rem',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', fontWeight: 600, color: '#38bdf8' }}>
                          <span>⚡️</span>
                          <span>Flow AI Krediti</span>
                        </div>
                        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: acc.has_flow_credits && acc.credits_remaining > 0 ? '#10b981' : '#ef4444' }}>
                          {acc.has_flow_credits ? `${acc.credits_remaining} / ${acc.initial_credits}` : 'Kredit Yo\'q'}
                        </span>
                      </div>

                      <div className="metric-progress-track">
                        <div
                          className={`metric-progress-bar ${percent > 50 ? 'success' : percent > 15 ? '' : 'warning'}`}
                          style={{ width: `${Math.max(4, percent)}%` }}
                        />
                      </div>
                    </div>

                    {/* YouTube Channel Status */}
                    <div
                      style={{
                        background: acc.has_youtube_channel ? 'rgba(239, 68, 68, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                        border: `1px solid ${acc.has_youtube_channel ? 'rgba(239, 68, 68, 0.25)' : 'var(--border-color)'}`,
                        borderRadius: 'var(--radius-md)',
                        padding: '0.85rem',
                        marginBottom: '1rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                        <span style={{ fontSize: '1.1rem' }}>📺</span>
                        <div>
                          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: acc.has_youtube_channel ? '#f87171' : 'var(--text-muted)' }}>
                            {acc.has_youtube_channel ? 'YouTube Kanal Ulangan' : 'Kanal Ulanmagan'}
                          </div>
                          {acc.has_youtube_channel && acc.youtube_channel_name && (
                            <div style={{ fontSize: '0.75rem', color: '#ffffff', fontWeight: 500 }}>
                              {acc.youtube_channel_name}
                            </div>
                          )}
                        </div>
                      </div>

                      {acc.has_youtube_channel && acc.youtube_subscribers > 0 && (
                        <span style={{ fontSize: '0.75rem', color: '#f87171', fontWeight: 700 }}>
                          {acc.youtube_subscribers.toLocaleString()} obunachi
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.85rem' }}>
                    <button
                      type="button"
                      className="btn-senior-secondary"
                      onClick={() => handleInspect(acc)}
                      disabled={inspectingId === acc.id}
                      style={{ flex: 1, padding: '0.45rem 0.6rem', fontSize: '0.8rem', justifyContent: 'center' }}
                    >
                      <span>🔍</span>
                      <span>{inspectingId === acc.id ? 'Tekshirilmoqda...' : 'Tekshirish'}</span>
                    </button>
                    <button
                      type="button"
                      className="btn-senior-secondary"
                      onClick={() => openEdit(acc)}
                      style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}
                      title="Tahrirlash"
                    >
                      ✏️
                    </button>
                    <button
                      type="button"
                      className="btn-senior-danger"
                      onClick={() => handleDelete(acc.id, acc.name)}
                      title="O'chirish"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Computer Chrome Profiles Auto-Discovery */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>
              🌐 Kompyuterdagi Google Chrome Profillari ({detectedProfiles.length} ta)
            </h3>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Kali Linux tizimidagi barcha profillar avtomatik aniqlandi. 1 ta bosish orqali boshqaruvga ulang:
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '0.75rem' }}>
          {detectedProfiles.map((p) => {
            const alreadyAdded = accounts.some((a) => a.profile_dir === p.profile_dir);
            return (
              <div
                key={p.profile_dir}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 0.9rem',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#ffffff' }}>
                    {p.name}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    📁 {p.profile_dir} • {p.email || 'Email yoʻq'}
                  </div>
                </div>

                {alreadyAdded ? (
                  <span style={{ fontSize: '0.75rem', color: 'var(--accent-success)', fontWeight: 600 }}>
                    ✓ Ulangan
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleQuickAddFromDetected(p)}
                    style={{
                      background: 'rgba(59, 130, 246, 0.15)',
                      color: '#60a5fa',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      padding: '0.3rem 0.65rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    ➕ Ulash
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Add / Edit Modal */}
      {isAddModalOpen && (
        <div className="modal-overlay" onClick={() => setIsAddModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>
                {editingAccount ? '✏️ Akkauntni Tahrirlash' : '➕ Yangi Akkaunt Qoʻshish'}
              </h3>
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '1.25rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveAccount} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Akkaunt Nomi
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Masalan: Ustaai (Asosiy)"
                  className="modal-input"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Email manzili
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="masalan: user@gmail.com"
                  className="modal-input"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Google Chrome Profili
                </label>
                <select
                  value={profileDir}
                  onChange={(e) => setProfileDir(e.target.value)}
                  className="modal-input"
                >
                  <option value="Profile 1">Profile 1 (Ustaai)</option>
                  <option value="Profile 3">Profile 3 (Samik)</option>
                  <option value="Profile 4">Profile 4 (DEfarux)</option>
                  <option value="Profile 6">Profile 6 (Shohruh)</option>
                  <option value="Default">Default (Ваш Chrome)</option>
                  <option value="Profile 13">Profile 13</option>
                  <option value="Profile 17">Profile 17</option>
                  <option value="Profile 22">Profile 22</option>
                  <option value="Profile 24">Profile 24</option>
                  <option value="Profile 25">Profile 25</option>
                  <option value="Profile 31">Profile 31</option>
                </select>
              </div>

              {/* Flow AI Credit Checkbox & Input */}
              <div
                style={{
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem',
                }}
              >
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: '#34d399', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={hasFlowCredits}
                    onChange={(e) => setHasFlowCredits(e.target.checked)}
                  />
                  ⚡️ Ushbu akkauntda Flow AI kreditlari bor
                </label>

                {hasFlowCredits && (
                  <div style={{ marginTop: '0.6rem' }}>
                    <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                      Mavjud kreditlar miqdori:
                    </label>
                    <input
                      type="number"
                      value={creditsRemaining}
                      onChange={(e) => setCreditsRemaining(Number(e.target.value))}
                      className="modal-input"
                    />
                  </div>
                )}
              </div>

              {/* YouTube Channel Checkbox & Input */}
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem',
                }}
              >
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: '#f87171', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={hasYoutubeChannel}
                    onChange={(e) => setHasYoutubeChannel(e.target.checked)}
                  />
                  📺 Ushbu akkauntda YouTube kanal bor
                </label>

                {hasYoutubeChannel && (
                  <div style={{ marginTop: '0.6rem' }}>
                    <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                      Kanal Nomi:
                    </label>
                    <input
                      type="text"
                      value={youtubeChannelName}
                      onChange={(e) => setYoutubeChannelName(e.target.value)}
                      placeholder="Masalan: Google Developers yoki Ustaai AI"
                      className="modal-input"
                    />
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  className="btn-senior-secondary"
                  onClick={() => setIsAddModalOpen(false)}
                >
                  Bekor qilish
                </button>
                <button type="submit" className="btn-senior-primary">
                  Saqlash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
export default AccountManagement;

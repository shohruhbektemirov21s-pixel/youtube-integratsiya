import { useState, useEffect } from 'react';
import { youtubeService } from '../../services/youtubeService';
import type { FlowAIAccount, DetectedProfile } from '../../types/youtube';

export function AccountManagement() {
  const [accounts, setAccounts] = useState<FlowAIAccount[]>([]);
  const [detectedProfiles, setDetectedProfiles] = useState<DetectedProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [inspectingId, setInspectingId] = useState<number | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [editingAccount, setEditingAccount] = useState<FlowAIAccount | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [profileDir, setProfileDir] = useState('Profile 1');
  const [hasFlowCredits, setHasFlowCredits] = useState(true);
  const [creditsRemaining, setCreditsRemaining] = useState(1000);
  const [hasYoutubeChannel, setHasYoutubeChannel] = useState(false);
  const [youtubeChannelName, setYoutubeChannelName] = useState('');
  const [youtubeChannelId, setYoutubeChannelId] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
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
      } else {
        await youtubeService.createFlowAccount(payload);
      }

      setIsAddModalOpen(false);
      setEditingAccount(null);
      resetForm();
      await loadData();
    } catch (err) {
      alert('Akkauntni saqlashda xatolik yuz berdi: ' + (err as Error).message);
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
      await loadData();
    } catch (err) {
      alert('Profilni qoʻshishda xatolik: ' + (err as Error).message);
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
      await loadData();
    } catch (err) {
      alert('Tekshirishda xatolik: ' + (err as Error).message);
    } finally {
      setInspectingId(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Ushbu akkauntni oʻchirishga ishonchingiz komilmi?')) return;
    try {
      await youtubeService.deleteFlowAccount(id);
      await loadData();
    } catch (err) {
      alert('Oʻchirishda xatolik: ' + (err as Error).message);
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

  return (
    <div style={{ padding: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
            👥 Mening Akkauntlarim (Flow AI & YouTube)
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '0.35rem' }}>
            Qaysi akkauntda Flow AI krediti borligi va qaysi birida YouTube kanal mavjudligini mustaqil belgilang va boshqaring.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            resetForm();
            setEditingAccount(null);
            setIsAddModalOpen(true);
          }}
          style={{
            padding: '0.6rem 1.25rem',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            borderRadius: '8px',
            border: 'none',
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(37,99,235,0.2)',
          }}
        >
          ➕ Yangi Akkaunt Kiritish
        </button>
      </div>

      {/* Summary Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginBottom: '2rem',
        }}
      >
        <div style={{ backgroundColor: '#ffffff', padding: '1.25rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>JAMI AKKAUNTLAR</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a', marginTop: '0.25rem' }}>
            {accounts.length} ta
          </div>
          <div style={{ fontSize: '0.8rem', color: '#16a34a', marginTop: '0.25rem' }}>Barchasi tizimga ulangan</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '1.25rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>⚡️ KREDIT MAVJUD AKKAUNTLAR</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#2563eb', marginTop: '0.25rem' }}>
            {accounts.filter((a) => a.has_flow_credits && a.credits_remaining > 0).length} ta
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
            Jami: {accounts.reduce((sum, a) => sum + (a.credits_remaining || 0), 0)} kredit
          </div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '1.25rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>📺 YOUTUBE KANAL MAVJUD AKKAUNTLAR</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#dc2626', marginTop: '0.25rem' }}>
            {accounts.filter((a) => a.has_youtube_channel).length} ta
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
            {accounts.find((a) => a.has_youtube_channel)?.youtube_channel_name || 'Asosiy kanal ulangan'}
          </div>
        </div>
      </div>

      {/* Account List Grid */}
      <div style={{ marginBottom: '2.5rem' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#1e293b', marginBottom: '1rem' }}>
          📋 Faol Akkauntlar Ro'yxati
        </h3>

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Akkauntlar yuklanmoqda...</div>
        ) : accounts.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#f8fafc', borderRadius: '12px' }}>
            Akkauntlar mavjud emas. Quyidagi Chrome profillaridan qo'shing yoki yangi akkaunt kiriting.
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
              gap: '1.25rem',
            }}
          >
            {accounts.map((acc) => (
              <div
                key={acc.id}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
                      {acc.name}
                    </h4>
                    <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.15rem' }}>
                      {acc.email || 'Email belgilanmagan'}
                    </div>
                  </div>
                  <span
                    style={{
                      padding: '0.2rem 0.6rem',
                      borderRadius: '20px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      backgroundColor: '#f1f5f9',
                      color: '#475569',
                      border: '1px solid #cbd5e1',
                    }}
                  >
                    📁 {acc.profile_dir}
                  </span>
                </div>

                {/* Badges: Credit and Channel */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                  {/* Flow AI Credit Row */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.6rem 0.75rem',
                      backgroundColor: acc.has_flow_credits && acc.credits_remaining > 0 ? '#f0fdf4' : '#f8fafc',
                      borderRadius: '8px',
                      border: acc.has_flow_credits && acc.credits_remaining > 0 ? '1px solid #bbf7d0' : '1px solid #e2e8f0',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '1.1rem' }}>⚡️</span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#166534' }}>
                        Flow AI Krediti:
                      </span>
                    </div>
                    <span style={{ fontSize: '0.9rem', fontWeight: 700, color: acc.has_flow_credits ? '#15803d' : '#94a3b8' }}>
                      {acc.has_flow_credits ? `${acc.credits_remaining} / ${acc.initial_credits}` : 'Mavjud emas'}
                    </span>
                  </div>

                  {/* YouTube Channel Row */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.6rem 0.75rem',
                      backgroundColor: acc.has_youtube_channel ? '#fef2f2' : '#f8fafc',
                      borderRadius: '8px',
                      border: acc.has_youtube_channel ? '1px solid #fecaca' : '1px solid #e2e8f0',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '1.1rem' }}>📺</span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#991b1b' }}>
                        YouTube Kanal:
                      </span>
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: acc.has_youtube_channel ? '#b91c1c' : '#94a3b8' }}>
                      {acc.has_youtube_channel ? acc.youtube_channel_name || 'Kanal mavjud' : 'Kanal ulanmagan'}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <button
                    type="button"
                    onClick={() => handleInspect(acc)}
                    disabled={inspectingId === acc.id}
                    style={{
                      flex: 1,
                      padding: '0.45rem',
                      backgroundColor: '#eff6ff',
                      color: '#2563eb',
                      border: '1px solid #bfdbfe',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {inspectingId === acc.id ? 'Tekshirilmoqda...' : '🔍 Tekshirish'}
                  </button>
                  <button
                    type="button"
                    onClick={() => openEdit(acc)}
                    style={{
                      padding: '0.45rem 0.75rem',
                      backgroundColor: '#f8fafc',
                      color: '#475569',
                      border: '1px solid #cbd5e1',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    ✏️ Tahrirlash
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(acc.id)}
                    style={{
                      padding: '0.45rem 0.75rem',
                      backgroundColor: '#fef2f2',
                      color: '#dc2626',
                      border: '1px solid #fecaca',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    🗑
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Auto-detected Chrome Profiles on Computer */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              🌐 Kompyuterdagi Google Chrome Profillari (Aniqlangan)
            </h3>
            <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: '0.25rem' }}>
              Quyidagi profillardan birini bitta bosish orqali tizimga tezkor qo'shishingiz mumkin:
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0.75rem' }}>
          {detectedProfiles.map((p) => {
            const alreadyAdded = accounts.some((a) => a.profile_dir === p.profile_dir);
            return (
              <div
                key={p.profile_dir}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  backgroundColor: '#f8fafc',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>
                    {p.name} ({p.profile_dir})
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{p.email || 'Email yoʻq'}</div>
                </div>
                {alreadyAdded ? (
                  <span style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: 600 }}>✓ Ulangan</span>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleQuickAddFromDetected(p)}
                    style={{
                      padding: '0.35rem 0.75rem',
                      backgroundColor: '#2563eb',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    ➕ Qo'shish
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Add / Edit Modal */}
      {isAddModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              maxWidth: '500px',
              width: '100%',
              padding: '1.75rem',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
          >
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, marginBottom: '1.25rem', color: '#0f172a' }}>
              {editingAccount ? '✏️ Akkauntni Tahrirlash' : '➕ Yangi Akkaunt Qoʻshish'}
            </h3>

            <form onSubmit={handleSaveAccount} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Akkaunt Nomi
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Masalan: Ustaai (Asosiy)"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Email manzili
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="masalan: user@gmail.com"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                  Chrome Profil Katalogi
                </label>
                <select
                  value={profileDir}
                  onChange={(e) => setProfileDir(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.9rem', backgroundColor: '#fff' }}
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

              {/* Flow AI Credit Settings */}
              <div style={{ padding: '0.75rem', backgroundColor: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: '#166534', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={hasFlowCredits}
                    onChange={(e) => setHasFlowCredits(e.target.checked)}
                  />
                  ⚡️ Ushbu akkauntda Flow AI kreditlari bor
                </label>
                {hasFlowCredits && (
                  <div style={{ marginTop: '0.5rem' }}>
                    <label style={{ fontSize: '0.8rem', color: '#15803d', display: 'block', marginBottom: '0.2rem' }}>
                      Mavjud kredit miqdori:
                    </label>
                    <input
                      type="number"
                      value={creditsRemaining}
                      onChange={(e) => setCreditsRemaining(Number(e.target.value))}
                      style={{ width: '100%', padding: '0.4rem', borderRadius: '6px', border: '1px solid #bbf7d0' }}
                    />
                  </div>
                )}
              </div>

              {/* YouTube Channel Settings */}
              <div style={{ padding: '0.75rem', backgroundColor: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: '#991b1b', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={hasYoutubeChannel}
                    onChange={(e) => setHasYoutubeChannel(e.target.checked)}
                  />
                  📺 Ushbu akkauntda YouTube kanal bor
                </label>
                {hasYoutubeChannel && (
                  <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div>
                      <label style={{ fontSize: '0.8rem', color: '#991b1b', display: 'block', marginBottom: '0.2rem' }}>
                        YouTube Kanal Nomi:
                      </label>
                      <input
                        type="text"
                        value={youtubeChannelName}
                        onChange={(e) => setYoutubeChannelName(e.target.value)}
                        placeholder="Masalan: Google Developers yoki Ustaai AI"
                        style={{ width: '100%', padding: '0.4rem', borderRadius: '6px', border: '1px solid #fecaca' }}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#f1f5f9',
                    color: '#475569',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '0.5rem 1.25rem',
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
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

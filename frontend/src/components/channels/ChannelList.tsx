import { useState, useEffect } from 'react';
import { youtubeService } from '../../services/youtubeService';
import { Spinner } from '../common/Spinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { EmptyState } from '../common/EmptyState';
import { AddChannelModal } from './AddChannelModal';
import { useAuth } from '../../context/AuthContext';
import { ApiError } from '../../services/api';
import type { YouTubeChannel } from '../../types/youtube';

interface ChannelListProps {
  onOpenAuth: () => void;
}

export function ChannelList({ onOpenAuth }: ChannelListProps) {
  const { isAuthenticated, user } = useAuth();
  const [channels, setChannels] = useState<YouTubeChannel[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<{ message: string; code?: string; details?: unknown } | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const fetchChannels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await youtubeService.getChannels();
      setChannels(response.results);
    } catch (err) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, details: err.details });
      } else {
        setError({ message: 'Kanallarni yuklashda xatolik yuz berdi.' });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChannels();
  }, []);

  const handleSync = async (channel: YouTubeChannel) => {
    if (!isAuthenticated) {
      onOpenAuth();
      return;
    }

    setSyncingId(channel.id);
    setActionNotice(null);
    try {
      const res = await youtubeService.triggerSync(channel.id);
      setActionNotice(`✅ '${channel.title}': ${res.message || 'Sinxronizatsiya muvaffaqiyatli yakunlandi'}`);
      await fetchChannels();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Sinxronizatsiyada xatolik yuz berdi';
      setActionNotice(`❌ '${channel.title}' sinxronizatsiyasi muvaffaqiyatsiz: ${msg}`);
    } finally {
      setSyncingId(null);
    }
  };

  const handleDelete = async (channel: YouTubeChannel) => {
    if (!isAuthenticated) {
      onOpenAuth();
      return;
    }

    if (!window.confirm(`'${channel.title}' kanalini o'chirishni tasdiqlaysizmi?`)) {
      return;
    }

    try {
      await youtubeService.deleteChannel(channel.id);
      setChannels((prev) => prev.filter((c) => c.id !== channel.id));
      setActionNotice(`🗑️ '${channel.title}' kanali muvaffaqiyatli o'chirildi.`);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "O'chirishda xatolik yuz berdi";
      alert(`Xatolik: ${msg}`);
    }
  };

  const handleChannelAdded = (newChannel: YouTubeChannel) => {
    setChannels((prev) => [newChannel, ...prev]);
    setActionNotice(`🎉 Yangi kanal '${newChannel.title}' muvaffaqiyatli qo'shildi!`);
  };

  const formatNumber = (num: number): string => {
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, color: '#0f172a', fontSize: '1.5rem' }}>YouTube Kanallari</h2>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
            Integratsiya qilingan barcha YouTube kanallari va ularning ko'rsatkichlari
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            if (!isAuthenticated) {
              onOpenAuth();
            } else {
              setIsAddModalOpen(true);
            }
          }}
          style={{
            padding: '0.6rem 1.25rem',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span>➕</span> Kanal Qo'shish
        </button>
      </div>

      {actionNotice && (
        <div
          style={{
            padding: '0.75rem 1rem',
            backgroundColor: actionNotice.startsWith('✅') || actionNotice.startsWith('🎉') ? '#f0fdf4' : '#fef2f2',
            border: `1px solid ${actionNotice.startsWith('✅') || actionNotice.startsWith('🎉') ? '#bbf7d0' : '#fecaca'}`,
            borderRadius: '6px',
            color: actionNotice.startsWith('✅') || actionNotice.startsWith('🎉') ? '#166534' : '#991b1b',
            marginBottom: '1.25rem',
            fontSize: '0.9rem',
          }}
        >
          {actionNotice}
        </div>
      )}

      {loading && <Spinner message="Kanallar yuklanmoqda..." />}

      {error && <ErrorMessage message={error.message} code={error.code} details={error.details} onRetry={fetchChannels} />}

      {!loading && !error && channels.length === 0 && (
        <EmptyState
          title="Hech qanday kanal topilmadi"
          description="Hozircha birorta ham YouTube kanali integratsiya qilinmagan. Birinchi kanalingizni qo'shib boshlang!"
          actionLabel="Kanal Qo'shish"
          onAction={() => {
            if (!isAuthenticated) {
              onOpenAuth();
            } else {
              setIsAddModalOpen(true);
            }
          }}
          icon="📺"
        />
      )}

      {!loading && !error && channels.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {channels.map((channel) => (
            <div
              key={channel.id}
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '10px',
                border: '1px solid #e2e8f0',
                padding: '1.25rem',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  {channel.thumbnail_url ? (
                    <img
                      src={channel.thumbnail_url}
                      alt={channel.title}
                      style={{ width: '48px', height: '48px', borderRadius: '50%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        backgroundColor: '#e2e8f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.5rem',
                      }}
                    >
                      📺
                    </div>
                  )}
                  <div style={{ overflow: 'hidden' }}>
                    <h3 style={{ margin: 0, fontSize: '1.05rem', color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {channel.title}
                    </h3>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      {channel.custom_url || channel.channel_id}
                    </span>
                  </div>
                </div>

                {channel.description && (
                  <p
                    style={{
                      fontSize: '0.85rem',
                      color: '#475569',
                      margin: '0.5rem 0 1rem 0',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {channel.description}
                  </p>
                )}

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '0.5rem',
                    padding: '0.75rem',
                    backgroundColor: '#f8fafc',
                    borderRadius: '8px',
                    textAlign: 'center',
                    marginBottom: '1rem',
                  }}
                >
                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Obunachilar</span>
                    <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>{formatNumber(channel.subscriber_count)}</strong>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Videolar</span>
                    <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>{channel.video_count || channel.total_videos}</strong>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Ko'rishlar</span>
                    <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>{formatNumber(channel.view_count)}</strong>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem' }}>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Egasi: {channel.owner_username}
                </span>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    type="button"
                    onClick={() => handleSync(channel)}
                    disabled={syncingId === channel.id}
                    style={{
                      padding: '0.35rem 0.75rem',
                      backgroundColor: '#eff6ff',
                      color: '#2563eb',
                      border: '1px solid #bfdbfe',
                      borderRadius: '4px',
                      cursor: syncingId === channel.id ? 'not-allowed' : 'pointer',
                      fontSize: '0.8rem',
                      fontWeight: 500,
                    }}
                  >
                    {syncingId === channel.id ? 'Sinxronlanmoqda...' : '🔄 Sinxronlash'}
                  </button>

                  {user?.username === channel.owner_username && (
                    <button
                      type="button"
                      onClick={() => handleDelete(channel)}
                      style={{
                        padding: '0.35rem 0.5rem',
                        backgroundColor: '#fff5f5',
                        color: '#dc2626',
                        border: '1px solid #fecaca',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                      }}
                      title="Kanalni o'chirish"
                    >
                      🗑️
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <AddChannelModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onChannelAdded={handleChannelAdded}
      />
    </div>
  );
}

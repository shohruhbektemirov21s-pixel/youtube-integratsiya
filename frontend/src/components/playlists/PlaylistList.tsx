import { useState, useEffect } from 'react';
import { youtubeService } from '../../services/youtubeService';
import { Spinner } from '../common/Spinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { EmptyState } from '../common/EmptyState';
import { ApiError } from '../../services/api';
import type { YouTubePlaylist } from '../../types/youtube';

export function PlaylistList() {
  const [playlists, setPlaylists] = useState<YouTubePlaylist[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<{ message: string; code?: string; details?: unknown } | null>(null);

  const fetchPlaylists = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await youtubeService.getPlaylists();
      setPlaylists(res.results);
    } catch (err) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, details: err.details });
      } else {
        setError({ message: 'Playlistlarni yuklashda xatolik yuz berdi.' });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlaylists();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0, color: '#0f172a', fontSize: '1.5rem' }}>YouTube Playlistlari</h2>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
            Kanallarga tegishli playlistlar va ularning videolari soni
          </p>
        </div>
        <button
          type="button"
          onClick={fetchPlaylists}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#f1f5f9',
            color: '#334155',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: 500,
          }}
        >
          🔄 Yangilash
        </button>
      </div>

      {loading && <Spinner message="Playlistlar yuklanmoqda..." />}

      {error && <ErrorMessage message={error.message} code={error.code} details={error.details} onRetry={fetchPlaylists} />}

      {!loading && !error && playlists.length === 0 && (
        <EmptyState
          title="Hech qanday playlist topilmadi"
          description="Kanalingiz sinxronlanganda playlistlar avtomatik ushbu ro'yxatda paydo bo'ladi."
          icon="📑"
        />
      )}

      {!loading && !error && playlists.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.25rem' }}>
          {playlists.map((pl) => (
            <div
              key={pl.id}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '8px',
                      backgroundColor: '#eff6ff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.25rem',
                    }}
                  >
                    📑
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1rem', color: '#0f172a' }}>{pl.title}</h3>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>📺 {pl.channel_title}</span>
                  </div>
                </div>

                {pl.description && (
                  <p style={{ fontSize: '0.85rem', color: '#475569', margin: '0.5rem 0' }}>{pl.description}</p>
                )}
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderTop: '1px solid #f1f5f9',
                  paddingTop: '0.75rem',
                  marginTop: '0.75rem',
                  fontSize: '0.8rem',
                  color: '#64748b',
                }}
              >
                <span>Elementlar: <strong>{pl.item_count || pl.videos_count} ta</strong></span>
                <span style={{ fontFamily: 'monospace' }}>{pl.playlist_id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

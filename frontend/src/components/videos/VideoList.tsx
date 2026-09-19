import { useState, useEffect, useCallback } from 'react';
import { youtubeService } from '../../services/youtubeService';
import { Spinner } from '../common/Spinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { EmptyState } from '../common/EmptyState';
import { StatCard } from '../common/StatCard';
import { ApiError } from '../../services/api';
import type { YouTubeVideo, VideoStatistics } from '../../types/youtube';

export function VideoList() {
  const [videos, setVideos] = useState<YouTubeVideo[]>([]);
  const [statistics, setStatistics] = useState<VideoStatistics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<{ message: string; code?: string; details?: unknown } | null>(null);

  // Search & filter
  const [search, setSearch] = useState<string>('');
  const [ordering, setOrdering] = useState<string>('-published_at');

  const fetchStats = async () => {
    try {
      const res = await youtubeService.getVideoStatistics();
      setStatistics(res.data);
    } catch {
      // Non-critical if statistics fail to load initially
    }
  };

  const fetchVideos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await youtubeService.getVideos({
        search: search.trim() || undefined,
        ordering,
      });
      setVideos(res.results);
    } catch (err) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, details: err.details });
      } else {
        setError({ message: 'Videolarni yuklashda xatolik yuz berdi.' });
      }
    } finally {
      setLoading(false);
    }
  }, [search, ordering]);

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchVideos();
    }, 250);
    return () => clearTimeout(timer);
  }, [fetchVideos]);

  const formatNumber = (num: number): string => {
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0, color: '#0f172a', fontSize: '1.5rem' }}>YouTube Videolari</h2>
        <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
          Integratsiya qilingan barcha videolar tahlili va ko'rsatkichlari
        </p>
      </div>

      {statistics && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginBottom: '1.5rem',
          }}
        >
          <StatCard title="Jami Videolar" value={statistics.total_videos} icon="🎬" />
          <StatCard title="Ko'rishlar Soni" value={formatNumber(statistics.total_views)} icon="👁️" />
          <StatCard title="Like'lar Soni" value={formatNumber(statistics.total_likes)} icon="👍" />
          <StatCard title="Sharhlar Soni" value={formatNumber(statistics.total_comments)} icon="💬" />
        </div>
      )}

      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
          backgroundColor: '#ffffff',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid #e2e8f0',
        }}
      >
        <div style={{ flex: 1, minWidth: '240px' }}>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Sarlavha yoki video ID bo'yicha qidiruv..."
            style={{
              width: '100%',
              padding: '0.55rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div>
          <select
            value={ordering}
            onChange={(e) => setOrdering(e.target.value)}
            style={{
              padding: '0.55rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '0.9rem',
              backgroundColor: '#fff',
              cursor: 'pointer',
            }}
          >
            <option value="-published_at">Eng yangi chiqqan</option>
            <option value="published_at">Eng eski chiqqan</option>
            <option value="-view_count">Eng ko'p ko'rilgan</option>
            <option value="-like_count">Eng ko'p yoqtirilgan</option>
            <option value="-duration_seconds">Eng uzoq davomiylik</option>
          </select>
        </div>
      </div>

      {loading && <Spinner message="Videolar yuklanmoqda..." />}

      {error && <ErrorMessage message={error.message} code={error.code} details={error.details} onRetry={fetchVideos} />}

      {!loading && !error && videos.length === 0 && (
        <EmptyState
          title="Hech qanday video topilmadi"
          description={
            search
              ? `'${search}' bo'yicha hech qanday video mos kelmadi.`
              : "Kanallaringizda videolar mavjud bo'lsa, 'Sinxronlash' tugmasini bosib ularni yuklab oling."
          }
          icon="🎥"
        />
      )}

      {!loading && !error && videos.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.25rem' }}>
          {videos.map((video) => (
            <div
              key={video.id}
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '10px',
                border: '1px solid #e2e8f0',
                overflow: 'hidden',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div style={{ position: 'relative', width: '100%', height: '160px', backgroundColor: '#0f172a' }}>
                {video.thumbnail_url ? (
                  <img
                    src={video.thumbnail_url}
                    alt={video.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <div
                    style={{
                      width: '100%',
                      height: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#94a3b8',
                      fontSize: '2.5rem',
                    }}
                  >
                    🎬
                  </div>
                )}
                <span
                  style={{
                    position: 'absolute',
                    bottom: '8px',
                    right: '8px',
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    color: '#ffffff',
                    padding: '0.15rem 0.4rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    fontFamily: 'monospace',
                  }}
                >
                  {video.formatted_duration || '00:00'}
                </span>
              </div>

              <div style={{ padding: '1rem', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <h4
                    style={{
                      margin: '0 0 0.35rem 0',
                      fontSize: '0.95rem',
                      color: '#0f172a',
                      lineHeight: 1.3,
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                    title={video.title}
                  >
                    {video.title}
                  </h4>
                  <span style={{ fontSize: '0.8rem', color: '#64748b', display: 'block', marginBottom: '0.75rem' }}>
                    📺 {video.channel_title}
                  </span>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    borderTop: '1px solid #f1f5f9',
                    paddingTop: '0.5rem',
                    fontSize: '0.75rem',
                    color: '#64748b',
                  }}
                >
                  <span>👁️ {formatNumber(video.view_count)}</span>
                  <span>👍 {formatNumber(video.like_count)}</span>
                  <span>💬 {formatNumber(video.comment_count)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

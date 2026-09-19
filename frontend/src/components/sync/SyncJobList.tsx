import { useState, useEffect } from 'react';
import { youtubeService } from '../../services/youtubeService';
import { Spinner } from '../common/Spinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { EmptyState } from '../common/EmptyState';
import { ApiError } from '../../services/api';
import type { SyncJob } from '../../types/youtube';

export function SyncJobList() {
  const [jobs, setJobs] = useState<SyncJob[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<{ message: string; code?: string; details?: unknown } | null>(null);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await youtubeService.getSyncJobs();
      setJobs(res.results);
    } catch (err) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, details: err.details });
      } else {
        setError({ message: 'Sinxronizatsiya audit jurnalini yuklashda xatolik yuz berdi.' });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const getStatusBadge = (status: SyncJob['status']) => {
    switch (status) {
      case 'completed':
        return { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0', label: 'Muvaffaqiyatli' };
      case 'in_progress':
        return { bg: '#eff6ff', color: '#1e40af', border: '#bfdbfe', label: 'Bajarilmoqda' };
      case 'failed':
        return { bg: '#fef2f2', color: '#991b1b', border: '#fecaca', label: 'Xatolik' };
      default:
        return { bg: '#f8fafc', color: '#475569', border: '#e2e8f0', label: 'Kutilmoqda' };
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0, color: '#0f172a', fontSize: '1.5rem' }}>Sinxronizatsiya Audit Jurnali</h2>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
            YouTube API orqali amalga oshirilgan ma'lumotlar almashinuvi qaydlari
          </p>
        </div>
        <button
          type="button"
          onClick={fetchJobs}
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

      {loading && <Spinner message="Audit jurnali yuklanmoqda..." />}

      {error && <ErrorMessage message={error.message} code={error.code} details={error.details} onRetry={fetchJobs} />}

      {!loading && !error && jobs.length === 0 && (
        <EmptyState
          title="Hozircha hech qanday sinxronizatsiya bajarilmagan"
          description="Kanallar ro'yxatida 'Sinxronlash' tugmasini bosganingizda, natijalar ushbu jurnalda qayd etiladi."
          icon="📝"
        />
      )}

      {!loading && !error && jobs.length > 0 && (
        <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '0.75rem 1rem' }}>ID</th>
                <th style={{ padding: '0.75rem 1rem' }}>Kanal</th>
                <th style={{ padding: '0.75rem 1rem' }}>Holat</th>
                <th style={{ padding: '0.75rem 1rem' }}>Sinxronlangan</th>
                <th style={{ padding: '0.75rem 1rem' }}>Boshlangan vaqti</th>
                <th style={{ padding: '0.75rem 1rem' }}>Izoh / Xato</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => {
                const badge = getStatusBadge(job.status);
                return (
                  <tr key={job.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace', color: '#64748b' }}>#{job.id}</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#0f172a' }}>{job.channel_title}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span
                        style={{
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor: badge.bg,
                          color: badge.color,
                          border: `1px solid ${badge.border}`,
                        }}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#334155' }}>
                      {job.items_synced} ta element
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#64748b', fontSize: '0.85rem' }}>
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: job.error_message ? '#dc2626' : '#94a3b8', fontSize: '0.85rem' }}>
                      {job.error_message || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

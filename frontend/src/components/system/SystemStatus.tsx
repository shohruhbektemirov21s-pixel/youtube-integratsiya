import { useState, useEffect } from 'react';
import { youtubeService } from '../../services/youtubeService';
import { Spinner } from '../common/Spinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { StatCard } from '../common/StatCard';
import type { HealthResponse } from '../../types/api';

export function SystemStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await youtubeService.checkHealth();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Backend bilan bog‘lanishda xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0, color: '#0f172a', fontSize: '1.5rem' }}>Tizim Holati va Arxitektura</h2>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
            Django REST Framework, PostgreSQL va TypeScript integratsiyasi monitoringi
          </p>
        </div>
        <button
          type="button"
          onClick={checkHealth}
          disabled={loading}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '0.85rem',
            fontWeight: 500,
          }}
        >
          {loading ? 'Tekshirilmoqda...' : '🔄 Qayta tekshirish'}
        </button>
      </div>

      {loading && <Spinner message="Server va baza holati tekshirilmoqda..." />}

      {error && (
        <ErrorMessage
          message="Backend bilan bog'lanishda uzilish yuz berdi"
          details={error}
          onRetry={checkHealth}
        />
      )}

      {health && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <StatCard
            title="Backend Xizmati"
            value={health.status === 'online' ? '🟢 Online' : '🔴 Offline'}
            icon="⚙️"
            subtitle={health.service}
          />
          <StatCard
            title="PostgreSQL Baza"
            value={health.database === 'ok' ? '🟢 Bog‘langan' : '🔴 Nosoz'}
            icon="🗄️"
            subtitle="PostgreSQL 18"
          />
          <StatCard
            title="API Versiyasi"
            value={`v${health.version}`}
            icon="🚀"
            subtitle="Django REST Framework"
          />
        </div>
      )}

      <div style={{ backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <h3 style={{ marginTop: 0, color: '#0f172a', fontSize: '1.1rem' }}>Arxitektura va Integratsiya Qoidalari</h3>
        <ul style={{ color: '#475569', lineHeight: 1.8, fontSize: '0.9rem', paddingLeft: '1.25rem', margin: 0 }}>
          <li><strong>Xavfsizlik:</strong> TokenAuthentication va CORS faqat ruxsat etilgan manbalar uchun ishlaydi.</li>
          <li><strong>Optimallashuv:</strong> N+1 so'rovlar oldini olish uchun Django ORM <code>select_related</code> va <code>annotate(Count)</code> qo'llangan.</li>
          <li><strong>Validatsiya:</strong> YouTube Channel ID va Video ID frontenda hamda backendda qat'iy tekshiriladi.</li>
          <li><strong>Ma'lumotlar yaxlitligi:</strong> PostgreSQL darajasida <code>UniqueConstraint</code> va <code>CheckConstraint</code> o'rnatilgan.</li>
        </ul>
      </div>
    </div>
  );
}

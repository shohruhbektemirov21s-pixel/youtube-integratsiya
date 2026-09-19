import { useEffect, useState } from 'react';
import { checkBackendHealth, type HealthCheckResponse } from './api/client';
import './App.css';

export function App() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkBackendHealth();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Backend bilan bog‘lanishda xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <header style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', margin: 0, color: '#0f172a' }}>YouTube Integratsiya</h1>
        <p style={{ color: '#64748b', marginTop: '0.5rem' }}>Django REST Framework + PostgreSQL + TypeScript React Platformasi</p>
      </header>

      <section style={{ backgroundColor: '#f8fafc', borderRadius: '8px', padding: '1.5rem', border: '1px solid #e2e8f0' }}>
        <h2 style={{ fontSize: '1.25rem', marginTop: 0, color: '#1e293b' }}>Tizim Holati</h2>

        {loading && <p style={{ color: '#64748b' }}>Backend holati tekshirilmoqda...</p>}

        {error && (
          <div style={{ padding: '1rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', color: '#991b1b' }}>
            <p style={{ margin: 0, fontWeight: 600 }}>Bog'lanishda xato:</p>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>{error}</p>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem', color: '#7f1d1d' }}>
              (Backend serveri ishga tushirilganligini tekshiring: <code>python manage.py runserver</code>)
            </p>
          </div>
        )}

        {health && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
            <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '0.85rem', color: '#64748b' }}>Backend API</span>
              <p style={{ fontSize: '1.1rem', fontWeight: 600, color: '#16a34a', margin: '0.25rem 0 0 0' }}>
                🟢 {health.status.toUpperCase()}
              </p>
            </div>
            <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '0.85rem', color: '#64748b' }}>PostgreSQL</span>
              <p style={{ fontSize: '1.1rem', fontWeight: 600, color: '#16a34a', margin: '0.25rem 0 0 0' }}>
                🟢 {health.database.toUpperCase()}
              </p>
            </div>
            <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '0.85rem', color: '#64748b' }}>Versiya</span>
              <p style={{ fontSize: '1.1rem', fontWeight: 600, color: '#0f172a', margin: '0.25rem 0 0 0' }}>
                {health.version}
              </p>
            </div>
          </div>
        )}

        <button
          onClick={fetchHealth}
          disabled={loading}
          style={{
            marginTop: '1.5rem',
            padding: '0.5rem 1.25rem',
            backgroundColor: '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          {loading ? 'Tekshirilmoqda...' : 'Qayta tekshirish'}
        </button>
      </section>

      <section style={{ marginTop: '2rem' }}>
        <h3 style={{ fontSize: '1.1rem', color: '#1e293b' }}>Arxitektura Tafsilotlari</h3>
        <ul style={{ color: '#475569', lineHeight: 1.8 }}>
          <li><strong>Backend:</strong> Django 6.1, Django REST Framework, CORS Headers</li>
          <li><strong>Frontend:</strong> TypeScript 5, React 19, Vite</li>
          <li><strong>Ma'lumotlar bazasi:</strong> PostgreSQL 18.4</li>
          <li><strong>Xavfsizlik:</strong> Maxfiy kalitlar va muhit parametrlari <code>.env</code> faylida saqlanadi</li>
        </ul>
      </section>
    </div>
  );
}

export default App;

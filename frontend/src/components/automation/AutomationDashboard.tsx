import { useState, useEffect } from 'react';
import { youtubeService } from '../../services/youtubeService';
import type {
  FlowAIAccount,
  ChannelNiche,
  VideoGenerationTask,
  ScheduledUpload,
  DailyChannelAnalytics,
} from '../../types/youtube';

export function AutomationDashboard() {
  const [accounts, setAccounts] = useState<FlowAIAccount[]>([]);
  const [niche, setNiche] = useState<ChannelNiche | null>(null);
  const [tasks, setTasks] = useState<VideoGenerationTask[]>([]);
  const [uploads, setUploads] = useState<ScheduledUpload[]>([]);
  const [analytics, setAnalytics] = useState<DailyChannelAnalytics[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [reporting, setReporting] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [accRes, nicheRes, tasksRes, uploadsRes, analyticsRes] = await Promise.all([
        youtubeService.getFlowAccounts(),
        youtubeService.getNiches(),
        youtubeService.getGenerationTasks(),
        youtubeService.getScheduledUploads(),
        youtubeService.getDailyAnalytics(),
      ]);

      setAccounts(accRes.results || []);
      setNiche(nicheRes.results?.[0] || null);
      setTasks(tasksRes.results || []);
      setUploads(uploadsRes.results || []);
      setAnalytics(analyticsRes.results || []);
    } catch (err: any) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerateNext = async () => {
    try {
      setGenerating(true);
      const res = await youtubeService.generateNextVideo();
      showToast(`⚡️ Yangi video yaratildi va 19:00 ga rejalashtirildi! (${res.data?.topic})`);
      await loadData();
    } catch (err: any) {
      showToast('Xatolik: ' + (err?.message || "Video generatsiyasida xatolik."));
    } finally {
      setGenerating(false);
    }
  };

  const handleSendReport = async () => {
    try {
      setReporting(true);
      const res = await youtubeService.sendDailyReport();
      showToast(res.message || '📊 Kunlik hisobot Telegramga yuborildi!');
      await loadData();
    } catch (err: any) {
      showToast('Xatolik: ' + (err?.message || 'Telegramga yuborishda xatolik.'));
    } finally {
      setReporting(false);
    }
  };

  const totalCredits = accounts.reduce((acc, curr) => acc + (curr.credits_remaining || 0), 0);
  const totalMaxCredits = accounts.length * 1000;
  const creditPercent = totalMaxCredits > 0 ? Math.round((totalCredits / totalMaxCredits) * 100) : 0;

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🤖</div>
        <div style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff' }}>Avtomatlashtirish markazi yuklanmoqda...</div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Flow AI va YouTube navbatlari tayyorlanmoqda</div>
      </div>
    );
  }

  return (
    <div>
      {/* Toast Notification */}
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
              <span style={{ fontSize: '1.5rem' }}>🤖</span>
              <h2>YouTube AI Avtomatlashtirish Markazi</h2>
            </div>
            <p>
              Hermes Agent va Gemini 3.8 Flash integratsiyasi. Har kuni soat 19:00 da avtomatik video yuklash va 4 ta Flow AI profillari nazorati.
            </p>
          </div>

          <div className="cockpit-actions">
            <button
              type="button"
              className="btn-senior-secondary"
              onClick={handleSendReport}
              disabled={reporting}
            >
              <span>📊</span>
              <span>{reporting ? 'Yuborilmoqda...' : 'Telegramga Hisobot'}</span>
            </button>
            <button
              type="button"
              className="btn-senior-primary"
              onClick={handleGenerateNext}
              disabled={generating}
            >
              <span>⚡️</span>
              <span>{generating ? 'Generatsiya...' : 'Video Generatsiya Qilish (Gemini AI)'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Primary KPI Cockpit Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {/* Flow AI Credit Meter Card */}
        <div className="senior-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>FLOW AI BALANSI</span>
            <span style={{ fontSize: '1.25rem' }}>⚡️</span>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#38bdf8', margin: '0.35rem 0' }}>
            {totalCredits} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ {totalMaxCredits}</span>
          </div>
          <div className="metric-progress-track" style={{ marginBottom: '0.4rem' }}>
            <div className="metric-progress-bar success" style={{ width: `${creditPercent}%` }} />
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {accounts.length} ta Flow AI profili bo'yicha
          </div>
        </div>

        {/* Channel Niche Card */}
        <div className="senior-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>KANAL STRATEGIYASI</span>
            <span style={{ fontSize: '1.25rem' }}>🎯</span>
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff', margin: '0.5rem 0', lineHeight: 1.3 }}>
            {niche ? niche.niche_name : "Sun'iy Intellekt va Kelajak"}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--accent-success)' }}>
            ✓ Qat'iy 1 ta nisha doirasida kontent
          </div>
        </div>

        {/* 19:00 Scheduled Upload Card */}
        <div className="senior-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>19:00 YUKLASH NAVBATI</span>
            <span style={{ fontSize: '1.25rem' }}>⏰</span>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#f87171', margin: '0.35rem 0' }}>
            {uploads.length} ta video
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Bugun soat 19:00 da avtomatik chiqariladi
          </div>
        </div>

        {/* Analytics Growth Card */}
        <div className="senior-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>TELEGRAM HISOBOT</span>
            <span style={{ fontSize: '1.25rem' }}>📱</span>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#34d399', margin: '0.35rem 0' }}>
            {analytics.length > 0 ? `+${analytics[0].views_growth_today}` : '+1,240'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Kunlik o'sish @youtubebildirishnoma_bot da
          </div>
        </div>
      </div>

      {/* 4 Flow AI Accounts Grid */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
              ⚡️ Flow AI Akkauntlar Holati (Har biri 1000 kredit)
            </h3>
            <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Video generatsiya qilishda kreditlar avtomatik eng ko'p kreditga ega hisobdan olinadi.
            </p>
          </div>
        </div>

        <div className="senior-grid">
          {accounts.map((acc) => {
            const initialLetter = acc.name ? acc.name.charAt(0).toUpperCase() : 'F';
            const percent = Math.round((acc.credits_remaining / (acc.initial_credits || 1000)) * 100);

            return (
              <div key={acc.id} className="senior-card">
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <div className="account-avatar">{initialLetter}</div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#ffffff' }}>{acc.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>📁 {acc.profile_dir}</div>
                      </div>
                    </div>
                    <span
                      style={{
                        padding: '0.2rem 0.6rem',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#34d399',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                      }}
                    >
                      Faol
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem', marginBottom: '0.4rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Mavjud kredit:</span>
                    <strong style={{ color: '#38bdf8' }}>{acc.credits_remaining} / {acc.initial_credits}</strong>
                  </div>

                  <div className="metric-progress-track">
                    <div
                      className={`metric-progress-bar ${percent > 50 ? 'success' : ''}`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>

                <div style={{ marginTop: '0.85rem', paddingTop: '0.65rem', borderTop: '1px solid var(--border-color)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  {acc.has_youtube_channel ? `📺 Kanal ulangan: ${acc.youtube_channel_name || 'Ha'}` : '⚡️ Faqat video generatsiya'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 19:00 Upload Queue Table */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>
              ⏰ 19:00 YouTube Avto-Yuklash Navbati
            </h3>
            <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Har kuni soat 19:00 da YouTube kanalga avtomatik chiqariladigan videolar
            </p>
          </div>
        </div>

        {uploads.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Hozircha navbatda videolar mavjud emas. Yuqoridagi "Video Generatsiya Qilish" tugmasini bosing.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Sana & Vaqt</th>
                  <th style={{ padding: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Video Sarlavhasi</th>
                  <th style={{ padding: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Kanal</th>
                  <th style={{ padding: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Holat</th>
                </tr>
              </thead>
              <tbody>
                {uploads.map((u) => (
                  <tr key={u.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                    <td style={{ padding: '0.85rem 0.75rem', fontSize: '0.85rem' }}>
                      <strong style={{ color: '#ffffff' }}>{u.scheduled_date}</strong>{' '}
                      <span style={{ color: '#38bdf8' }}>soat {u.scheduled_time}</span>
                    </td>
                    <td style={{ padding: '0.85rem 0.75rem', fontSize: '0.85rem', color: '#ffffff', fontWeight: 600 }}>
                      {u.title}
                    </td>
                    <td style={{ padding: '0.85rem 0.75rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {u.channel_title}
                    </td>
                    <td style={{ padding: '0.85rem 0.75rem' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.65rem',
                          borderRadius: 'var(--radius-full)',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          background: 'rgba(59, 130, 246, 0.15)',
                          color: '#60a5fa',
                          border: '1px solid rgba(59, 130, 246, 0.3)',
                        }}
                      >
                        19:00 ga Rejalashtirilgan
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Generations Log */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
        <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '1rem' }}>
          🎬 Oxirgi Generatsiya Qilingan Videolar (Gemini + Flow AI)
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {tasks.slice(0, 5).map((t) => (
            <div
              key={t.id}
              style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <strong style={{ fontSize: '0.95rem', color: '#ffffff' }}>{t.topic}</strong>
                <span style={{ fontSize: '0.78rem', color: '#38bdf8', fontWeight: 600 }}>
                  {t.account_name} (-{t.credits_used} kredit)
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Flow AI Prompt: "{t.prompt}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
export default AutomationDashboard;

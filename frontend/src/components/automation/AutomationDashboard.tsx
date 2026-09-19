import { useState, useEffect } from 'react';
import { youtubeService } from '../../services/youtubeService';
import type {
  FlowAIAccount,
  ChannelNiche,
  VideoGenerationTask,
  ScheduledUpload,
  DailyChannelAnalytics,
} from '../../types/youtube';
import { StatCard } from '../common/StatCard';
import { Spinner } from '../common/Spinner';
import { ErrorMessage } from '../common/ErrorMessage';

export function AutomationDashboard() {
  const [accounts, setAccounts] = useState<FlowAIAccount[]>([]);
  const [niche, setNiche] = useState<ChannelNiche | null>(null);
  const [tasks, setTasks] = useState<VideoGenerationTask[]>([]);
  const [uploads, setUploads] = useState<ScheduledUpload[]>([]);
  const [analytics, setAnalytics] = useState<DailyChannelAnalytics[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [reporting, setReporting] = useState<boolean>(false);
  const [reportResult, setReportResult] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
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
      setError(err?.message || "Ma'lumotlarni yuklashda xatolik yuz berdi.");
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
      setError(null);
      await youtubeService.generateNextVideo();
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Video g'oyasini yaratishda xatolik yuz berdi.");
    } finally {
      setGenerating(false);
    }
  };

  const handleSendReport = async () => {
    try {
      setReporting(true);
      setReportResult(null);
      const res = await youtubeService.sendDailyReport();
      setReportResult(res.message || "Hisobot muvaffaqiyatli shakllantirildi.");
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Telegram hisobotini yuborishda xatolik.");
    } finally {
      setReporting(false);
    }
  };

  if (loading) {
    return <Spinner message="Avtomatlashtirish markazi yuklanmoqda..." />;
  }

  const totalCredits = accounts.reduce((acc, curr) => acc + curr.credits_remaining, 0);

  return (
    <div className="automation-dashboard">
      <div className="section-header">
        <div>
          <h2>🤖 Avtomatlashtirish & Flow AI Markazi</h2>
          <p className="section-subtitle">
            Hermes Agent, Gemini AI, 4 ta Flow AI profili va 19:00 YouTube avto-yuklash boshqaruvi
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn btn-secondary"
            onClick={handleSendReport}
            disabled={reporting}
          >
            {reporting ? 'Yuborilmoqda...' : '📱 Telegramga Hisobot Yuborish'}
          </button>
          <button
            className="btn btn-primary"
            onClick={handleGenerateNext}
            disabled={generating}
          >
            {generating ? 'Generatsiya...' : '⚡️ Yangi Video Generatsiya Qilish (Gemini)'}
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={loadData} />}

      {reportResult && (
        <div style={{ background: 'rgba(34, 197, 94, 0.1)', border: '1px solid #22c55e', borderRadius: '8px', padding: '12px 16px', marginBottom: '20px', color: '#22c55e' }}>
          ✓ {reportResult}
        </div>
      )}

      {/* KPI Stats */}
      <div className="stats-grid">
        <StatCard
          title="Mavjud Flow AI Kreditlari"
          value={`${totalCredits} / 4000`}
          subtitle="4 ta akkaunt bo'yicha jami balans"
          icon="⚡️"
        />
        <StatCard
          title="Kanal Strategiyasi"
          value={niche ? niche.niche_name : "1ta Mavzu"}
          subtitle="Faqat bitta yo'nalish bo'yicha qat'iy kontent"
          icon="🎯"
        />
        <StatCard
          title="19:00 Rejalashtirilgan Yuklashlar"
          value={uploads.length}
          subtitle="Har kuni soat 19:00 da avtomatik yuklanadi"
          icon="⏰"
        />
        <StatCard
          title="Telegram Bot & Statistika"
          value={analytics.length > 0 ? `+${analytics[0].views_growth_today} ko'rish` : "@youtubebildirishnoma_bot"}
          subtitle="Kunlik o'sish va hisobotlar Telegramga boradi"
          icon="💬"
        />
      </div>

      {/* 4 Flow AI Accounts Grid */}
      <div style={{ marginTop: '30px' }}>
        <h3>⚡️ Flow AI 4 ta Akkaunt Balansi (1000 kreditdan)</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginTop: '14px' }}>
          {accounts.map((acc) => {
            const percent = Math.round((acc.credits_remaining / acc.initial_credits) * 100);
            return (
              <div
                key={acc.id}
                style={{
                  background: 'var(--card-bg, #1e1e24)',
                  border: '1px solid var(--border-color, #2a2a32)',
                  borderRadius: '12px',
                  padding: '18px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontWeight: 600, fontSize: '15px' }}>{acc.name}</span>
                  <span
                    style={{
                      background: acc.is_active ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: acc.is_active ? '#22c55e' : '#ef4444',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '12px',
                    }}
                  >
                    {acc.is_active ? 'Faol' : 'Nofaol'}
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary, #a0a0ab)', marginBottom: '8px' }}>
                  Brauzer profili: <code>{acc.profile_dir}</code>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', marginBottom: '6px' }}>
                  <span>Qolgan kredit:</span>
                  <strong>{acc.credits_remaining} / {acc.initial_credits}</strong>
                </div>
                <div style={{ width: '100%', height: '8px', background: '#2e2e38', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${percent}%`,
                      height: '100%',
                      background: percent > 20 ? '#3b82f6' : '#ef4444',
                      borderRadius: '4px',
                      transition: 'width 0.3s'
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 19:00 Upload Queue */}
      <div style={{ marginTop: '40px' }}>
        <h3>⏰ 19:00 YouTube Avto-Yuklash Navbati</h3>
        {uploads.length === 0 ? (
          <div style={{ padding: '24px', background: 'var(--card-bg, #1e1e24)', borderRadius: '12px', textAlign: 'center', marginTop: '12px' }}>
            <p>Hozircha navbatda videolar yo'q. "Yangi Video Generatsiya Qilish" tugmasini bosing.</p>
          </div>
        ) : (
          <div className="table-responsive" style={{ marginTop: '14px' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sana & Vaqt</th>
                  <th>Video Sarlavhasi</th>
                  <th>Kanal</th>
                  <th>Holat</th>
                </tr>
              </thead>
              <tbody>
                {uploads.map((up) => (
                  <tr key={up.id}>
                    <td>
                      <strong>{up.scheduled_date}</strong> soat <strong>{up.scheduled_time}</strong>
                    </td>
                    <td>{up.title}</td>
                    <td>{up.channel_title}</td>
                    <td>
                      <span
                        style={{
                          padding: '4px 10px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          background: up.status === 'published' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                          color: up.status === 'published' ? '#22c55e' : '#60a5fa',
                        }}
                      >
                        {up.status === 'scheduled' ? '19:00 ga Rejalashtirilgan' : up.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Generation History */}
      <div style={{ marginTop: '40px' }}>
        <h3>🎬 Oxirgi Generatsiya Qilingan Videolar (Gemini + Flow AI)</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '14px' }}>
          {tasks.slice(0, 5).map((t) => (
            <div
              key={t.id}
              style={{
                background: 'var(--card-bg, #1e1e24)',
                border: '1px solid var(--border-color, #2a2a32)',
                borderRadius: '10px',
                padding: '16px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <strong style={{ fontSize: '15px' }}>{t.topic}</strong>
                <span style={{ fontSize: '13px', color: '#60a5fa' }}>{t.account_name} (-{t.credits_used} kredit)</span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary, #94a3b8)', fontStyle: 'italic', margin: '4px 0' }}>
                Flow AI Prompt: "{t.prompt}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

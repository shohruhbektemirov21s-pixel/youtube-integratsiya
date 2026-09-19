interface StatCardProps {
  title: string;
  value: string | number;
  icon: string;
  subtitle?: string;
}

export function StatCard({ title, value, icon, subtitle }: StatCardProps) {
  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        padding: '1.25rem',
        borderRadius: '8px',
        border: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}
    >
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: '8px',
          backgroundColor: '#eff6ff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
        }}
      >
        {icon}
      </div>
      <div>
        <span style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>{title}</span>
        <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', margin: '0.1rem 0' }}>
          {value}
        </div>
        {subtitle && <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{subtitle}</span>}
      </div>
    </div>
  );
}

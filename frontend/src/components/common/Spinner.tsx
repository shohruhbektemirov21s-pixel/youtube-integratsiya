interface SpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Spinner({ message, size = 'md' }: SpinnerProps) {
  const sizeMap = {
    sm: '16px',
    md: '28px',
    lg: '44px',
  };

  const dim = sizeMap[size];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div
        style={{
          width: dim,
          height: dim,
          border: '3px solid #e2e8f0',
          borderTop: '3px solid #2563eb',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      {message && <p style={{ marginTop: '0.75rem', color: '#64748b', fontSize: '0.9rem' }}>{message}</p>}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

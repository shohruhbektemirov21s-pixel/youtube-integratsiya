interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: string;
}

export function EmptyState({ title, description, actionLabel, onAction, icon = '📭' }: EmptyStateProps) {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '3rem 1.5rem',
        backgroundColor: '#f8fafc',
        borderRadius: '8px',
        border: '1px dashed #cbd5e1',
        margin: '1.5rem 0',
      }}
    >
      <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>{icon}</div>
      <h3 style={{ margin: '0 0 0.5rem 0', color: '#1e293b', fontSize: '1.2rem' }}>{title}</h3>
      <p style={{ margin: 0, color: '#64748b', fontSize: '0.9rem', maxWidth: '400px', marginLeft: 'auto', marginRight: 'auto' }}>
        {description}
      </p>
      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          style={{
            marginTop: '1.25rem',
            padding: '0.5rem 1.25rem',
            backgroundColor: '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            fontWeight: 500,
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

import type { ReactNode } from 'react';

interface ErrorMessageProps {
  message: string;
  code?: string;
  details?: unknown;
  onRetry?: () => void;
  children?: ReactNode;
}

export function ErrorMessage({ message, code, details, onRetry, children }: ErrorMessageProps) {
  const formatDetails = (det: unknown): string | null => {
    if (!det) return null;
    if (typeof det === 'string') return det;
    if (typeof det === 'object') {
      try {
        return JSON.stringify(det, null, 2);
      } catch {
        return String(det);
      }
    }
    return String(det);
  };

  const detailsText = formatDetails(details);

  return (
    <div
      style={{
        padding: '1.25rem',
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        borderRadius: '8px',
        color: '#991b1b',
        margin: '1rem 0',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.25rem' }}>⚠️</span>
          <strong style={{ fontSize: '1rem' }}>{message}</strong>
        </div>
        {code && (
          <span
            style={{
              fontSize: '0.75rem',
              backgroundColor: '#fee2e2',
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              fontFamily: 'monospace',
              color: '#7f1d1d',
            }}
          >
            {code}
          </span>
        )}
      </div>

      {detailsText && (
        <pre
          style={{
            margin: '0.75rem 0 0 0',
            padding: '0.5rem',
            backgroundColor: '#fff5f5',
            borderRadius: '4px',
            fontSize: '0.8rem',
            overflowX: 'auto',
          }}
        >
          {detailsText}
        </pre>
      )}

      {children}

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          style={{
            marginTop: '0.75rem',
            padding: '0.4rem 0.8rem',
            backgroundColor: '#dc2626',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: 500,
          }}
        >
          Qayta urinish
        </button>
      )}
    </div>
  );
}

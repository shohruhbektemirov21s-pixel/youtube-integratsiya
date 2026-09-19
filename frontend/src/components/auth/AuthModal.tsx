import { useState, type FormEvent } from 'react';
import { Modal } from '../common/Modal';
import { ErrorMessage } from '../common/ErrorMessage';
import { useAuth } from '../../context/AuthContext';
import { ApiError } from '../../services/api';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');

  // Form states
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  // Validation & error states
  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<{ message: string; code?: string; details?: unknown } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const resetForm = () => {
    setUsername('');
    setEmail('');
    setPassword('');
    setPasswordConfirm('');
    setFirstName('');
    setLastName('');
    setValidationError(null);
    setApiError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const validate = (): boolean => {
    setValidationError(null);
    setApiError(null);

    if (!username.trim()) {
      setValidationError('Foydalanuvchi nomini (username) kiriting.');
      return false;
    }

    if (mode === 'register') {
      if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        setValidationError('To‘g‘ri email manzilini kiriting.');
        return false;
      }
      if (password.length < 8) {
        setValidationError('Parol kamida 8 ta belgidan iborat bo‘lishi kerak.');
        return false;
      }
      if (password !== passwordConfirm) {
        setValidationError('Kiritilgan parollar bir-biriga mos kelmadi.');
        return false;
      }
    } else {
      if (!password) {
        setValidationError('Parolni kiriting.');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setApiError(null);

    try {
      if (mode === 'login') {
        await login({ username: username.trim(), password });
      } else {
        await register({
          username: username.trim(),
          email: email.trim(),
          password,
          password_confirm: passwordConfirm,
          first_name: firstName.trim() || undefined,
          last_name: lastName.trim() || undefined,
        });
      }
      handleClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setApiError({
          message: err.message,
          code: err.code,
          details: err.details,
        });
      } else {
        setApiError({
          message: 'Kutilmagan xatolik yuz berdi. Iltimos qayta urinib ko‘ring.',
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '0.6rem 0.75rem',
    borderRadius: '6px',
    border: '1px solid #cbd5e1',
    fontSize: '0.9rem',
    boxSizing: 'border-box' as const,
    marginTop: '0.25rem',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#334155',
    marginBottom: '0.75rem',
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={mode === 'login' ? 'Tizimga kirish' : "Ro'yxatdan o'tish"}>
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', marginBottom: '1.25rem' }}>
        <button
          type="button"
          onClick={() => {
            setMode('login');
            resetForm();
          }}
          style={{
            flex: 1,
            padding: '0.6rem',
            border: 'none',
            borderBottom: mode === 'login' ? '2px solid #2563eb' : 'none',
            backgroundColor: 'transparent',
            color: mode === 'login' ? '#2563eb' : '#64748b',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Kirish
        </button>
        <button
          type="button"
          onClick={() => {
            setMode('register');
            resetForm();
          }}
          style={{
            flex: 1,
            padding: '0.6rem',
            border: 'none',
            borderBottom: mode === 'register' ? '2px solid #2563eb' : 'none',
            backgroundColor: 'transparent',
            color: mode === 'register' ? '#2563eb' : '#64748b',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Ro'yxatdan o'tish
        </button>
      </div>

      {validationError && (
        <div style={{ padding: '0.75rem', backgroundColor: '#fffbeb', border: '1px solid #fef3c7', borderRadius: '6px', color: '#92400e', marginBottom: '1rem', fontSize: '0.85rem' }}>
          ⚠️ {validationError}
        </div>
      )}

      {apiError && (
        <ErrorMessage message={apiError.message} code={apiError.code} details={apiError.details} />
      )}

      <form onSubmit={handleSubmit}>
        {mode === 'register' && (
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <label style={{ ...labelStyle, flex: 1, marginBottom: 0 }}>
              Ism
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Shohruh"
                style={inputStyle}
              />
            </label>
            <label style={{ ...labelStyle, flex: 1, marginBottom: 0 }}>
              Familiya
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Temirov"
                style={inputStyle}
              />
            </label>
          </div>
        )}

        <label style={labelStyle}>
          Foydalanuvchi nomi (Username) *
          <input
            type="text"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="masalan: user2026"
            style={inputStyle}
          />
        </label>

        {mode === 'register' && (
          <label style={labelStyle}>
            Email manzil *
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              style={inputStyle}
            />
          </label>
        )}

        <label style={labelStyle}>
          Parol *
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Kamida 8 ta belgi"
            style={inputStyle}
          />
        </label>

        {mode === 'register' && (
          <label style={labelStyle}>
            Parolni takrorlang *
            <input
              type="password"
              required
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              placeholder="Parolni qayta kiriting"
              style={inputStyle}
            />
          </label>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            width: '100%',
            marginTop: '1rem',
            padding: '0.75rem',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '0.95rem',
            fontWeight: 600,
            cursor: isSubmitting ? 'not-allowed' : 'pointer',
            opacity: isSubmitting ? 0.7 : 1,
          }}
        >
          {isSubmitting
            ? 'Bajarilmoqda...'
            : mode === 'login'
            ? 'Kirish'
            : "Ro'yxatdan o'tish"}
        </button>
      </form>
    </Modal>
  );
}

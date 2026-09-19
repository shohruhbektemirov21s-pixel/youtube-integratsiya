import { useState, type FormEvent } from 'react';
import { Modal } from '../common/Modal';
import { ErrorMessage } from '../common/ErrorMessage';
import { youtubeService } from '../../services/youtubeService';
import { ApiError } from '../../services/api';
import type { YouTubeChannel } from '../../types/youtube';

interface AddChannelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onChannelAdded: (channel: YouTubeChannel) => void;
}

export function AddChannelModal({ isOpen, onClose, onChannelAdded }: AddChannelModalProps) {
  const [channelId, setChannelId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [customUrl, setCustomUrl] = useState('');
  const [apiKey, setApiKey] = useState('');

  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<{ message: string; code?: string; details?: unknown } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const resetForm = () => {
    setChannelId('');
    setTitle('');
    setDescription('');
    setCustomUrl('');
    setApiKey('');
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

    const cleanChannelId = channelId.trim();
    if (!cleanChannelId) {
      setValidationError('YouTube Kanal ID kiritilishi shart.');
      return false;
    }
    if (cleanChannelId.length < 10) {
      setValidationError('YouTube Kanal ID uzunligi kamida 10 ta belgi bo‘lishi kerak (masalan: UC_x5XG1OV2P6uZZ5FSM9Ttw).');
      return false;
    }
    if (!title.trim()) {
      setValidationError('Kanal nomi kiritilishi shart.');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setApiError(null);

    try {
      const newChannel = await youtubeService.createChannel({
        channel_id: channelId.trim(),
        title: title.trim(),
        description: description.trim() || undefined,
        custom_url: customUrl.trim() || undefined,
        api_key: apiKey.trim() || undefined,
      });

      onChannelAdded(newChannel);
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
          message: 'Kanalni qo‘shishda xatolik yuz berdi.',
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
    <Modal isOpen={isOpen} onClose={handleClose} title="Yangi YouTube Kanal Qo'shish">
      {validationError && (
        <div style={{ padding: '0.75rem', backgroundColor: '#fffbeb', border: '1px solid #fef3c7', borderRadius: '6px', color: '#92400e', marginBottom: '1rem', fontSize: '0.85rem' }}>
          ⚠️ {validationError}
        </div>
      )}

      {apiError && (
        <ErrorMessage message={apiError.message} code={apiError.code} details={apiError.details} />
      )}

      <form onSubmit={handleSubmit}>
        <label style={labelStyle}>
          YouTube Channel ID *
          <input
            type="text"
            required
            value={channelId}
            onChange={(e) => setChannelId(e.target.value)}
            placeholder="UC_x5XG1OV2P6uZZ5FSM9Ttw"
            style={inputStyle}
          />
          <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'normal' }}>
            YouTube studiyangiz yoki kanal havolasidagi noyob kanal identifikatori.
          </span>
        </label>

        <label style={labelStyle}>
          Kanal Nomi *
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Google Developers"
            style={inputStyle}
          />
        </label>

        <label style={labelStyle}>
          Maxsus havola (Custom URL)
          <input
            type="text"
            value={customUrl}
            onChange={(e) => setCustomUrl(e.target.value)}
            placeholder="@googledevs"
            style={inputStyle}
          />
        </label>

        <label style={labelStyle}>
          Kanal Tavsifi (Description)
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Kanal haqida qisqacha ma'lumot..."
            style={{ ...inputStyle, resize: 'vertical' }}
          />
        </label>

        <label style={labelStyle}>
          YouTube Data API Kaliti (Ixtiyoriy)
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="AIzaSy..."
            style={inputStyle}
          />
          <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'normal' }}>
            Kanal ma'lumotlarini to'g'ridan-to'g'ri YouTube API orqali sinxronlash uchun.
          </span>
        </label>

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
          {isSubmitting ? 'Saqlanmoqda...' : 'Kanalni Qo‘shish'}
        </button>
      </form>
    </Modal>
  );
}

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createRoot } from 'react-dom/client';
import { act } from 'react';
import { AddChannelModal } from '../components/channels/AddChannelModal';
import { youtubeService } from '../services/youtubeService';

// @ts-expect-error React act flag
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

describe('AddChannelModal Security & Form Contract', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    vi.restoreAllMocks();
  });

  it('renders modal without exposing or asking for any YouTube API keys', () => {
    const root = createRoot(container);
    act(() => {
      root.render(
        <AddChannelModal
          isOpen={true}
          onClose={() => {}}
          onChannelAdded={() => {}}
        />
      );
    });

    // Verify modal rendered
    expect(container.textContent).toContain('Yangi YouTube Kanal Qo\'shish');
    expect(container.textContent).toContain('YouTube Channel ID *');
    expect(container.textContent).toContain('Kanal Nomi *');

    // CRITICAL SECURITY ASSERTION: No API Key input, label, or placeholder should ever exist in frontend
    expect(container.textContent).not.toContain('API Kaliti');
    expect(container.textContent).not.toContain('api_key');
    expect(container.querySelector('input[placeholder*="AIzaSy"]')).toBeNull();
    expect(container.querySelector('input[type="password"]')).toBeNull();

    act(() => {
      root.unmount();
    });
  });

  it('submits valid channel data without any api_key property', async () => {
    const createChannelSpy = vi.spyOn(youtubeService, 'createChannel').mockResolvedValue({
      id: 10,
      channel_id: 'UC_valid_channel_12345',
      title: 'Valid Channel',
      description: 'Channel description',
      custom_url: '@validchannel',
      published_at: null,
      subscriber_count: 0,
      video_count: 0,
      view_count: 0,
      thumbnail_url: '',
      is_active: true,
      owner_username: 'testuser',
      playlists_count: 0,
      total_videos: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const onChannelAddedMock = vi.fn();
    const onCloseMock = vi.fn();

    const root = createRoot(container);
    act(() => {
      root.render(
        <AddChannelModal
          isOpen={true}
          onClose={onCloseMock}
          onChannelAdded={onChannelAddedMock}
        />
      );
    });

    const setInputValue = (input: HTMLInputElement, val: string) => {
      const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
      if (nativeSetter) {
        nativeSetter.call(input, val);
      } else {
        input.value = val;
      }
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    };

    const inputs = container.querySelectorAll('input');
    const channelIdInput = inputs[0] as HTMLInputElement;
    const titleInput = inputs[1] as HTMLInputElement;

    act(() => {
      setInputValue(channelIdInput, 'UC_valid_channel_12345');
      setInputValue(titleInput, 'Valid Channel');
    });

    const form = container.querySelector('form');
    expect(form).not.toBeNull();

    await act(async () => {
      form?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    });

    // Check that createChannel was called with sanitized, secure payload
    expect(createChannelSpy).toHaveBeenCalledWith({
      channel_id: 'UC_valid_channel_12345',
      title: 'Valid Channel',
      description: undefined,
      custom_url: undefined,
    });

    const callArg = createChannelSpy.mock.calls[0][0];
    expect(callArg).not.toHaveProperty('api_key');

    act(() => {
      root.unmount();
    });
  });
});

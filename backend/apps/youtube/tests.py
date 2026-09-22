"""
Unit and Integration Tests for YouTube API and Models.
Verifies CRUD operations, permissions, constraints, validations, and query optimizations.
"""
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from .models import YouTubeChannel, YouTubePlaylist, YouTubeVideo, SyncJob


class YouTubeAPITests(APITestCase):
    def setUp(self):
        # Users
        self.user1 = User.objects.create_user(
            username='creator1',
            email='creator1@example.com',
            password='Password123!'
        )
        self.token1 = Token.objects.create(user=self.user1)

        self.user2 = User.objects.create_user(
            username='creator2',
            email='creator2@example.com',
            password='Password123!'
        )
        self.token2 = Token.objects.create(user=self.user2)

        # Base Channel owned by user1
        self.channel1 = YouTubeChannel.objects.create(
            owner=self.user1,
            channel_id='UC_x5XG1OV2P6uZZ5FSM9Ttw',
            title='Google Developers',
            description='The official channel for Google Developers.',
            subscriber_count=2300000,
            video_count=5400,
            view_count=180000000
        )

        # Playlist for channel1
        self.playlist1 = YouTubePlaylist.objects.create(
            channel=self.channel1,
            playlist_id='PLOU2XLYxmsIKN6f4bS0tN6qFjVp9q',
            title='Android Dev Summit'
        )

        # Videos for channel1
        self.video1 = YouTubeVideo.objects.create(
            channel=self.channel1,
            playlist=self.playlist1,
            video_id='dQw4w9WgXcQ',
            title='First Integration Video',
            description='Testing YouTube API integration',
            published_at=timezone.now(),
            duration_seconds=213,
            view_count=150000,
            like_count=9800,
            comment_count=450,
            privacy_status='public'
        )

        self.video2 = YouTubeVideo.objects.create(
            channel=self.channel1,
            video_id='kJQP7kiw5Fk',
            title='Second Integration Video',
            description='Second testing video',
            published_at=timezone.now(),
            duration_seconds=300,
            view_count=50000,
            like_count=3200,
            comment_count=120,
            privacy_status='public'
        )

    # 1. Channels Tests
    def test_list_channels_unauthenticated(self):
        """Anonim so'rov rad etilishi shart (regressiya himoyasi).

        Ilgari bu endpoint AllowAny edi va barcha foydalanuvchilar kanallarini
        tokensiz qaytarardi. Test o'sha zaiflikni tasdiqlab turardi.
        """
        url = reverse('youtube-channel-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_channels_authenticated_returns_only_own(self):
        url = reverse('youtube-channel-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Google Developers')

        # user2 ning ro'yxati bo'sh — IDOR yo'q
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        other = self.client.get(url)
        self.assertEqual(other.status_code, status.HTTP_200_OK)
        self.assertEqual(other.data['count'], 0)

    def test_create_channel_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('youtube-channel-list')
        payload = {
            'channel_id': 'UCBJycsmduvYEL83R_U4JriQ',
            'title': 'Marques Brownlee',
            'description': 'Tech reviews',
            'subscriber_count': 18000000,
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Marques Brownlee')
        # Ensure API key is NEVER exposed in API response
        self.assertNotIn('api_key', response.data)
        # Ensure owner is set to user1
        created_channel = YouTubeChannel.objects.get(channel_id='UCBJycsmduvYEL83R_U4JriQ')
        self.assertEqual(created_channel.owner, self.user1)

    def test_api_key_never_exposed_or_required_from_frontend(self):
        """Verify API key is completely isolated to backend and not accepted or exposed in serializer."""
        from .serializers import YouTubeChannelSerializer
        serializer = YouTubeChannelSerializer()
        self.assertNotIn('api_key', serializer.fields)


    def test_create_channel_validation_short_channel_id(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('youtube-channel-list')
        payload = {
            'channel_id': 'short',
            'title': 'Invalid Channel'
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_update_channel_permission_denied_for_non_owner(self):
        # user2 tries to update user1's channel
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('youtube-channel-detail', kwargs={'pk': self.channel1.pk})
        response = self.client.patch(url, {'title': 'Hacked Title'})
        self.assertIn(response.status_code,
                      (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

    def test_update_channel_allowed_for_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('youtube-channel-detail', kwargs={'pk': self.channel1.pk})
        response = self.client.patch(url, {'title': 'Google Devs Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Google Devs Updated')

    # 2. Trigger Sync Action
    def test_trigger_channel_sync(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('youtube-channel-trigger-sync', kwargs={'pk': self.channel1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'completed')
        self.assertTrue(SyncJob.objects.filter(channel=self.channel1).exists())

    # 3. Video Tests & Statistics
    def test_list_videos_with_search_and_filter(self):
        url = reverse('youtube-video-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')

        # Search by title
        response = self.client.get(url, {'search': 'First'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['video_id'], 'dQw4w9WgXcQ')

        # Filter by channel_id
        response2 = self.client.get(url, {'channel_id': self.channel1.channel_id})
        self.assertEqual(response2.data['count'], 2)

    def test_video_statistics_endpoint(self):
        url = reverse('youtube-video-statistics')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        data = response.data['data']
        self.assertEqual(data['total_videos'], 2)
        self.assertEqual(data['total_views'], 200000)
        self.assertEqual(data['total_likes'], 13000)
        self.assertEqual(data['total_comments'], 570)

    def test_video_id_validation_length(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('youtube-video-list')
        payload = {
            'channel': self.channel1.pk,
            'video_id': 'invalid_id',  # Not 11 chars
            'title': 'Bad video'
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    # 4. N+1 Query Optimization Check
    def test_channel_list_query_efficiency(self):
        # Create additional channels to verify query count is O(1) constant
        for i in range(5):
            ch = YouTubeChannel.objects.create(
                owner=self.user1,
                channel_id=f'UC_bulk_channel_id_{i:04d}',
                title=f'Channel {i}'
            )
            YouTubePlaylist.objects.create(channel=ch, playlist_id=f'PL_bulk_{i:04d}', title=f'PL {i}')
            YouTubeVideo.objects.create(channel=ch, video_id=f'vid_{i:08d}', title=f'Vid {i}')

        url = reverse('youtube-channel-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        # COUNT + SELECT + TokenAuthentication uchun bitta token/user SELECT'i
        with self.assertNumQueries(3):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['count'], 6)

    def test_delete_channel_forbidden_for_other_users(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('youtube-channel-detail', kwargs={'pk': self.channel1.pk})
        response = self.client.delete(url)
        # 404 — 403 dan yaxshiroq: obyekt mavjudligi ham oshkor qilinmaydi
        self.assertIn(response.status_code,
                      (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))
        self.assertTrue(YouTubeChannel.objects.filter(pk=self.channel1.pk).exists())

    def test_delete_channel_allowed_for_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('youtube-channel-detail', kwargs={'pk': self.channel1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(YouTubeChannel.objects.filter(pk=self.channel1.pk).exists())

    def test_playlist_creation_and_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('youtube-playlist-list')
        payload = {
            'channel': self.channel1.pk,
            'playlist_id': 'PL_test_custom_playlist_id_99',
            'title': 'New Playlist',
            'description': 'Testing playlist'
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Playlist')
        self.assertEqual(response.data['channel_title'], self.channel1.title)

    def test_not_found_error_structure(self):
        url = reverse('youtube-channel-detail', kwargs={'pk': 999999})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn(response.data['error']['code'], ['Http404', 'NotFound'])


from unittest.mock import patch, MagicMock
from .services import YouTubeService, YouTubeAPIError


class YouTubeServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='syncuser', password='Password123!')
        self.channel = YouTubeChannel.objects.create(
            owner=self.user,
            channel_id='UC_mock_channel_12345',
            title='Mock Channel',
            api_key='mock_live_api_key_sample'
        )

    @patch('requests.get')
    def test_sync_channel_with_api_mock(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [{
                'snippet': {
                    'title': 'Mock Channel Updated Title',
                    'description': 'Updated description',
                    'customUrl': '@mockchannel',
                    'thumbnails': {'high': {'url': 'https://example.com/high.jpg'}}
                },
                'statistics': {
                    'subscriberCount': '500000',
                    'videoCount': '150',
                    'viewCount': '12500000'
                }
            }]
        }
        mock_get.return_value = mock_response

        service = YouTubeService(api_key='mock_live_api_key_sample')
        job = service.sync_channel(self.channel)

        self.channel.refresh_from_db()
        self.assertEqual(job.status, SyncJob.Status.COMPLETED)
        self.assertEqual(self.channel.title, 'Mock Channel Updated Title')
        self.assertEqual(self.channel.subscriber_count, 500000)
        self.assertEqual(self.channel.video_count, 150)
        self.assertEqual(self.channel.view_count, 12500000)

    @patch('requests.get')
    def test_sync_channel_api_error_handling(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.json.return_value = {
            'error': {'message': 'Quota exceeded'}
        }
        mock_get.return_value = mock_response

        service = YouTubeService(api_key='mock_live_api_key_sample')
        job = service.sync_channel(self.channel)

        self.assertEqual(job.status, SyncJob.Status.FAILED)
        self.assertIn('Quota exceeded', job.error_message)

    def test_missing_api_key_raises_error(self):
        service = YouTubeService(api_key='')
        with self.assertRaises(YouTubeAPIError):
            service.fetch_channel_details('UC_any_channel')


class YouTubeSecurityTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='channel_owner', password='Password123!')
        self.attacker = User.objects.create_user(username='attacker_user', password='Password123!')
        self.attacker_token = Token.objects.create(user=self.attacker)

        self.victim_channel = YouTubeChannel.objects.create(
            owner=self.owner,
            channel_id='UC_victim_channel_9999',
            title='Victim Channel'
        )

    def test_create_playlist_idor_blocked(self):
        # Attacker tries to inject a playlist into Victim's channel
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.attacker_token.key}')
        url = reverse('youtube-playlist-list')
        payload = {
            'channel': self.victim_channel.pk,
            'playlist_id': 'PL_hacked_playlist_1',
            'title': 'Hacked Playlist'
        }
        response = self.client.post(url, payload)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        self.assertFalse(YouTubePlaylist.objects.filter(playlist_id='PL_hacked_playlist_1').exists())

    def test_create_video_idor_blocked(self):
        # Attacker tries to inject a video into Victim's channel
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.attacker_token.key}')
        url = reverse('youtube-video-list')
        payload = {
            'channel': self.victim_channel.pk,
            'video_id': 'hacked_vid1',
            'title': 'Hacked Video'
        }
        response = self.client.post(url, payload)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        self.assertFalse(YouTubeVideo.objects.filter(video_id='hacked_vid1').exists())

    def test_channel_id_regex_sanitization(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.attacker_token.key}')
        url = reverse('youtube-channel-list')
        payload = {
            'channel_id': 'UC_bad<script>alert(1)</script>',
            'title': 'XSS Attack Channel'
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(YouTubeChannel.objects.filter(title='XSS Attack Channel').exists())

    def test_video_cross_channel_playlist_blocked(self):
        # Create channel for attacker
        attacker_channel = YouTubeChannel.objects.create(
            owner=self.attacker,
            channel_id='UC_attacker_channel_1111',
            title='Attacker Channel'
        )
        # Playlist belongs to victim channel
        victim_playlist = YouTubePlaylist.objects.create(
            channel=self.victim_channel,
            playlist_id='PL_victim_sec_play',
            title='Victim Playlist'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.attacker_token.key}')
        url = reverse('youtube-video-list')
        payload = {
            'channel': attacker_channel.pk,
            'playlist': victim_playlist.pk,
            'video_id': 'cross_vid_01',
            'title': 'Cross Injected Video'
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(YouTubeVideo.objects.filter(video_id='cross_vid_01').exists())





class AutomationEndpointSecurityTests(APITestCase):
    """Regressiya himoyasi: avtomatlashtirish API si anonim kirishga ochilmasin.

    Tarixda `0fd109a "remove auth barriers"` commiti 9 ta ViewSet'ni AllowAny
    qilib qo'ygan edi va tizim shu holatda Cloudflare tunnel orqali internetga
    chiqarilgandi. Bu testlar o'sha regressiyani qaytadan sodir bo'lishidan
    saqlaydi — himoya yechilsa, CI darhol qizaradi.
    """

    ANON_BLOCKED = (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    LIST_ROUTES = [
        'youtube-channel-list',
        'youtube-playlist-list',
        'youtube-video-list',
        'sync-job-list',
        'flow-account-list',
        'channel-niche-list',
        'generation-task-list',
        'scheduled-upload-list',
        'daily-analytic-list',
    ]

    def _resolve(self, name):
        try:
            return reverse(name)
        except Exception:
            return None

    def test_anonymous_read_is_blocked(self):
        checked = 0
        for name in self.LIST_ROUTES:
            url = self._resolve(name)
            if url is None:
                continue
            checked += 1
            with self.subTest(route=name):
                self.assertIn(self.client.get(url).status_code, self.ANON_BLOCKED)
        self.assertGreaterEqual(checked, 5, "Marshrut nomlari o'zgargan — testni yangilang")

    def test_anonymous_write_is_blocked(self):
        for name in self.LIST_ROUTES:
            url = self._resolve(name)
            if url is None:
                continue
            with self.subTest(route=name):
                # Bo'sh body: himoya bo'lsa 401/403, bo'lmasa validatsiya 400 beradi
                self.assertIn(self.client.post(url, {}, format='json').status_code,
                              self.ANON_BLOCKED)

    def test_no_viewset_uses_allow_any(self):
        """Kod darajasidagi qo'riqchi — AllowAny qaytib kelsa test yiqiladi."""
        from pathlib import Path
        source = Path(__file__).with_name('views.py').read_text(encoding='utf-8')
        self.assertNotIn('permissions.AllowAny', source,
                         "views.py da AllowAny paydo bo'ldi — avtomatlashtirish API si "
                         "anonim kirishga ochilgan bo'lishi mumkin.")


class ScheduledUploadStateMachineTests(APITestCase):
    """Holat o'tishlari: nashr qilinganni qayta tasdiqlash/bekor qilish mumkin emas."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner', email='owner@example.com', password='Password123!')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.channel = YouTubeChannel.objects.create(
            owner=self.user, channel_id='UC_state_machine_test_1', title='SM Channel')

    def _upload(self, upload_status):
        from .models import ScheduledUpload, VideoGenerationTask
        task = VideoGenerationTask.objects.create(
            topic='SM topic', prompt='SM prompt',
            status=VideoGenerationTask.GenerationStatus.COMPLETED,
        )
        self._slot_seq = getattr(self, '_slot_seq', 0) + 1
        return ScheduledUpload.objects.create(
            channel=self.channel,
            video_task=task,
            title='Test video',
            scheduled_date=timezone.now().date() + timedelta(days=self._slot_seq),
            scheduled_time='19:00:00',
            status=upload_status,
        )

    def test_confirm_rejects_already_published(self):
        from .models import ScheduledUpload
        up = self._upload(ScheduledUpload.UploadStatus.PUBLISHED)
        url = reverse('scheduled-upload-confirm-upload', kwargs={'pk': up.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        up.refresh_from_db()
        self.assertEqual(up.status, ScheduledUpload.UploadStatus.PUBLISHED)

    def test_confirm_accepts_pending_confirmation(self):
        from .models import ScheduledUpload
        up = self._upload(ScheduledUpload.UploadStatus.PENDING_CONFIRMATION)
        url = reverse('scheduled-upload-confirm-upload', kwargs={'pk': up.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        up.refresh_from_db()
        self.assertEqual(up.status, ScheduledUpload.UploadStatus.SCHEDULED)

    def test_cancel_rejects_published(self):
        from .models import ScheduledUpload
        up = self._upload(ScheduledUpload.UploadStatus.PUBLISHED)
        url = reverse('scheduled-upload-cancel-upload', kwargs={'pk': up.pk})
        self.assertEqual(self.client.post(url).status_code, status.HTTP_409_CONFLICT)

    def test_status_cannot_be_set_via_patch(self):
        """serializers.py read_only_fields — tasdiqlash oqimini aylanib o'tish yo'li."""
        from .models import ScheduledUpload
        up = self._upload(ScheduledUpload.UploadStatus.PENDING_CONFIRMATION)
        url = reverse('scheduled-upload-detail', kwargs={'pk': up.pk})
        self.client.patch(url, {'status': 'published',
                                'youtube_video_id': 'HACKED12345'}, format='json')
        up.refresh_from_db()
        self.assertEqual(up.status, ScheduledUpload.UploadStatus.PENDING_CONFIRMATION)
        self.assertEqual(up.youtube_video_id, '')


class FlowAccountCreditTests(APITestCase):
    """Kredit hisobi: mass-assignment yo'q, yechish atomik."""

    def setUp(self):
        # Flow AI akkauntlari kanalga bog'lanmagan resurs — ularni o'zgartirish
        # staff huquqini talab qiladi (IsOwnerOfRelatedChannel).
        self.user = User.objects.create_user(
            username='creditor', email='c@example.com', password='Password123!',
            is_staff=True)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        from .models import FlowAIAccount
        self.account = FlowAIAccount.objects.create(
            name='Test Profile', profile_dir='Profile 1',
            credits_remaining=1000, initial_credits=1000, is_active=True)

    def test_credits_cannot_be_set_via_patch(self):
        """Staff bo'lsa ham kredit maydoni serializer darajasida read-only."""
        url = reverse('flow-account-detail', kwargs={'pk': self.account.pk})
        self.client.patch(url, {'credits_remaining': 999999}, format='json')
        self.account.refresh_from_db()
        self.assertEqual(self.account.credits_remaining, 1000)

    def test_non_staff_cannot_modify_flow_account(self):
        other = User.objects.create_user(
            username='plain', email='p@example.com', password='Password123!')
        other_token = Token.objects.create(user=other)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        url = reverse('flow-account-inspect-account', kwargs={'pk': self.account.pk})
        response = self.client.post(url, {'credits_remaining': 500}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inspect_account_rejects_non_integer_credits(self):
        url = reverse('flow-account-inspect-account', kwargs={'pk': self.account.pk})
        response = self.client.post(url, {'credits_remaining': 'abc'}, format='json')
        # Ilgari int('abc') -> ValueError -> HTTP 500 bo'lardi
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inspect_account_rejects_negative_credits(self):
        url = reverse('flow-account-inspect-account', kwargs={'pk': self.account.pk})
        response = self.client.post(url, {'credits_remaining': -5}, format='json')
        # Ilgari DB CHECK constraint -> IntegrityError -> HTTP 500
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

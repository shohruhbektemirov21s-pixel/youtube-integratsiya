"""
Unit and Integration Tests for YouTube API and Models.
Verifies CRUD operations, permissions, constraints, validations, and query optimizations.
"""
from django.contrib.auth.models import User
from django.urls import reverse
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
        url = reverse('youtube-channel-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Google Developers')

    def test_create_channel_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('youtube-channel-list')
        payload = {
            'channel_id': 'UCBJycsmduvYEL83R_U4JriQ',
            'title': 'Marques Brownlee',
            'description': 'Tech reviews',
            'subscriber_count': 18000000,
            'api_key': 'secret-api-key-test'
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Marques Brownlee')
        # Ensure api_key is write_only and not leaked
        self.assertNotIn('api_key', response.data)
        # Ensure owner is set to user1
        created_channel = YouTubeChannel.objects.get(channel_id='UCBJycsmduvYEL83R_U4JriQ')
        self.assertEqual(created_channel.owner, self.user1)

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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
        # With pagination and annotations, query count is strictly bounded (COUNT query + SELECT query)
        with self.assertNumQueries(2):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['count'], 6)

    def test_delete_channel_forbidden_for_other_users(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('youtube-channel-detail', kwargs={'pk': self.channel1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
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



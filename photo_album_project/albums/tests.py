from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from .models import Tag, Album, AlbumTemplate, Photo, AlbumPhoto, Review

User = get_user_model()


class BaseTestCase(TestCase):
    """Базовый класс с общими данными для всех тестов."""

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123',
            email='other@test.com'
        )
        self.admin = User.objects.create_user(
            username='adminuser',
            password='testpass123',
            email='admin@test.com',
            role='admin'
        )
        self.tag = Tag.objects.create(name='тестовый тег', color='#FF5733')
        self.template = AlbumTemplate.objects.create(
            name='Классический',
            is_premium=False
        )
        self.album = Album.objects.create(
            user=self.user,
            title='Мой альбом',
            description='Описание'
        )
        small_image = SimpleUploadedFile(
            'test.jpg',
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
        self.photo = Photo.objects.create(
            user=self.user,
            title='Моё фото',
            image=small_image
        )


class TagValidationTest(BaseTestCase):
    """Тесты валидации тегов."""

    def test_invalid_color_format(self) -> None:
        """Тест: неверный формат цвета тега возвращает 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/tags/', {
            'name': 'новый тег',
            'color': 'red'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('color', response.data)

    def test_valid_color_format(self) -> None:
        """Тест: верный формат цвета тега возвращает 201."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/tags/', {
            'name': 'новый тег',
            'color': '#AABBCC'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_tag_name_too_short(self) -> None:
        """Тест: название тега короче 2 символов возвращает 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/tags/', {
            'name': 'a',
            'color': '#FF5733'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AlbumValidationTest(BaseTestCase):
    """Тесты валидации альбомов."""

    def test_album_title_too_short(self) -> None:
        """Тест: название альбома короче 3 символов возвращает 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/albums/', {
            'title': 'аб',
            'description': 'описание'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_album_title_unique_per_user(self) -> None:
        """Тест: дублирующееся название альбома у одного юзера возвращает 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/albums/', {
            'title': 'Мой альбом',
            'description': 'описание'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_album_title_duplicate_allowed_for_other_user(self) -> None:
        """Тест: одинаковое название альбома у разных юзеров разрешено."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post('/api/albums/', {
            'title': 'Мой альбом',
            'description': 'описание'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ReviewValidationTest(BaseTestCase):
    """Тесты валидации отзывов."""

    def test_rating_out_of_range(self) -> None:
        """Тест: оценка вне диапазона 1-5 возвращает 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/reviews/', {
            'email': 'test@test.com',
            'text': 'Отличный сервис для фото',
            'rating': 6
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rating', response.data)

    def test_review_text_too_short(self) -> None:
        """Тест: текст отзыва короче 10 символов возвращает 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/reviews/', {
            'email': 'test@test.com',
            'text': 'Коротко',
            'rating': 5
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('text', response.data)

    def test_valid_review_created(self) -> None:
        """Тест: корректный отзыв создаётся успешно."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/reviews/', {
            'email': 'test@test.com',
            'text': 'Отличный сервис, буду пользоваться!',
            'rating': 5
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PermissionsTest(BaseTestCase):
    """Тесты прав доступа."""

    def test_other_user_cannot_delete_album(self) -> None:
        """Тест: чужой пользователь не может удалить альбом — 403."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(f'/api/albums/{self.album.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_album(self) -> None:
        """Тест: владелец может удалить свой альбом — 204."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/albums/{self.album.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_delete_any_album(self) -> None:
        """Тест: администратор может удалить любой альбом — 204."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/albums/{self.album.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class AddPhotoTest(BaseTestCase):
    """Тесты добавления фото в альбом."""

    def test_cannot_add_other_users_photo(self) -> None:
        """Тест: нельзя добавить чужое фото в альбом — 403."""
        self.client.force_authenticate(user=self.other_user)
        other_album = Album.objects.create(
            user=self.other_user,
            title='Альбом другого'
        )
        response = self.client.post(f'/api/albums/{other_album.id}/add_photo/', {
            'photo_id': self.photo.id,
            'order': 0
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_add_photo_twice(self) -> None:
        """Тест: нельзя добавить одно фото в альбом дважды — 400."""
        self.client.force_authenticate(user=self.user)
        AlbumPhoto.objects.create(album=self.album, photo=self.photo, order=0)
        response = self.client.post(f'/api/albums/{self.album.id}/add_photo/', {
            'photo_id': self.photo.id,
            'order': 1
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewVisibilityTest(BaseTestCase):
    """Тесты видимости отзывов."""

    def setUp(self) -> None:
        super().setUp()
        self.published_review = Review.objects.create(
            user=self.user,
            email='test@test.com',
            text='Опубликованный отзыв о сервисе',
            rating=5,
            is_published=True
        )
        self.unpublished_review = Review.objects.create(
            user=self.other_user,
            email='other@test.com',
            text='Неопубликованный отзыв о сервисе',
            rating=3,
            is_published=False
        )

    def test_anonymous_sees_only_published(self) -> None:
        """Тест: анонимный пользователь видит только опубликованные отзывы."""
        response = self.client.get('/api/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r['id'] for r in response.data['results']]
        self.assertIn(self.published_review.id, ids)
        self.assertNotIn(self.unpublished_review.id, ids)

    def test_admin_sees_all_reviews(self) -> None:
        """Тест: администратор видит все отзывы включая неопубликованные."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r['id'] for r in response.data['results']]
        self.assertIn(self.published_review.id, ids)
        self.assertIn(self.unpublished_review.id, ids)

    def test_regular_user_cannot_publish_review(self) -> None:
        """Тест: обычный пользователь не может опубликовать отзыв — 403."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/reviews/{self.unpublished_review.id}/publish/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_publish_review(self) -> None:
        """Тест: администратор может опубликовать отзыв."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'/api/reviews/{self.unpublished_review.id}/publish/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unpublished_review.refresh_from_db()
        self.assertTrue(self.unpublished_review.is_published)
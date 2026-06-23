from django.core.mail import send_mail

from .filters import PhotoFilter, AlbumFilter
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json

from django.db.models import Q, Count, QuerySet

from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request

from .models import Tag, AlbumTemplate, Photo, Album, AlbumPhoto, Review
from .serializers import (
    TagSerializer, AlbumTemplateSerializer, PhotoSerializer,
    AlbumSerializer, AlbumPhotoSerializer, ReviewSerializer
)
from .permissions import IsOwnerOrAdmin

User = get_user_model()


class StandardPagination(PageNumberPagination):
    """Стандартная пагинация: 10 элементов на страницу, максимум 100."""

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet для управления тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = StandardPagination


class AlbumTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet для управления шаблонами оформления альбомов."""

    queryset = AlbumTemplate.objects.all()
    serializer_class = AlbumTemplateSerializer
    pagination_class = StandardPagination


class PhotoViewSet(viewsets.ModelViewSet):
    """ViewSet для управления фотографиями."""

    serializer_class = PhotoSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PhotoFilter
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'title']

    def get_queryset(self) -> QuerySet:
        """
        Возвращает QuerySet фотографий с оптимизированными запросами.
        Поддерживает фильтрацию по тегам через query-параметр tags.

        Returns:
            QuerySet фотографий
        """
        queryset = Photo.objects.select_related('user').prefetch_related('tags')
        tag_filter = self.request.query_params.get('tags')
        if tag_filter:
            tag_list = tag_filter.split(',')
            queryset = queryset.filter(tags__name__in=tag_list).distinct()
        return queryset

    def get_serializer_context(self) -> dict:
        """
        Расширяет контекст сериализатора — передаёт список id тегов текущего пользователя.

        Returns:
            Словарь контекста с ключом user_tag_ids
        """
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context['user_tag_ids'] = list(
                self.request.user.photos.values_list('tags__id', flat=True)
            )
        else:
            context['user_tag_ids'] = []
        return context

    def perform_create(self, serializer) -> None:
        """
        Сохраняет фотографию с привязкой к текущему пользователю.

        Args:
            serializer: валидированный сериализатор фотографии
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request: Request) -> Response:
        """
        Поиск фотографий по названию и описанию.
        Для авторизованных пользователей — только среди своих фото.

        Args:
            request: объект запроса с параметром q

        Returns:
            Пагинированный список фотографий
        """
        query = request.query_params.get('q', '')
        q_objects = Q(title__icontains=query) | Q(description__icontains=query)
        if request.user.is_authenticated:
            q_objects &= Q(user=request.user)
        photos = Photo.objects.select_related('user').prefetch_related('tags').filter(q_objects)
        page = self.paginate_queryset(photos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(photos, many=True)
        return Response(serializer.data)


class AlbumViewSet(viewsets.ModelViewSet):
    """ViewSet для управления альбомами."""

    serializer_class = AlbumSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AlbumFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'photo_count']

    def get_queryset(self) -> QuerySet:
        """
        Возвращает QuerySet альбомов с аннотацией photo_count и оптимизированными запросами.

        Returns:
            QuerySet альбомов
        """
        queryset = Album.objects.annotate(
            photo_count=Count('albumphoto')
        ).select_related('user', 'template').prefetch_related(
            'albumphoto_set__photo',
            'albumphoto_set__photo__tags'
        )
        user_filter = self.request.query_params.get('user')
        if user_filter:
            queryset = queryset.filter(user__username=user_filter)
        return queryset

    def perform_create(self, serializer) -> None:
        """
        Сохраняет альбом с привязкой к текущему пользователю.

        Args:
            serializer: валидированный сериализатор альбома
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my(self, request: Request) -> Response:
        """
        Возвращает список альбомов текущего пользователя.

        Args:
            request: объект запроса

        Returns:
            Список альбомов пользователя
        """
        albums = Album.objects.annotate(
            photo_count=Count('albumphoto')
        ).select_related('user', 'template').filter(user=request.user)
        serializer = self.get_serializer(albums, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_photo(self, request: Request, pk: int = None) -> Response:
        """
        Добавляет фотографию в альбом. Только свои фотографии.

        Args:
            request: объект запроса с photo_id и order
            pk: id альбома

        Returns:
            Созданная связь альбом-фото или ошибка
        """
        album = self.get_object()
        photo_id = request.data.get('photo_id')
        order = request.data.get('order', 0)
        try:
            photo = Photo.objects.get(id=photo_id)
            if photo.user != request.user:
                return Response(
                    {'error': 'Вы можете добавлять только свои фотографии'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if AlbumPhoto.objects.filter(album=album, photo=photo).exists():
                return Response(
                    {'error': 'Фотография уже в альбоме'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            album_photo = AlbumPhoto.objects.create(album=album, photo=photo, order=order)
            serializer = AlbumPhotoSerializer(album_photo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Photo.DoesNotExist:
            return Response(
                {'error': 'Фотография не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )


class AlbumPhotoViewSet(viewsets.ModelViewSet):
    """ViewSet для управления связями альбом-фотография."""

    queryset = AlbumPhoto.objects.select_related('album', 'photo', 'photo__user')
    serializer_class = AlbumPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance) -> None:
        """
        Удаляет связь альбом-фото и саму фотографию.

        Args:
            instance: объект AlbumPhoto
        """
        photo = instance.photo
        instance.delete()
        photo.delete()


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet для управления отзывами о сервисе."""

    serializer_class = ReviewSerializer
    pagination_class = StandardPagination

    def get_queryset(self) -> QuerySet:
        """
        Возвращает все отзывы для админа, только опубликованные для остальных.

        Returns:
            QuerySet отзывов
        """
        user = self.request.user
        if user.is_authenticated and user.role == 'admin':
            return Review.objects.select_related('user').all()
        return Review.objects.select_related('user').filter(is_published=True)

    def get_permissions(self) -> list:
        """
        Определяет права доступа в зависимости от действия.

        Returns:
            Список объектов разрешений
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer) -> None:
        """
        Сохраняет отзыв и отправляет уведомление администратору.

        Args:
            serializer: валидированный сериализатор отзыва
        """
        review = serializer.save(user=self.request.user)
        send_mail(
            subject=f'Новый отзыв от {review.user.username}',
            message=f'Оценка: {review.rating}/5\n\nТекст: {review.text}\n\nEmail для связи: {review.email}',
            from_email='noreply@photoalbum.local',
            recipient_list=['admin@photoalbum.local'],
            fail_silently=True,
    )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request: Request, pk: int = None) -> Response:
        """
        Публикует отзыв. Доступно только администратору.

        Args:
            request: объект запроса
            pk: id отзыва

        Returns:
            Подтверждение публикации или ошибка доступа
        """
        if request.user.role != 'admin':
            return Response({'error': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        review = self.get_object()
        review.is_published = True
        review.save()
        return Response({'status': 'Отзыв опубликован'})


def home_page(request: HttpRequest) -> HttpResponse:
    """Главная страница приложения."""
    return render(request, 'albums/home.html')


def album_detail_page(request: HttpRequest, album_id: int) -> HttpResponse:
    """
    Страница детального просмотра альбома.

    Args:
        request: объект запроса
        album_id: id альбома
    """
    try:
        album = Album.objects.get(id=album_id)
    except Album.DoesNotExist:
        return render(request, 'albums/404.html', status=404)
    return render(request, 'albums/album_detail.html', {'album': album})


def photo_detail_page(request: HttpRequest, photo_id: int) -> HttpResponse:
    """
    Страница детального просмотра фотографии.

    Args:
        request: объект запроса
        photo_id: id фотографии
    """
    try:
        photo = Photo.objects.get(id=photo_id)
    except Photo.DoesNotExist:
        return render(request, 'albums/404.html', status=404)
    return render(request, 'albums/photo_detail.html', {'photo': photo})


@login_required
def create_album_page(request: HttpRequest) -> HttpResponse:
    """Страница создания альбома. Требует авторизации."""
    return render(request, 'albums/create_album.html')


@csrf_exempt
def api_login(request: HttpRequest) -> JsonResponse:
    """
    Аутентификация пользователя по логину и паролю.

    Args:
        request: POST-запрос с username и password

    Returns:
        JSON с результатом входа
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return JsonResponse({'success': True, 'username': user.username, 'role': user.role})
            else:
                return JsonResponse({'success': False, 'error': 'Неверные данные'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_register(request: HttpRequest) -> JsonResponse:
    """
    Регистрация нового пользователя.

    Args:
        request: POST-запрос с username, email и password

    Returns:
        JSON с результатом регистрации
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Пользователь уже существует'}, status=400)
            User.objects.create_user(username=username, email=email, password=password)
            return JsonResponse({'success': True, 'message': 'Пользователь создан'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_logout(request: HttpRequest) -> JsonResponse:
    """
    Выход пользователя из системы.

    Args:
        request: POST-запрос

    Returns:
        JSON с подтверждением выхода
    """
    if request.method == 'POST':
        auth_logout(request)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)
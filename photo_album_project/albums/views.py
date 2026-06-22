# 1. Импорты
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
import json

from django.db.models import Q, Count

from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Tag, AlbumTemplate, Photo, Album, AlbumPhoto
from .serializers import (
    TagSerializer, AlbumTemplateSerializer, PhotoSerializer, 
    AlbumSerializer, AlbumPhotoSerializer, UserSerializer
)


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = StandardPagination

class AlbumTemplateViewSet(viewsets.ModelViewSet):
    queryset = AlbumTemplate.objects.all()
    serializer_class = AlbumTemplateSerializer
    pagination_class = StandardPagination

class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'title']

    def get_queryset(self):
        queryset = Photo.objects.select_related('user', 'album').prefetch_related('tags')
        
        tag_filter = self.request.query_params.get('tags')
        if tag_filter:
            tag_list = tag_filter.split(',')
            queryset = queryset.filter(tags__name__in=tag_list).distinct()
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        
        q_objects = Q(title__icontains=query) | Q(description__icontains=query)
        
        if request.user.is_authenticated:
            q_objects &= Q(user=request.user)
        
        photos = Photo.objects.filter(q_objects)
        page = self.paginate_queryset(photos)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(photos, many=True)
        return Response(serializer.data)

class AlbumViewSet(viewsets.ModelViewSet):
    serializer_class = AlbumSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['created_at', 'user__username']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'photo_count']

    queryset = Album.objects.annotate(
        photo_count=Count('albumphoto')
    ).select_related('user', 'template').prefetch_related(
        'albumphoto_set__photo',
        'albumphoto_set__photo__tags'
    )
  

    def get_queryset(self):
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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my(self, request):
        if not request.user.is_authenticated:
            return Response([], status=200)
    
        albums = Album.objects.filter(user=request.user)
        serializer = self.get_serializer(albums, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_photo(self, request, pk=None):
        album = self.get_object()
        photo_id = request.data.get('photo_id')
        order = request.data.get('order', 0)
        
        try:
            photo = Photo.objects.get(id=photo_id)
            
            if AlbumPhoto.objects.filter(album=album, photo=photo).exists():
                return Response(
                    {'error': 'Photo already in album'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            album_photo = AlbumPhoto.objects.create(
                album=album, 
                photo=photo, 
                order=order
            )
            
            serializer = AlbumPhotoSerializer(album_photo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Photo.DoesNotExist:
            return Response(
                {'error': 'Photo not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class AlbumPhotoViewSet(viewsets.ModelViewSet):
    queryset = AlbumPhoto.objects.all()
    serializer_class = AlbumPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_destroy(self, instance):
        # Удаляем фото ВМЕСТЕ со связью
        photo = instance.photo
        instance.delete()  # Удаляем связь
        photo.delete()   


def home_page(request):
    return render(request, 'albums/home.html')

def album_detail_page(request, album_id):
    try:
        album = Album.objects.get(id=album_id)
    except Album.DoesNotExist:
        return render(request, 'albums/404.html', status=404)
    
    return render(request, 'albums/album_detail.html', {'album': album})

def photo_detail_page(request, photo_id):
    try:
        photo = Photo.objects.get(id=photo_id)
    except Photo.DoesNotExist:
        return render(request, 'albums/404.html', status=404)
    
    return render(request, 'albums/photo_detail.html', {'photo': photo})

@login_required
def create_album_page(request):
    return render(request, 'albums/create_album.html')


@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return JsonResponse({'success': True, 'username': user.username})
            else:
                return JsonResponse({'success': False, 'error': 'Неверные данные'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def api_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Пользователь уже существует'}, status=400)
            
            user = User.objects.create_user(username=username, email=email, password=password)
            return JsonResponse({'success': True, 'message': 'Пользователь создан'})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def api_logout(request):
    if request.method == 'POST':
        auth_logout(request)
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
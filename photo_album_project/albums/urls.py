from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tags', views.TagViewSet)
router.register(r'templates', views.AlbumTemplateViewSet)
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'albums', views.AlbumViewSet, basename='album')
router.register(r'album-photos', views.AlbumPhotoViewSet)
router.register(r'reviews', views.ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.api_login, name='api-login'),
    path('register/', views.api_register, name='api-register'),
    path('logout/', views.api_logout, name='api-logout'),

    path('', views.home_page, name='home'),
    path('albums/<int:album_id>/', views.album_detail_page, name='album-detail'),
    path('albums/create/', views.create_album_page, name='create-album-page'),
    path('photos/<int:photo_id>/', views.photo_detail_page, name='photo-detail'),
]
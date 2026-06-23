from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from albums import views

urlpatterns = [
    path('silk/', include('silk.urls', namespace='silk')),
    path('', views.home_page, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('albums.urls')),
    path('albums/<int:album_id>/', views.album_detail_page, name='album-detail'),
    path('albums/create/', views.create_album_page, name='create-album-page'),
    path('photos/<int:photo_id>/', views.photo_detail_page, name='photo-detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
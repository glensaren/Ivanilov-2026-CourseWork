from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3498db')
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

class AlbumTemplate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    preview_image = models.ImageField(upload_to='templates/', blank=True)
    is_premium = models.BooleanField(default=False)
    style_config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Шаблон альбома"
        verbose_name_plural = "Шаблоны альбомов"

class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='photos/%Y/%m/%d/')
    description = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='photos')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"

class Album(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='albums')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    photos = models.ManyToManyField(Photo, through='AlbumPhoto', related_name='albums')
    template = models.ForeignKey(AlbumTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Альбом"
        verbose_name_plural = "Альбомы"

class AlbumPhoto(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['order']

    class Meta:
        verbose_name = "Фотография в альбоме"
        verbose_name_plural = "Фотографии в альбомах"
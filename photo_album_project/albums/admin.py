from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from import_export.admin import ImportExportModelAdmin
from .models import Tag, AlbumTemplate, Photo, Album, AlbumPhoto, Review, User
from simple_history.admin import SimpleHistoryAdmin




class AlbumPhotoInline(admin.TabularInline):
    model = AlbumPhoto
    extra = 1
    fields = ['photo', 'order', 'added_at']
    readonly_fields = ['added_at']


@admin.register(Tag)
class TagAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ['name', 'color_display', 'photo_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    fieldsets = (
        (None, {'fields': ('name', 'color')}),
        ('Дополнительно', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ['created_at']

    def color_display(self, obj):
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', obj.color, obj.color)
    color_display.short_description = 'Цвет'

    def photo_count(self, obj):
        count = obj.photos.count()
        url = reverse('admin:albums_photo_changelist') + f'?tags__id={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    photo_count.short_description = 'Количество фото'


@admin.register(AlbumTemplate)
class AlbumTemplateAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ['name', 'is_premium', 'preview_display', 'created_at']
    list_filter = ['is_premium', 'created_at']
    search_fields = ['name', 'description']
    fieldsets = (
        ('Основное', {'fields': ('name', 'description', 'preview_image', 'is_premium')}),
        ('Настройки стиля', {'fields': ('style_config',), 'classes': ('collapse',)}),
        ('Даты', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ['created_at']

    def preview_display(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.preview_image.url)
        return 'Нет изображения'
    preview_display.short_description = 'Превью'


@admin.register(Photo)
class PhotoAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ['title', 'user_link', 'image_display', 'tag_list', 'uploaded_at']
    list_filter = ['uploaded_at', 'tags', 'user']
    search_fields = ['title', 'description', 'user__username']
    filter_horizontal = ['tags']
    fieldsets = (
        ('Основное', {'fields': ('user', 'title', 'image', 'description')}),
        ('Теги', {'fields': ('tags',)}),
        ('Даты', {'fields': ('uploaded_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ['uploaded_at', 'updated_at']

    def user_link(self, obj):
        return obj.user.username
    user_link.short_description = 'Пользователь'

    def image_display(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return 'Нет изображения'
    image_display.short_description = 'Изображение'

    def tag_list(self, obj):
        tags = obj.tags.all()
        if tags:
            tag_links = []
            for tag in tags:
                url = reverse('admin:albums_tag_change', args=[tag.id])
                tag_links.append(f'<a href="{url}">{tag.name}</a>')
            return format_html(', '.join(tag_links))
        return 'Нет тегов'
    tag_list.short_description = 'Теги'


@admin.register(Album)
class AlbumAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ['title', 'user_link', 'template_link', 'photo_count_display', 'created_at']
    list_filter = ['created_at', 'template', 'user']
    search_fields = ['title', 'description', 'user__username']
    fieldsets = (
        ('Основное', {'fields': ('user', 'title', 'description', 'template')}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [AlbumPhotoInline]
    readonly_fields = ['created_at', 'updated_at']

    def user_link(self, obj):
        return obj.user.username
    user_link.short_description = 'Пользователь'

    def template_link(self, obj):
        if obj.template:
            url = reverse('admin:albums_albumtemplate_change', args=[obj.template.id])
            return format_html('<a href="{}">{}</a>', url, obj.template.name)
        return 'Без шаблона'
    template_link.short_description = 'Шаблон'

    def photo_count_display(self, obj):
        count = obj.photos.count()
        url = reverse('admin:albums_albumphoto_changelist') + f'?album__id={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    photo_count_display.short_description = 'Фотографий'


@admin.register(AlbumPhoto)
class AlbumPhotoAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    list_display = ['album_link', 'photo_link', 'order', 'added_at']
    list_filter = ['added_at', 'album']
    search_fields = ['album__title', 'photo__title']
    fields = ['album', 'photo', 'order', 'added_at']
    readonly_fields = ['added_at']

    def album_link(self, obj):
        url = reverse('admin:albums_album_change', args=[obj.album.id])
        return format_html('<a href="{}">{}</a>', url, obj.album.title)
    album_link.short_description = 'Альбом'

    def photo_link(self, obj):
        url = reverse('admin:albums_photo_change', args=[obj.photo.id])
        return format_html('<a href="{}">{}</a>', url, obj.photo.title)
    photo_link.short_description = 'Фотография'


@admin.register(Review)
class ReviewAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    list_display = ['user', 'rating', 'is_published', 'created_at']
    list_filter = ['is_published', 'rating', 'created_at']
    search_fields = ['user__username', 'text', 'email']
    fields = ['user', 'email', 'text', 'rating', 'is_published', 'created_at']
    readonly_fields = ['created_at']
    actions = ['publish_reviews']

    def publish_reviews(self, request, queryset):
        queryset.update(is_published=True)
    publish_reviews.short_description = 'Опубликовать выбранные отзывы'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Роль', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Роль', {'fields': ('role',)}),
    )
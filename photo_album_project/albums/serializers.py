import re
from rest_framework import serializers
from .models import Tag, AlbumTemplate, Photo, Album, AlbumPhoto, Review
from django.contrib.auth import get_user_model

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at']

    def validate_color(self, value: str) -> str:
        """
        Валидация формата цвета тега.

        Args:
            value: строка цвета в формате #RRGGBB

        Returns:
            Валидированная строка цвета
        """
        if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError('Цвет должен быть в формате #RRGGBB')
        return value

    def validate_name(self, value: str) -> str:
        """
        Валидация минимальной длины названия тега.

        Args:
            value: название тега

        Returns:
            Валидированное название
        """
        if len(value) < 2:
            raise serializers.ValidationError('Название тега должно быть не короче 2 символов')
        return value


class AlbumTemplateSerializer(serializers.ModelSerializer):
    """Сериализатор шаблона оформления альбома."""

    class Meta:
        model = AlbumTemplate
        fields = ['id', 'name', 'description', 'preview_image', 'is_premium', 'style_config', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']


class PhotoSerializer(serializers.ModelSerializer):
    """Сериализатор фотографии."""

    user = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        source='tags'
    )
    tags_count = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ['id', 'user', 'title', 'image', 'description', 'tags', 'tag_ids', 'tags_count', 'uploaded_at', 'updated_at']
        read_only_fields = ['user', 'uploaded_at', 'updated_at']

    def get_tags_count(self, obj: Photo) -> int:
        """
        Возвращает количество тегов у фотографии.

        Args:
            obj: объект фотографии

        Returns:
            Количество тегов
        """
        return obj.tags.count()

    def validate_title(self, value: str) -> str:
        """
        Валидация минимальной длины названия фото.

        Args:
            value: название фотографии

        Returns:
            Валидированное название
        """
        if len(value) < 3:
            raise serializers.ValidationError('Название должно быть не короче 3 символов')
        return value

    def validate_image(self, value) -> object:
        """
        Валидация размера загружаемого файла.

        Args:
            value: загружаемый файл изображения

        Returns:
            Валидированный файл
        """
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('Размер файла не должен превышать 10 МБ')
        return value


class AlbumPhotoSerializer(serializers.ModelSerializer):
    """Сериализатор связи альбом-фотография."""

    photo = PhotoSerializer(read_only=True)

    class Meta:
        model = AlbumPhoto
        fields = ['id', 'photo', 'order', 'added_at']
        read_only_fields = ['added_at']


class AlbumSerializer(serializers.ModelSerializer):
    """Сериализатор альбома."""

    user = UserSerializer(read_only=True)
    template = AlbumTemplateSerializer(read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=AlbumTemplate.objects.all(),
        write_only=True,
        source='template',
        required=False,
        allow_null=True
    )
    photos = AlbumPhotoSerializer(many=True, read_only=True, source='albumphoto_set')
    photo_count = serializers.IntegerField(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = ['id', 'user', 'title', 'description', 'template', 'template_id',
                  'photos', 'photo_count', 'is_owner', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_is_owner(self, obj: Album) -> bool:
        """
        Проверяет является ли текущий пользователь владельцем альбома.

        Args:
            obj: объект альбома

        Returns:
            True если текущий пользователь — владелец, иначе False
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user == obj.user
        return False

    def validate_title(self, value: str) -> str:
        """
        Валидация минимальной длины названия альбома.

        Args:
            value: название альбома

        Returns:
            Валидированное название
        """
        if len(value) < 3:
            raise serializers.ValidationError('Название должно быть не короче 3 символов')
        return value

    def validate(self, data: dict) -> dict:
        """
        Валидация уникальности названия альбома у одного пользователя.

        Args:
            data: словарь валидированных данных

        Returns:
            Валидированный словарь данных
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            title = data.get('title')
            if title:
                qs = Album.objects.filter(user=request.user, title=title)
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise serializers.ValidationError({'title': 'У вас уже есть альбом с таким названием'})
        return data


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор отзыва о сервисе."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'email', 'text', 'rating', 'is_published', 'created_at']
        read_only_fields = ['user', 'is_published', 'created_at']

    def validate_rating(self, value: int) -> int:
        """
        Валидация оценки — целое число от 1 до 5.

        Args:
            value: оценка пользователя

        Returns:
            Валидированная оценка
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5')
        return value

    def validate_text(self, value: str) -> str:
        """
        Валидация минимальной длины текста отзыва.

        Args:
            value: текст отзыва

        Returns:
            Валидированный текст
        """
        if len(value) < 10:
            raise serializers.ValidationError('Текст отзыва должен быть не короче 10 символов')
        return value
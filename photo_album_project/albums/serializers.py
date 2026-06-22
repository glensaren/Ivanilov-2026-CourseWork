from rest_framework import serializers
from .models import Tag, AlbumTemplate, Photo, Album, AlbumPhoto
from django.contrib.auth.models import User

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at']

class AlbumTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlbumTemplate
        fields = ['id', 'name', 'description', 'preview_image', 'is_premium', 'style_config', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class PhotoSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        source='tags'
    )
    
    class Meta:
        model = Photo
        fields = ['id', 'user', 'title', 'image', 'description', 'tags', 'tag_ids', 'uploaded_at', 'updated_at']
        read_only_fields = ['user', 'uploaded_at', 'updated_at']

class AlbumPhotoSerializer(serializers.ModelSerializer):
    photo = PhotoSerializer(read_only=True)
    
    class Meta:
        model = AlbumPhoto
        fields = ['id', 'photo', 'order', 'added_at']
        read_only_fields = ['added_at']

class AlbumSerializer(serializers.ModelSerializer):
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


    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user == obj.user
        return False

    class Meta:
        model = Album
        fields = ['id', 'user', 'title', 'description', 'template', 'template_id', 
                  'photos', 'photo_count', 'is_owner', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
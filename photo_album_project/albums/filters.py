import django_filters
from django.db.models import QuerySet
from .models import Photo, Album


class PhotoFilter(django_filters.FilterSet):
    """Фильтр для фотографий по названию, дате загрузки и тегам."""

    title = django_filters.CharFilter(lookup_expr='icontains')
    uploaded_at_from = django_filters.DateFilter(field_name='uploaded_at', lookup_expr='gte')
    uploaded_at_to = django_filters.DateFilter(field_name='uploaded_at', lookup_expr='lte')
    tags = django_filters.CharFilter(method='filter_by_tags')

    def filter_by_tags(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Фильтрация фотографий по списку тегов через запятую.

        Args:
            queryset: исходный QuerySet фотографий
            name: имя поля фильтра
            value: строка тегов через запятую

        Returns:
            Отфильтрованный QuerySet
        """
        tag_list = value.split(',')
        return queryset.filter(tags__name__in=tag_list).distinct()

    class Meta:
        model = Photo
        fields = ['title', 'uploaded_at_from', 'uploaded_at_to', 'tags']


class AlbumFilter(django_filters.FilterSet):
    """Фильтр для альбомов по названию, пользователю, дате и наличию шаблона."""

    title = django_filters.CharFilter(lookup_expr='icontains')
    username = django_filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    created_at_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    has_template = django_filters.BooleanFilter(field_name='template', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Album
        fields = ['title', 'username', 'created_at_from', 'created_at_to', 'has_template']
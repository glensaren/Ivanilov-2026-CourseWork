from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Album, Photo, Review
from django.contrib.auth import get_user_model

@shared_task
def send_daily_stats() -> None:
    """
    Периодическая задача: отправляет администратору ежедневную статистику.
    Запускается каждый день в 9:00 по московскому времени.
    """

    User = get_user_model()

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    new_albums = Album.objects.filter(created_at__date=yesterday).count()
    new_photos = Photo.objects.filter(uploaded_at__date=yesterday).count()
    new_reviews = Review.objects.filter(created_at__date=yesterday).count()
    new_users = User.objects.filter(date_joined__date=yesterday).count()
    total_albums = Album.objects.count()
    total_photos = Photo.objects.count()
    total_users = User.objects.count()

    message = f"""
Ежедневный отчёт — {yesterday.strftime('%d.%m.%Y')}

За вчера:
- Новых пользователей: {new_users}
- Новых альбомов: {new_albums}
- Новых фотографий: {new_photos}
- Новых отзывов: {new_reviews}

Всего в системе:
- Пользователей: {total_users}
- Альбомов: {total_albums}
- Фотографий: {total_photos}
    """

    send_mail(
        subject=f'Статистика фотоальбомов за {yesterday.strftime("%d.%m.%Y")}',
        message=message,
        from_email='noreply@photoalbum.local',
        recipient_list=['admin@photoalbum.local'],
        fail_silently=False,
    )
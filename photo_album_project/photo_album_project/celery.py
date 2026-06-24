import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_album_project.settings')

app = Celery('photo_album_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'daily-stats-report': {
        'task': 'albums.tasks.send_daily_stats',
        'schedule': crontab(hour=9, minute=0),  # каждый день в 9:00
    },
}
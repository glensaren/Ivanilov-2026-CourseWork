from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from albums.models import Tag, AlbumTemplate, Photo, Album, AlbumPhoto
from django.core.files.base import ContentFile
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Генерирует тестовые данные для конструктора фотоальбомов'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Количество тестовых фото для генерации'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(f'Генерация тестовых данных ({count} фото)...')
        
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Создан тестовый пользователь'))
        
        tags_data = [
            {'name': 'отпуск', 'color': '#FF5733'},
            {'name': 'семья', 'color': '#33FF57'},
            {'name': 'природа', 'color': '#3357FF'},
            {'name': 'город', 'color': '#F333FF'},
            {'name': 'праздник', 'color': '#33FFF3'},
        ]
        
        tags = []
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={'color': tag_data['color']}
            )
            tags.append(tag)
        
        self.stdout.write(f'Создано/найдено {len(tags)} тегов')
        
        templates_data = [
            {'name': 'Классический', 'is_premium': False},
            {'name': 'Современный', 'is_premium': False},
            {'name': 'Минимализм', 'is_premium': True},
            {'name': 'Винтаж', 'is_premium': True},
        ]
        
        templates = []
        for template_data in templates_data:
            template, created = AlbumTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': f'Шаблон "{template_data["name"]}" для фотоальбомов',
                    'is_premium': template_data['is_premium'],
                    'style_config': {'theme': 'light', 'font': 'Arial'}
                }
            )
            templates.append(template)
        
        self.stdout.write(f'Создано/найдено {len(templates)} шаблонов')
        
        photo_titles = [
            'Отпуск на море', 'Семейный ужин', 'Горный поход', 
            'Городская прогулка', 'День рождения', 'Закат в лесу',
            'Утренний кофе', 'Зимний пейзаж', 'Летний пикник', 'Ночной город'
        ]
        
        photos_created = 0
        for i in range(count):
            title = f'{photo_titles[i % len(photo_titles)]} #{i+1}'
            
            photo = Photo.objects.create(
                user=user,
                title=title,
                description=f'Тестовое описание для {title}. Сгенерировано автоматически.',
            )
            
            photo_tags = random.sample(tags, random.randint(1, 3))
            photo.tags.set(photo_tags)
            
            photos_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Создано {photos_created} тестовых фото'))
        
        album_titles = ['Летний отпуск 2024', 'Семейный архив', 'Природа России', 'Городские зарисовки']
        
        for album_title in album_titles:
            album = Album.objects.create(
                user=user,
                title=album_title,
                description=f'Альбом "{album_title}" с тестовыми фото',
                template=random.choice(templates)
            )
            
            all_photos = Photo.objects.all()[:random.randint(3, 8)]
            for order, photo in enumerate(all_photos):
                AlbumPhoto.objects.create(
                    album=album,
                    photo=photo,
                    order=order
                )
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(album_titles)} тестовых альбомов'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ'))
        self.stdout.write('='*50)
        self.stdout.write(f'Пользователей: {User.objects.count()}')
        self.stdout.write(f'Тегов: {Tag.objects.count()}')
        self.stdout.write(f'Шаблонов: {AlbumTemplate.objects.count()}')
        self.stdout.write(f'Фотографий: {Photo.objects.count()}')
        self.stdout.write(f'Альбомов: {Album.objects.count()}')
        self.stdout.write(f'Связей фото-альбом: {AlbumPhoto.objects.count()}')
        self.stdout.write('='*50)
        self.stdout.write(self.style.SUCCESS(f'Для входа используйте: test_user / testpass123'))
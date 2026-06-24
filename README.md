# Конструктор фотоальбомов

Веб-приложение на Django для создания и управления цифровыми фотоальбомами. Пользователи могут загружать фотографии, организовывать их в тематические альбомы, применять шаблоны оформления и фильтровать контент по тегам.

Выполнил: Иванилов Алексей Тимофеевич, гр. 241-321
Направление: 09.03.01 «Информатика и вычислительная техника», профиль «Веб-технологии»
Московский Политехнический Университет, 2026

## Технологии

- **Backend:** Django 6.0, Django REST Framework
- **База данных:** SQLite (разработка), PostgreSQL (продакшен)
- **Очереди задач:** Celery + Redis
- **Мониторинг ошибок:** Sentry
- **Профилировщик:** Django Silk
- **Email:** Mailhog (тестирование), SMTP (продакшен)
- **Аутентификация:** сессионная + OAuth2 через Google
- **Контейнеризация:** Docker + Docker Compose

## Функционал

**Пользователь:**
- Регистрация и вход (в том числе через Google)
- Создание альбомов с выбором шаблона оформления
- Загрузка фотографий с названием, описанием и тегами
- Фильтрация альбомов по тегам через боковую панель
- Оставление отзывов о сервисе

**Администратор:**
- Дашборд со статистикой системы
- Управление пользователями, тегами и шаблонами
- Модерация отзывов
- Ежедневная статистика на email через Celery

## Запуск через Docker

```bash
cp .env.example .env
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Запуск локально

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# В отдельных терминалах:
celery -A photo_album_project worker --loglevel=info -P solo
celery -A photo_album_project beat --loglevel=info
```

## Структура проекта
photo_album_project/

├── albums/                 # Основное приложение

│   ├── models.py           # Модели: User, Album, Photo, Tag, Review

│   ├── views.py            # ViewSet-ы и HTML-вьюхи

│   ├── serializers.py      # Сериализаторы DRF

│   ├── filters.py          # FilterSet-ы для фильтрации

│   ├── permissions.py      # Кастомные права доступа

│   ├── tasks.py            # Celery-задачи

│   └── tests.py            # 18 автотестов

├── photo_album_project/

│   ├── settings.py         # Настройки проекта

│   ├── urls.py             # Корневые маршруты

│   └── celery.py           # Конфигурация Celery

├── templates/              # HTML-шаблоны

├── Dockerfile

├── docker-compose.yml

├── nginx.conf

└── .env.example

## API

Документация API доступна через DRF Browsable API: `http://127.0.0.1:8000/api/`

Postman-коллекция с 30 запросами: `postman_collection.json`

---
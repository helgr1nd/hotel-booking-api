# Room Booking API

REST API для бронирования переговорных комнат на FastAPI.

## Описание

Сервис позволяет:
- Просматривать список комнат и их доступность
- Создавать, подтверждать и отменять бронирования
- Управлять справочниками комнат и удобств (для администраторов)
- Автоматически истекать неподтвержденные бронирования
- Отправлять напоминания о предстоящих бронированиях

## Роли

- **Anonymous**: просмотр активных комнат и доступности
- **Authenticated**: создание/просмотр/отмена своих бронирований
- **Admin**: управление комнатами/удобствами, просмотр всех бронирований

## Технологии

- FastAPI (OpenAPI / Swagger UI)
- SQLAlchemy (ORM), PostgreSQL
- Poetry (менеджер зависимостей)
- Docker, docker-compose
- Celery + RabbitMQ (фоновые задачи)
- Redis (кэш)
- pytest (тестирование)

## Быстрый старт

### Требования

- Docker и docker-compose
- Make (опционально)

### Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd room-booking-api
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
copy .env.example .env
```

3. Запустите проект:
```bash
make up
# или
docker-compose up -d
```

4. Примените миграции:
```bash
make migrate
# или
docker-compose exec api alembic upgrade head
```

5. Откройте документацию API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Создание администратора

Подключитесь к контейнеру и создайте пользователя через API или напрямую в БД:

```bash
docker-compose exec api python
```

```python
import asyncio
from app.db.session import async_session
from app.models.user import User
from app.core.security import get_password_hash

async def create_admin():
    async with async_session() as session:
        admin = User(
            email="admin@example.com",
            username="admin",
            password_hash=get_password_hash("admin123"),
            is_admin=True,
            is_active=True
        )
        session.add(admin)
        await session.commit()
        print("Admin created!")

asyncio.run(create_admin())
```

## Команды Make

```bash
make up          # Запустить все сервисы
make down        # Остановить все сервисы
make logs        # Просмотр логов
make restart     # Перезапустить сервисы
make build       # Пересобрать образы
make migrate     # Применить миграции
make test        # Запустить тесты
make lint        # Проверить код (black, flake8)
make clean       # Очистить volumes и кэш
```

## Структура проекта

```
app/
├── api/
│   ├── v1/
│   │   └── routers/      # API endpoints
│   └── dependencies.py   # FastAPI dependencies
├── core/
│   ├── cache.py         # Redis cache
│   └── security.py      # JWT, password hashing
├── db/
│   ├── base.py          # SQLAlchemy Base
│   └── session.py       # Database session
├── models/              # SQLAlchemy models
├── repositories/        # Data access layer
├── schemas/             # Pydantic schemas
├── tasks/               # Celery tasks
├── config.py            # Settings
└── main.py              # FastAPI app

alembic/                 # Database migrations
tests/                   # Tests
```

## Архитектура

Проект следует трехслойной архитектуре:

1. **API слой** (`app/api/`): FastAPI роутеры, Pydantic схемы, зависимости
2. **Service слой** (в роутерах): Бизнес-логика, валидация, работа с кэшем
3. **Repository слой** (`app/repositories/`): Доступ к БД через SQLAlchemy

## API Endpoints

### Аутентификация (`/api/v1/auth`)

- `POST /register` - Регистрация
- `POST /login` - Вход (получение JWT токенов)
- `POST /refresh` - Обновление access token
- `GET /me` - Профиль текущего пользователя

### Комнаты (`/api/v1/rooms`)

- `GET /rooms` - Список активных комнат
- `GET /rooms/{room_id}` - Детальная информация о комнате
- `GET /rooms/availability` - Поиск доступных комнат
- `POST /rooms` - Создать комнату (Admin)
- `PATCH /rooms/{room_id}` - Изменить комнату (Admin)
- `DELETE /rooms/{room_id}` - Деактивировать комнату (Admin)

### Удобства (`/api/v1/amenities`)

- `GET /amenities` - Список удобств
- `POST /amenities` - Создать удобство (Admin)
- `PATCH /amenities/{amenity_id}` - Изменить удобство (Admin)
- `DELETE /amenities/{amenity_id}` - Удалить удобство (Admin)

### Бронирования (`/api/v1/bookings`)

- `GET /bookings` - Мои бронирования
- `POST /bookings` - Создать бронирование (PENDING)
- `GET /bookings/{booking_id}` - Детальное бронирование
- `POST /bookings/{booking_id}/confirm` - Подтвердить бронирование
- `POST /bookings/{booking_id}/cancel` - Отменить бронирование
- `GET /admin/bookings` - Все бронирования (Admin)

## Бизнес-правила

- Минимальная длительность бронирования: 15 минут
- Нельзя создать бронирование в прошлом
- Запрещены пересечения бронирований для статусов CONFIRMED и PENDING
- PENDING бронирование автоматически истекает через 15 минут
- Напоминание отправляется за 30 минут до начала бронирования

## Кэширование

- `GET /rooms` - TTL 5 минут
- `GET /rooms/availability` - TTL 60 секунд
- Инвалидация при создании/изменении/отмене бронирований

## Фоновые задачи (Celery)

1. **expire_pending_booking** - Истечение неподтвержденных бронирований
2. **send_booking_reminder** - Напоминание о предстоящем бронировании

## Тестирование

Запуск тестов:

```bash
make test
# или
docker-compose exec api pytest -v
```

Покрытие кода:

```bash
make test-cov
# или
docker-compose exec api pytest --cov=app --cov-report=html
```

## Разработка

### Создание миграции

```bash
make migrate-create message="описание изменений"
# или
docker-compose exec api alembic revision --autogenerate -m "описание изменений"
```

### Применение миграций

```bash
make migrate
# или
docker-compose exec api alembic upgrade head
```

### Линтинг

```bash
make lint
# или
docker-compose exec api black app tests
docker-compose exec api flake8 app tests
```

## Переменные окружения

См. файл `.env.example` для полного списка переменных.

Основные:
- `DATABASE_URL` - URL подключения к PostgreSQL
- `REDIS_URL` - URL подключения к Redis
- `CELERY_BROKER_URL` - URL брокера для Celery
- `SECRET_KEY` - Секретный ключ для JWT
- `PENDING_BOOKING_EXPIRE_MINUTES` - Время истечения PENDING бронирований
- `BOOKING_REMINDER_MINUTES` - За сколько минут отправлять напоминание

## Лицензия

MIT

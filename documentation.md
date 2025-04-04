# Документация бэкенда для приложения поиска потерянных животных

# Обзор API

Данная документация описывает REST API бэкенда, разработанного на Python с использованием FastAPI для мобильного приложения по поиску потерянных животных с помощью искусственного интеллекта.

# Архитектура бэкенда

├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py           # Эндпоинты аутентификации
│   │   │   ├── pets.py           # Эндпоинты питомцев
│   │   │   ├── matches.py        # Эндпоинты совпадений
│   │   │   ├── users.py          # Эндпоинты пользователей
│   │   │   ├── found_pets.py     # Эндпоинты найденных животных
│   │   │   └── notifications.py  # Эндпоинты уведомлений
│   │   ├── deps.py               # Зависимости для эндпоинтов
│   │   └── routes.py             # Регистрация маршрутов
│   ├── core/
│   │   ├── config.py             # Конфигурация приложения
│   │   ├── security.py           # Безопасность и JWT
│   │   ├── exceptions.py         # Обработка исключений
│   │   └── database.py           # Соединение с БД
│   ├── models/                   # Модели данных (ORM)
│   │   ├── base.py               # Базовая модель
│   │   ├── pet.py                # Модель питомца
│   │   ├── user.py               # Модель пользователя
│   │   ├── match.py              # Модель совпадения
│   │   ├── found_pet.py          # Модель найденного питомца
│   │   ├── pet_photo.py          # Модель фотографии питомца
│   │   └── notification.py       # Модель уведомления
│   ├── repository/               # CRUD операции
│   │   ├── base.py               # Базовые CRUD операции
│   │   ├── pet.py                # CRUD для питомцев
│   │   ├── user.py               # CRUD для пользователей
│   │   ├── match.py              # CRUD для совпадений
│   │   ├── found_pet.py          # CRUD для найденных питомцев
│   │   └── notification.py       # CRUD для уведомлений
│   ├── services/
│   │   ├── pets_service.py       # Бизнес-логика для питомцев
│   │   └── notification_service.py # Сервис уведомлений
│   ├── schemas/                  # Pydantic модели
│   │   ├── pet.py                # Схемы для питомцев
│   │   ├── user.py               # Схемы для пользователей
│   │   ├── auth.py               # Схемы для аутентификации
│   │   ├── match.py              # Схемы для совпадений
│   │   ├── found_pet.py          # Схемы для найденных питомцев
│   │   └── notification.py       # Схемы для уведомлений
│   └── main.py                   # Точка входа приложения
├── pet.py                        # Модель компьютерного зрения (CV)


## Структура базы данных

### Основные таблицы:
1. **users** - Пользователи приложения
2. **pets** - Информация о питомцах
3. **pet_photos** - Фотографии питомцев
4. **found_pets** - Информация о найденных животных
5. **matches** - Совпадения между найденными и потерянными животными
6. **notifications** - Уведомления для пользователей

## Эндпоинты API

**Запрос:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7XXXXXXXXXX"
}
```
**Ответ:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7XXXXXXXXXX",
  "is_verified": false,
  "created_at": "2025-04-01T09:54:24"
}
```

#### Вход пользователя
```
POST /auth/login
```
**Запрос:**
```json
{
  "username": "user@example.com",
  "password": "SecurePass123"
}
```
**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Обновление токена
```
POST /auth/refresh
```
**Запрос:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Выход из системы
```
POST /auth/logout
```
**Запрос:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
**Ответ:**
```json
{
  "message": "Successfully logged out"
}
```

#### Запрос на верификацию email
```
POST /auth/request-verification-email
```

**Ответ:**
```json
{
  "message": "Verification email sent"
}
```

#### Верификация email
```
POST /auth/verify-email
```
**Запрос:**
```json
{
  "verification_code": "ABC123"
}
```
**Ответ:**
```json
{
  "message": "Электронная почта успешно проверена"
}
```

#### Запрос на восстановление пароля
```
POST /auth/forgot-password
```
**Запрос:**
```json
{
  "email": "user@example.com"
}
```
**Ответ:**
```json
{
  "message": "Если ваш адрес электронной почты зарегистрирован, вы получите ссылку для сброса пароля."
}
```

#### Сброс пароля
```
POST /auth/reset-password
```
**Запрос:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass123"
}
```
**Ответ:**
```json
{
  "message": "Пароль успешно сброшен"
}
```

### 2. Управление питомцами

#### Получение списка потерянных животных
```
GET /pets/lost
```
**Параметры запроса:**
- `page` (int, необязательный): Номер страницы (по умолчанию: 1)
- `limit` (int, необязательный): Количество записей на странице (по умолчанию: 20)
- `species` (string, необязательный): Вид животного (собака, кошка и т.д.)
- `location` (string, необязательный): Местоположение

**Ответ:**
```json
{
  "items": [
    {
      "id": "pet_id_1",
      "name": "Барсик",
      "species": "Кошка",
      "breed": "Британская короткошерстная",
      "color": "Серый",
      "age": 3,
      "gender": "male",
      "status": "lost",
      "lost_date": "2025-03-25",
      "lost_location": "Москва, ул. Пушкина, д.10",
      "description": "Серый кот с белой грудкой и зелеными глазами",
      "photos": ["https://api.petfinder.com/photos/123.jpg"],
      "owner": {
        "id": "user_id",
        "first_name": "Иван",
        "last_name": "Иванов"
      },
      "created_at": "2025-03-25T12:00:00"
    },
    // другие питомцы
  ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

#### Получение подробной информации о питомце
```
GET /pets/{pet_id}
```
**Ответ:**
```json
{
  "id": "pet_id_1",
  "name": "Барсик",
  "species": "Кошка",
  "breed": "Британская короткошерстная",
  "color": "Серый",
  "age": 3,
  "gender": "male",
  "status": "lost",
  "lost_date": "2025-03-25",
  "lost_location": "Москва, ул. Пушкина, д.10",
  "description": "Серый кот с белой грудкой и зелеными глазами",
  "photos": [
    {
      "id": "photo_id_1",
      "url": "https://api.petfinder.com/photos/123.jpg",
      "is_main": true
    }
  ],
  "owner": {
    "id": "user_id",
    "first_name": "Иван",
    "last_name": "Иванов",
    "phone": "+7XXXXXXXXXX"
  },
  "created_at": "2025-03-25T12:00:00",
  "updated_at": "2025-03-25T12:00:00"
}
```

#### Получение списка питомцев пользователя
```
GET /users/me/pets
```
**Ответ:**
```json
{
  "items": [
    {
      "id": "pet_id_1",
      "name": "Барсик",
      "species": "Кошка",
      "breed": "Британская короткошерстная",
      "photo_url": "https://api.petfinder.com/photos/123.jpg",
      "status": "lost",
      "lost_date": "2025-03-25"
    },
    // другие питомцы
  ]
}
```

#### Добавление нового питомца
```
POST /pets
```
**Запрос:**
```json
{
  "name": "Мурзик",
  "species": "Кошка",
  "breed": "Сиамская",
  "color": "Светло-коричневый",
  "age": 2,
  "gender": "male",
  "description": "Сиамский кот с голубыми глазами",
  "microchipped": false
}
```
**Ответ:**
```json
{
  "id": "pet_id_3",
  "name": "Мурзик",
  "species": "Кошка",
  "breed": "Сиамская",
  "color": "Светло-коричневый",
  "age": 2,
  "gender": "male",
  "status": "normal",
  "description": "Сиамский кот с голубыми глазами",
  "microchipped": false,
  "created_at": "2025-04-01T09:54:24"
}
```

#### Загрузка фотографии питомца
```
POST /pets/{pet_id}/photos
```
**Запрос:**
Multipart/form-data с полями:
- `photo`: изображение питомца (обязательное)
- `is_main`: установить как главное фото (boolean, необязательное)
- `description`: описание фотографии (необязательное)

**Ответ:**
```json
{
  "id": "photo_id_2",
  "url": "https://api.petfinder.com/photos/456.jpg",
  "is_main": false,
  "created_at": "2025-04-01T09:54:24",
  "image_processing_status": "completed",
  "detected_attributes": {
    "species": "cat",
    "breed": "siamese",
    "colors": ["light brown", "beige"],
    "confidence": 0.94
  }
}
```

**Примечание:** При загрузке фотографии питомца система компьютерного зрения автоматически анализирует изображение в фоновом режиме, извлекая ключевые визуальные признаки и атрибуты животного. Эти данные будут использованы при поиске совпадений с найденными животными.

#### Обновление статуса питомца (пометить как потерянное)
```
PATCH /pets/{pet_id}/status
```
**Запрос:**
```json
{
  "status": "lost",
  "lost_date": "2025-04-01",
  "lost_location": "Москва, Ленинский проспект, 30",
  "lost_description": "Выбежал из подъезда, когда открывали дверь"
}
```
**Ответ:**
```json
{
  "id": "pet_id_3",
  "name": "Мурзик",
  "status": "lost",
  "lost_date": "2025-04-01",
  "lost_location": "Москва, Ленинский проспект, 30",
  "lost_description": "Выбежал из подъезда, когда открывали дверь",
  "updated_at": "2025-04-01T09:54:24"
}
```

### 3. Система найденных животных и сопоставления

#### Загрузка найденного животного
```
POST /found-pets
```
**Запрос:**
Multipart/form-data с полями:
- `photo`: изображение животного (обязательное)
- `species`: вид животного (необязательно)
- `description`: описание животного и места находки (необязательно)
- `location`: место, где было найдено животное (обязательное)
- `found_date`: дата находки (обязательное)
- `color`: цвет шерсти (необязательно)
- `distinctive_features`: особые приметы (необязательно)
- `approximate_age`: примерный возраст (необязательно)
- `size`: размер животного (маленький, средний, большой) (необязательно)

**Ответ:**
```json
{
  "id": "found_pet_id_1",
  "photo_url": "https://api.petfinder.com/found-photos/789.jpg",
  "species": "Кошка",
  "description": "Серый кот с белой грудкой, найден у магазина",
  "location": "Москва, ул. Тверская, 10",
  "found_date": "2025-04-01",
  "detected_attributes": {
    "species": "cat",
    "breed": "british shorthair",
    "colors": ["grey", "white"],
    "estimated_age": "adult",
    "estimated_size": "medium",
    "confidence": 0.92
  },
  "potential_matches": [
    {
      "pet_id": "pet_id_1",
      "name": "Барсик",
      "similarity": 0.89,
      "photo_url": "https://api.petfinder.com/photos/123.jpg",
      "lost_date": "2025-03-25"
    },
    {
      "pet_id": "pet_id_4",
      "name": "Том",
      "similarity": 0.72,
      "photo_url": "https://api.petfinder.com/photos/567.jpg",
      "lost_date": "2025-03-28"
    }
  ],
  "created_at": "2025-04-01T09:54:24"
}
```

**Примечание:** При загрузке найденного животного система автоматически анализирует изображение с помощью компьютерного зрения, определяет характеристики животного и ищет потенциальные совпадения среди потерянных питомцев. Дополнительная информация, предоставленная пользователем, улучшает точность поиска.

#### Получение подробной информации о совпадении
```
GET /matches/{match_id}
```
**Ответ:**
```json
{
  "id": "match_id_1",
  "similarity": 0.89,
  "created_at": "2025-04-01T09:54:24",
  "lost_pet": {
    "id": "pet_id_1",
    "name": "Барсик",
    "species": "Кошка",
    "breed": "Британская короткошерстная",
    "color": "Серый",
    "photo_url": "https://api.petfinder.com/photos/123.jpg",
    "lost_date": "2025-03-25",
    "lost_location": "Москва, ул. Пушкина, д.10"
  },
  "found_pet": {
    "id": "found_pet_id_1",
    "photo_url": "https://api.petfinder.com/found-photos/789.jpg",
    "location": "Москва, ул. Тверская, 10",
    "found_date": "2025-04-01",
    "finder": {
      "id": "user_id_2",
      "first_name": "Иван",
      "last_name": "Иванов"
    }
  },
  "pet_owner": {
    "id": "user_id",
    "first_name": "Иван",
    "last_name": "Иванов",
    "phone": "+7XXXXXXXXXX",
    "email": "user@example.com"
  }
}
```

### 4. Уведомления

#### Получение списка уведомлений
```
GET /notifications
```
**Параметры запроса:**
- `page` (int, необязательный): Номер страницы (по умолчанию: 1)
- `limit` (int, необязательный): Количество записей на странице (по умолчанию: 20)
- `is_read` (boolean, необязательный): Фильтр по прочитанным/непрочитанным

**Ответ:**
```json
{
  "items": [
    {
      "id": "notification_id_1",
      "type": "match_found",
      "title": "Найдено возможное совпадение",
      "message": "Мы нашли питомца, похожего на вашего Барсика, с вероятностью 89%",
      "data": {
        "match_id": "match_id_1",
        "pet_id": "pet_id_1",
        "similarity": 0.89
      },
      "is_read": false,
      "created_at": "2025-04-01T09:54:24"
    },
    // другие уведомления
  ],
  "total": 5,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

#### Пометить уведомление как прочитанное
```
PATCH /notifications/{notification_id}
```
**Запрос:**
```json
{
  "is_read": true
}
```
**Ответ:**
```json
{
  "id": "notification_id_1",
  "is_read": true,
  "updated_at": "2025-04-01T10:00:00"
}
```

### 5. Профиль пользователя

#### Получение данных профиля
```
GET /users/me
```
**Ответ:**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7XXXXXXXXXX",
  "created_at": "2025-03-15T14:30:00",
  "pets_count": 2
}
```

#### Обновление профиля
```
PATCH /users/me
```
**Запрос:**
```json
{
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7YYYYYYYYYY"
}
```
**Ответ:**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7YYYYYYYYYY",
  "updated_at": "2025-04-01T10:05:00"
}
```

#### Изменение пароля
```
POST /users/me/change-password
```
**Запрос:**
```json
{
  "current_password": "securepassword",
  "new_password": "newsecurepassword"
}
```
**Ответ:**
```json
{
  "message": "Пароль успешно изменен"
}
```

#### Запрос на изменение email
```
POST /users/me/change-email/request
```
**Требуется**: аутентификация токеном

**Запрос:**
```json
{
  "new_email": "newemail@example.com",
  "password": "SecurePass123"
}
```
**Ответ:**
```json
{
  "message": "Verification code sent to new email address"
}
```

#### Подтверждение изменения email
```
POST /users/me/change-email/confirm
```
**Требуется**: аутентификация токеном

**Запрос:**
```json
{
  "verification_code": "ABC123"
}
```
**Ответ:**
```json
{
  "message": "Email address updated successfully"
}
```

## Интеграция с компьютерным зрением (CV)

Бэкенд интегрируется с сервисом компьютерного зрения для обработки и сравнения фотографий животных. Основные компоненты:

### Эндпоинт для сравнения изображений
```
POST /cv/compare-images
```
**Запрос:**
```json
{
  "source_image_id": "img_id_1",
  "target_image_ids": ["img_id_2", "img_id_3", "img_id_4"],
  "filters": {
    "species": "cat",
    "breeds": ["persian", "british shorthair"],
    "colors": ["grey", "white"],
    "age_range": {
      "min": 2,
      "max": 5
    },
    "location_radius_km": 10,
    "lost_date_range": {
      "from": "2025-03-20",
      "to": "2025-04-02"
    }
  },
  "feature_weights": {
    "visual_similarity": 0.6,
    "location_proximity": 0.2,
    "time_proximity": 0.1,
    "attribute_match": 0.1
  }
}
```
**Ответ:**
```json
{
  "comparisons": [
    {
      "target_image_id": "img_id_2",
      "pet_id": "pet_id_1",
      "similarity": {
        "overall": 0.89,
        "visual": 0.92,
        "attribute": 0.85,
        "location": 0.75,
        "time": 0.88
      },
      "matching_features": [
        "facial structure",
        "fur pattern",
        "eye color",
        "body shape"
      ],
      "pet_details": {
        "name": "Барсик",
        "species": "Кошка",
        "breed": "Британская короткошерстная",
        "lost_date": "2025-03-25",
        "lost_location": "Москва, ул. Пушкина, д.10"
      }
    },
    {
      "target_image_id": "img_id_3",
      "pet_id": "pet_id_4",
      "similarity": {
        "overall": 0.72,
        "visual": 0.68,
        "attribute": 0.82,
        "location": 0.90,
        "time": 0.65
      },
      "matching_features": [
        "fur color",
        "ear shape",
        "size"
      ],
      "pet_details": {
        "name": "Том",
        "species": "Кошка",
        "breed": "Сиамская",
        "lost_date": "2025-03-28",
        "lost_location": "Москва, ул. Тверская, д.15"
      }
    }
  ],
  "search_metadata": {
    "total_candidates_considered": 120,
    "filtered_candidates": 15,
    "processing_time_ms": 450,
    "search_radius_expanded": false
  }
}
```


### Переменные окружения
```
# Основные настройки
APP_NAME=PetFinder
DEBUG=False
API_V1_PREFIX=/v1

# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/petfinder

# Безопасность
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Сервис CV
CV_API_URL=http://cv-service:8000/api
CV_API_KEY=your-cv-api-key

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://petfinder-app.com
```

## Заключение

Данная документация описывает основные эндпоинты и функциональность бэкенда для приложения поиска потерянных животных. Бэкенд построен на FastAPI и обеспечивает:
1. Аутентификацию и регистрацию пользователей
2. Управление данными о питомцах
3. Функциональность поиска и сопоставления найденных животных
4. Систему уведомлений
5. Интеграцию с сервисами компьютерного зрения

API организовано в RESTful стиле с использованием стандартных методов HTTP (GET, POST, PATCH, DELETE) и возвращает данные в формате JSON.
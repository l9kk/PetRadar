# Backend Documentation for Lost Pet Finder Application

**Current Documentation Version: 2025-04-04**

# API Overview

This documentation describes the REST API of the backend developed in Python using FastAPI for a mobile application that helps find lost pets using artificial intelligence. The system uses computer vision to recognize animals, determine their characteristics, and find matches between lost and found pets.

**Important Note**: While this documentation is in English, the application primarily serves Russian-speaking users. All user-facing content, notifications, and most user input will be in Russian.

# Backend Architecture

├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── pets.py           # Pet endpoints
│   │   │   ├── matches.py        # Match endpoints
│   │   │   ├── users.py          # User endpoints
│   │   │   ├── found_pets.py     # Found pets endpoints
│   │   │   └── notifications.py  # Notification endpoints
│   │   ├── deps.py               # Endpoint dependencies
│   │   └── routes.py             # Route registration
│   ├── core/
│   │   ├── config.py             # Application configuration
│   │   ├── security.py           # Security and JWT
│   │   ├── exceptions.py         # Exception handling
│   │   └── database.py           # Database connection
│   ├── models/                   # Data models (ORM)
│   │   ├── base.py               # Base model
│   │   ├── pet.py                # Pet model
│   │   ├── user.py               # User model
│   │   ├── match.py              # Match model
│   │   ├── found_pet.py          # Found pet model
│   │   ├── pet_photo.py          # Pet photo model
│   │   └── notification.py       # Notification model
│   ├── repository/               # CRUD operations
│   │   ├── base.py               # Base CRUD operations
│   │   ├── pet.py                # CRUD for pets
│   │   ├── user.py               # CRUD for users
│   │   ├── match.py              # CRUD for matches
│   │   ├── found_pet.py          # CRUD for found pets
│   │   └── notification.py       # CRUD for notifications
│   ├── services/
│   │   ├── pets_service.py       # Business logic for pets
│   │   ├── notification_service.py # Notification service
│   │   └── cv_service.py         # Computer vision service
│   ├── cv/                       # Computer vision module
│   │   ├── pet_finder.py         # Pet search algorithm
│   │   ├── models/               # Pre-trained models
│   │   │   └── README.md         # Model instructions
│   │   └── utils.py              # Helper functions
│   ├── schemas/                  # Pydantic models
│   │   ├── pet.py                # Schemas for pets
│   │   ├── user.py               # Schemas for users
│   │   ├── auth.py               # Schemas for authentication
│   │   ├── match.py              # Schemas for matches
│   │   ├── found_pet.py          # Schemas for found pets
│   │   └── notification.py       # Schemas for notifications
│   ├── localization/             # Localization resources
│   │   ├── ru.json               # Russian language strings
│   │   └── en.json               # English language strings (fallback)
│   └── main.py                   # Application entry point

## Database Structure

### Main Tables:
1. **users** - Application users
   - id: unique user identifier
   - email: user email (unique)
   - password_hash: password hash
   - first_name: first name
   - last_name: last name
   - phone: phone number
   - is_verified: verification status
   - created_at: creation date
   - updated_at: update date

2. **pets** - Pet information
   - id: unique pet identifier
   - owner_id: foreign key (users.id)
   - name: pet name
   - species: animal species
   - breed: breed
   - color: color
   - age: age
   - gender: gender
   - status: status (normal, lost, found)
   - lost_date: date lost
   - lost_location: location where lost
   - lost_description: description of circumstances when lost
   - description: general description
   - microchipped: presence of microchip
   - created_at: creation date
   - updated_at: update date

3. **pet_photos** - Pet photos
   - id: unique photo identifier
   - pet_id: foreign key (pets.id)
   - url: photo URL
   - path: file path
   - is_main: whether it's the main photo
   - description: photo description
   - image_processing_status: image processing status
   - detected_attributes: detected attributes (JSON)
   - feature_vector: feature vector for comparison (binary data)
   - created_at: creation date

4. **found_pets** - Information about found animals
   - id: unique found pet identifier
   - finder_id: foreign key (users.id)
   - species: animal species
   - photo_url: photo URL
   - photo_path: file path
   - description: description
   - location: location where found
   - found_date: date found
   - color: color
   - distinctive_features: distinctive features
   - approximate_age: approximate age
   - size: size
   - feature_vector: feature vector (binary data)
   - detected_attributes: detected attributes (JSON)
   - created_at: creation date
   - updated_at: update date

5. **matches** - Matches between found and lost animals
   - id: unique match identifier
   - lost_pet_id: foreign key (pets.id)
   - found_pet_id: foreign key (found_pets.id)
   - similarity: similarity coefficient
   - status: status (pending, confirmed, rejected)
   - confirmation_date: confirmation date
   - created_at: creation date
   - updated_at: update date

6. **notifications** - User notifications
   - id: unique notification identifier
   - user_id: foreign key (users.id)
   - type: notification type
   - title: title
   - message: message
   - data: additional data (JSON)
   - is_read: read status
   - created_at: creation date
   - updated_at: update date

## API Endpoints

### 1. Authentication and Registration

#### Register a new user
```
POST /auth/register
```
**Required**: no authentication

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7XXXXXXXXXX"
}
```
**Response (200 OK):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7XXXXXXXXXX",
  "is_verified": false,
  "created_at": "2025-04-01T09:54:24"
}
```

**Note**: All names, addresses, and user input fields support Russian characters (UTF-8 encoded). All IDs in the system are UUIDs.

**Errors:**
- 400 Bad Request: Invalid or missing fields
- 409 Conflict: User with this email already exists

#### User login
```
POST /auth/login
```
**Required**: no authentication

**Request:**
```json
{
  "username": "user@example.com",
  "password": "SecurePass123"
}
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- 401 Unauthorized: Invalid login or password
- 403 Forbidden: Account blocked

#### Token refresh
```
POST /auth/refresh
```
**Required**: no authentication

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- 401 Unauthorized: Invalid, expired, or revoked refresh token

#### Logout
```
POST /auth/logout
```
**Required**: token authentication

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
**Response (200 OK):**
```json
{
  "message": "Вы успешно вышли из системы"
}
```

**Errors:**
- 401 Unauthorized: Invalid token or missing authentication

#### Request email verification
```
POST /auth/request-verification-email
```
**Required**: token authentication

**Response (200 OK):**
```json
{
  "message": "На вашу электронную почту отправлен код подтверждения"
}
```

**Errors:**
- 401 Unauthorized: Missing authentication
- 429 Too Many Requests: Exceeded verification request limit

#### Email verification
```
POST /auth/verify-email
```
**Required**: token authentication

**Request:**
```json
{
  "verification_code": "ABC123"
}
```
**Response (200 OK):**
```json
{
  "message": "Электронная почта успешно подтверждена"
}
```

**Errors:**
- 401 Unauthorized: Missing authentication
- 400 Bad Request: Invalid verification code
- 410 Gone: Expired verification code

#### Password recovery request
```
POST /auth/forgot-password
```
**Required**: no authentication

**Request:**
```json
{
  "email": "user@example.com"
}
```
**Response (200 OK):**
```json
{
  "message": "Если ваш адрес электронной почты зарегистрирован, вы получите ссылку для сброса пароля."
}
```

**Note:** Even if the email is not found, 200 OK is returned to prevent information leakage.

#### Password reset
```
POST /auth/reset-password
```
**Required**: no authentication

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass123"
}
```
**Response (200 OK):**
```json
{
  "message": "Пароль успешно сброшен"
}
```

**Errors:**
- 400 Bad Request: Invalid token or weak password
- 410 Gone: Expired reset token

### 2. Pet Management

#### Get list of lost pets
```
GET /pets/lost
```
**Required**: no authentication

**Request parameters:**
- `page` (int, optional): Page number (default: 1)
- `limit` (int, optional): Number of records per page (default: 20)
- `species` (string, optional): Animal species (собака, кошка, etc.)
- `location` (string, optional): Location
- `radius` (float, optional): Search radius in km
- `lost_date_from` (date, optional): Start date lost
- `lost_date_to` (date, optional): End date lost

**Response (200 OK):**
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
    // other pets
  ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

**Note**: The species values accepted are in Russian: "Кошка", "Собака", etc. All location data is expected to be in Russian format (e.g., "Москва, ул. Ленина, 15").

**Errors:**
- 400 Bad Request: Invalid request parameters

#### Get detailed pet information
```
GET /pets/{pet_id}
```
**Required**: no authentication

**Response (200 OK):**
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

**Errors:**
- 404 Not Found: Pet not found

#### Get user's pets list
```
GET /users/me/pets
```
**Required**: token authentication

**Request parameters:**
- `status` (string, optional): Filter by status (normal, lost, found)

**Response (200 OK):**
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
    // other pets
  ]
}
```

**Errors:**
- 401 Unauthorized: Missing authentication

#### Add a new pet
```
POST /pets
```
**Required**: token authentication

**Request:**
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
**Response (201 Created):**
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

**Errors:**
- 401 Unauthorized: Missing authentication
- 400 Bad Request: Invalid data

#### Upload pet photo
```
POST /pets/{pet_id}/photos
```
**Required**: token authentication and pet ownership

**Request:**
Multipart/form-data with fields:
- `photo`: pet image (required)
- `is_main`: set as main photo (boolean, optional)
- `description`: photo description (optional, supports Russian text)

**Response (201 Created):**
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

**Note:** When uploading a pet photo, the computer vision system automatically analyzes the image in the background, extracting key visual features and attributes of the animal. This data will be used when searching for matches with found animals.

**Possible values for `image_processing_status`:**
- `pending`: processing has not started
- `processing`: image is being processed
- `completed`: processing successfully completed
- `failed`: error during image processing

**Errors:**
- 401 Unauthorized: Missing authentication
- 403 Forbidden: Insufficient permissions (not the pet owner)
- 404 Not Found: Pet not found
- 400 Bad Request: Invalid data or image

#### Update pet status (mark as lost)
```
PATCH /pets/{pet_id}/status
```
**Required**: token authentication and pet ownership

**Request:**
```json
{
  "status": "lost",
  "lost_date": "2025-04-01",
  "lost_location": "Москва, Ленинский проспект, 30",
  "lost_description": "Выбежал из подъезда, когда открывали дверь"
}
```
**Response (200 OK):**
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

**Errors:**
- 401 Unauthorized: Missing authentication
- 403 Forbidden: Insufficient permissions (not the pet owner)
- 404 Not Found: Pet not found
- 400 Bad Request: Invalid data

### 3. Found Animals and Matching System

#### Upload found animal
```
POST /found-pets
```
**Required**: token authentication

**Request:**
Multipart/form-data with fields:
- `photo`: animal image (required)
- `species`: animal species (optional, in Russian: "Кошка", "Собака", etc.)
- `description`: description of the animal and where it was found (optional, in Russian)
- `location`: place where the animal was found (required, in Russian)
- `found_date`: date found (required)
- `color`: fur color (optional, in Russian)
- `distinctive_features`: distinctive features (optional, in Russian)
- `approximate_age`: approximate age (optional, in Russian)
- `size`: animal size (small, medium, large) (optional, in Russian: "маленький", "средний", "большой")

**Response (201 Created):**
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

**Note:** When uploading a found animal, the system automatically analyzes the image using computer vision, determines the animal's characteristics, and looks for potential matches among lost pets. Additional information provided by the user improves search accuracy.

**Errors:**
- 401 Unauthorized: Missing authentication
- 400 Bad Request: Invalid data or image
- 422 Unprocessable Entity: Unable to recognize animal in the image

#### Get list of found animals
```
GET /found-pets
```
**Required**: no authentication

**Request parameters:**
- `page` (int, optional): Page number (default: 1)
- `limit` (int, optional): Number of records per page (default: 20)
- `species` (string, optional): Animal species (in Russian)
- `location` (string, optional): Location (in Russian)
- `radius` (float, optional): Search radius in km
- `found_date_from` (date, optional): Start date found
- `found_date_to` (date, optional): End date found

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "found_pet_id_1",
      "photo_url": "https://api.petfinder.com/found-photos/789.jpg",
      "species": "Кошка",
      "location": "Москва, ул. Тверская, 10",
      "found_date": "2025-04-01",
      "finder": {
        "id": "user_id_2",
        "first_name": "Иван",
        "last_name": "Петров"
      },
      "created_at": "2025-04-01T09:54:24"
    },
    // other found animals
  ],
  "total": 45,
  "page": 1,
  "limit": 20,
  "pages": 3
}
```

**Errors:**
- 400 Bad Request: Invalid request parameters

#### Get detailed match information
```
GET /matches/{match_id}
```
**Required**: token authentication and connection to the match (lost pet owner or finder)

**Response (200 OK):**
```json
{
  "id": "match_id_1",
  "similarity": 0.89,
  "created_at": "2025-04-01T09:54:24",
  "status": "pending",
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
      "last_name": "Петров"
    }
  },
  "pet_owner": {
    "id": "user_id",
    "first_name": "Иван",
    "last_name": "Иванов",
    "phone": "+7XXXXXXXXXX",
    "email": "user@example.com"
  },
  "matching_features": [
    "структура морды",
    "узор шерсти",
    "цвет глаз"
  ]
}
```

**Errors:**
- 401 Unauthorized: Missing authentication
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Match not found

#### Confirm match
```
PATCH /matches/{match_id}/status
```
**Required**: token authentication and lost pet owner rights

**Request:**
```json
{
  "status": "confirmed"
}
```
**Response (200 OK):**
```json
{
  "id": "match_id_1",
  "status": "confirmed",
  "confirmation_date": "2025-04-02T14:30:00",
  "updated_at": "2025-04-02T14:30:00"
}
```

**Errors:**
- 401 Unauthorized: Missing authentication
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Match not found
- 400 Bad Request: Invalid status

### 4. Notifications

#### Get notifications list
```
GET /notifications
```
**Required**: token authentication

**Request parameters:**
- `page` (int, optional): Page number (default: 1)
- `limit` (int, optional): Number of records per page (default: 20)
- `is_read` (boolean, optional): Filter by read/unread
- `type` (string, optional): Notification type

**Response (200 OK):**
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
    // other notifications
  ],
  "total": 5,
  "page": 1,
  "limit": 20,
  "pages": 1,
  "unread_count": 3
}
```

**Note**: All notification content (titles and messages) is provided in Russian.

**Errors:**
- 401 Unauthorized: Missing authentication
- 400 Bad Request: Invalid request parameters

#### Mark notification as read
```
PATCH /notifications/{notification_id}
```
**Required**: token authentication and notification ownership

**Request:**
```json
{
  "is_read": true
}
```
**Response (200 OK):**
```json
{
  "id": "notification_id_1",
  "is_read": true,
  "updated_at": "2025-04-01T10:00:00"
}
```

**Errors:**
- 401 Unauthorized: Missing authentication
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Notification not found

#### Mark all notifications as read
```
PATCH /notifications/read-all
```
**Required**: token authentication

**Response (200 OK):**
```json
{
  "message": "Все уведомления отмечены как прочитанные",
  "count": 5
}
```

**Errors:**
- 401 Unauthorized: Missing authentication

### 5. User Profile

#### Get profile data
```
GET /users/me
```
**Required**: token authentication

**Response (200 OK):**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7XXXXXXXXXX",
  "is_verified": true,
  "created_at": "2025-03-15T14:30:00",
  "pets_count": 2,
  "lost_pets_count": 1,
  "found_pets_count": 0
}
```

**Errors:**
- 401 Unauthorized: Missing authentication

#### Update profile
```
PATCH /users/me
```
**Required**: token authentication

**Request:**
```json
{
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "+7YYYYYYYYYY"
}
```
**Response (200 OK):**
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

**Errors:**
- 401 Unauthorized: Missing authentication
- 400 Bad Request: Invalid data

#### Change password
```
POST /users/me/change-password
```
**Required**: token authentication

**Request:**
```json
{
  "current_password": "securepassword",
  "new_password": "newsecurepassword"
}
```
**Response (200 OK):**
```json
{
  "message": "Пароль успешно изменен"
}
```

**Errors:**
- 401 Unauthorized: Missing authentication or incorrect current password
- 400 Bad Request: Invalid new password

#### Request to change email
```
POST /users/me/change-email/request
```
**Required**: token authentication

**Request:**
```json
{
  "new_email": "newemail@example.com",
  "password": "SecurePass123"
}
```
**Response (200 OK):**
```json
{
  "message": "Код подтверждения отправлен на новый адрес электронной почты"
}
```

**Errors:**
- 401 Unauthorized: Missing authentication or incorrect password
- 400 Bad Request: Invalid email
- 409 Conflict: Email already used by another user

#### Confirm email change
```
POST /users/me/change-email/confirm
```
**Required**: token authentication

**Request:**
```json
{
  "verification_code": "ABC123"
}
```
**Response (200 OK):**
```json
{
  "message": "Адрес электронной почты успешно обновлен"
}
```

**Errors:**
- 401 Unauthorized: Missing authentication
- 400 Bad Request: Invalid verification code
- 410 Gone: Expired verification code

## Computer Vision (CV) Integration

The backend integrates with a computer vision module for processing and comparing animal photos. The module uses a combination of neural networks to recognize animals, determine their attributes, and perform image comparison.

### Computer Vision Module Architecture

1. **Animal Detector**: YOLOv5 for detecting and localizing animals in photos
2. **Feature Extractors**: 
   - **Primary**: EfficientNet B3 for extracting high-quality visual features
   - **Secondary**: ResNet50 for determining breed-specific features

3. **Attribute Analyzers**:
   - Breed determination (considering 10 common breeds for dogs and cats)
   - Color determination (11 main fur colors)
   - Age determination (young, adult, senior)
   - Size determination (small, medium, large)

4. **Multi-factor Matching System** that considers:
   - Visual similarity of images (60%)
   - Attribute matching (20%)
   - Geographic proximity of the lost and found locations (10%)
   - Temporal proximity of the lost and found dates (10%)

### Image Comparison Endpoint
```
POST /cv/compare-images
```
**Required**: token authentication

**Request:**
```json
{
  "source_image_id": "img_id_1",
  "target_image_ids": ["img_id_2", "img_id_3", "img_id_4"],
  "filters": {
    "species": "cat",
    "breeds": ["персидская", "британская короткошерстная"],
    "colors": ["серый", "белый"],
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
    "attribute_match": 0.2,
    "location_proximity": 0.1,
    "time_proximity": 0.1
  }
}
```
**Response (200 OK):**
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
        "порода",
        "окрас",
        "размер"
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
        "окрас",
        "возраст"
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

**Note**: While the API parameters use English field names, many of the values (especially breeds, colors, and matching_features) can be provided and are returned in Russian.

### Animal Image Analysis
```
POST /cv/analyze-image
```
**Required**: token authentication

**Request:**
Multipart/form-data with fields:
- `image`: animal image (required)

**Response (200 OK):**
```json
{
  "detected_animals": [
    {
      "species": "cat",
      "confidence": 0.98,
      "bounding_box": [120, 50, 400, 380],
      "attributes": {
        "breed": {
          "name": "Британская короткошерстная",
          "confidence": 0.87
        },
        "colors": [
          {
            "name": "серый",
            "confidence": 0.92
          }
        ],
        "estimated_age": "взрослый",
        "estimated_size": "средний"
      }
    }
  ],
  "processing_time_ms": 230
}
```

**Errors:**
- 401 Unauthorized: Missing authentication
- 400 Bad Request: Invalid image
- 422 Unprocessable Entity: Unable to process image

## Asynchronous Processing and Webhooks

For long-running operations such as image analysis and match finding, asynchronous processing is used:

### Register webhook for receiving results
```
POST /webhooks/register
```
**Required**: token authentication

**Request:**
```json
{
  "event_types": ["match_found", "image_processed"],
  "url": "https://your-app.com/webhook-handler",
  "secret": "your-webhook-secret"
}
```
**Response (201 Created):**
```json
{
  "id": "webhook_id_1",
  "event_types": ["match_found", "image_processed"],
  "url": "https://your-app.com/webhook-handler",
  "created_at": "2025-04-01T11:23:45"
}
```

**Errors:**
- 401 Unauthorized: Missing authentication
- 400 Bad Request: Invalid parameters

### Example webhook notification for found match
```json
{
  "event_type": "match_found",
  "timestamp": "2025-04-01T12:34:56",
  "data": {
    "match_id": "match_id_1",
    "lost_pet_id": "pet_id_1",
    "found_pet_id": "found_pet_id_1",
    "similarity": 0.89
  },
  "signature": "sha256-signature-based-on-secret"
}
```

## Localization

The API supports both Russian and English languages, with Russian being the primary language for most users. While the API endpoint names and structure are in English, the content is predominantly in Russian.

### Language Settings
- Default language for all user-facing content is Russian
- Error messages are provided in Russian for better user experience
- Input values for breeds, colors, locations, and descriptions are expected and stored in Russian
- Display text, notification messages, and descriptions are served in Russian

## Environment Variables
```
# Core settings
APP_NAME=PetFinder
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/petfinder

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
VERIFICATION_CODE_EXPIRE_MINUTES=15

# CV Service
CV_MODEL_PATH=./app/cv/models  # Path to pre-trained models
CV_DETECTION_THRESHOLD=0.5     # Minimum detection threshold
CV_SIMILARITY_THRESHOLD=0.6    # Minimum similarity threshold for matches
CV_MAX_IMAGE_SIZE_MB=10        # Maximum size of uploaded images
CV_PROCESS_TIMEOUT_SECONDS=30  # Image processing timeout

# Comparison component weights (default)
CV_WEIGHT_VISUAL=0.6           # Visual similarity weight
CV_WEIGHT_ATTRIBUTE=0.2        # Attribute match weight
CV_WEIGHT_LOCATION=0.1         # Geographic proximity weight
CV_WEIGHT_TIME=0.1             # Temporal proximity weight

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://petfinder-app.com

# Notifications
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=True

# File storage
STORAGE_PROVIDER=local  # local, s3, azure
UPLOAD_DIR=./uploads
S3_BUCKET_NAME=petfinder-uploads
S3_REGION=us-east-1
```
# Cursed Board API Reference

Base URL: `http://localhost:8000`

## Аутентификация

### POST /api/users
Создание пользователя.

**Request:**
```json
{
  "username": "user1",
  "email": "user@example.com",
  "password": "secretpassword"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "user1",
  "email": "user@example.com"
}
```

### POST /api/users/login
Получение JWT токена.

**Request:**
```json
{
  "username": "user1",
  "password": "secretpassword"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Boards

### GET /api/boards
Список всех досок.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "General",
    "slug": "general",
    "description": "General discussion",
    "thread_count": 42
  }
]
```

### GET /api/boards/{slug}
Получение доски по slug.

### POST /api/boards
Создание доски (требует авторизации).

---

## Threads

### GET /api/boards/{slug}/threads
Список тредов на доске.

**Query params:**
- `limit` (int): Количество (default: 20)
- `offset` (int): Смещение (default: 0)

### GET /api/threads/{id}
Получение треда с постами.

### POST /api/boards/{slug}/threads
Создание треда.

**Request:**
```json
{
  "title": "New Thread",
  "content": "First post content"
}
```

---

## Posts

### GET /api/threads/{id}/posts
Список постов в треде.

### POST /api/threads/{id}/posts
Создание поста.

**Request:**
```json
{
  "content": "Post content"
}
```

### PUT /api/posts/{id}
Редактирование поста (только автор).

### DELETE /api/posts/{id}
Удаление поста (только автор).

---

## WebSocket

### WS /ws/ritual
Real-time подключение для получения аномалий.

**Query params:**
- `fp` (string): Fingerprint пользователя

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/ritual?fp=abc123');
```

**Server → Client Messages:**

```json
// Welcome message
{
  "type": "welcome",
  "user_id": "abc123"
}

// Anomaly event
{
  "type": "anomaly",
  "payload": {
    "id": "uuid",
    "anomaly_type": "whisper",
    "severity": "moderate",
    "target": "user",
    "data": {"message": "..."},
    "duration_ms": 5000,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Client → Server Messages:**

```json
// Heartbeat
{"type": "heartbeat"}

// Ping
{"type": "ping"}

// Activity report
{
  "type": "activity",
  "data": {
    "time_spent": 60,
    "viewed_thread": 123,
    "viewed_post": 456
  }
}
```

---

## Admin API (Ritual Engine)

> ⚠️ Эти endpoints должны быть защищены в production!

### GET /admin/ritual/state/{user_id}
Получить состояние пользователя.

**Response:**
```json
{
  "state": {
    "user_id": "abc123",
    "progress": 45,
    "viewed_threads": [1, 2, 3],
    "viewed_posts": [10, 20, 30],
    "time_on_site": 1800,
    "triggers_hit": ["first_visit", "deep_reader"],
    "known_patterns": {}
  },
  "level": "medium",
  "description": "Что-то здесь не так."
}
```

### POST /admin/ritual/state/{user_id}/reset
Сбросить состояние пользователя.

### POST /admin/ritual/state/{user_id}/progress
Установить прогресс.

**Request:**
```json
{"progress": 75}
```

### POST /admin/ritual/anomaly/{user_id}
Триггернуть аномалию.

**Request:**
```json
{
  "anomaly_type": "whisper",
  "severity": "intense",
  "custom_data": {"message": "Custom message"}
}
```

### GET /admin/ritual/anomaly/types
Список всех типов аномалий.

### GET /admin/ritual/connections
Активные WebSocket подключения.

### POST /admin/ritual/broadcast
Отправить аномалию всем подключённым.

### GET /admin/ritual/stats
Статистика системы.

---

## Health Check

### GET /health
Проверка состояния сервиса.

**Response:** `200 OK`
```json
{
  "status": "healthy"
}
```

---

## Error Responses

Все ошибки возвращаются в формате:

```json
{
  "detail": "Error message"
}
```

| Status | Описание |
|--------|----------|
| 400 | Bad Request - неверные данные |
| 401 | Unauthorized - требуется авторизация |
| 403 | Forbidden - нет доступа |
| 404 | Not Found - ресурс не найден |
| 422 | Validation Error - ошибка валидации |
| 500 | Internal Server Error |

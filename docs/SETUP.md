# Установка и настройка Cursed Board

## Требования

- Python 3.11+
- Redis 7.0+
- MySQL 8.0+
- Node.js 18+ (для frontend, опционально)

## Установка Backend

### 1. Клонирование и виртуальное окружение

```bash
git clone <repo-url>
cd cursed-board/backend

python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
.\venv\Scripts\activate   # Windows
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # для разработки и тестов
```

### 3. Настройка окружения

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Database
DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/cursed_board

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ritual Engine
RITUAL_STATE_TTL=86400
```

### 4. Инициализация базы данных

```bash
# Создайте базу данных в MySQL
mysql -u root -p -e "CREATE DATABASE cursed_board;"

# Применение миграций (если используете Alembic)
alembic upgrade head
```

### 5. Запуск Redis

```bash
# Docker
docker run -d -p 6379:6379 redis:7-alpine

# или локально
redis-server
```

## Запуск

### Development сервер

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API доступен по адресу: http://localhost:8000
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

### Celery Worker (для фоновых задач)

```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

### Celery Beat (для периодических задач)

```bash
cd backend
celery -A app.celery_app beat --loglevel=info
```

## Тестирование

### Запуск всех тестов

```bash
cd backend
pytest
```

### Запуск по категориям

```bash
pytest tests/unit           # Unit тесты
pytest tests/integration    # Integration тесты
pytest -m "not slow"        # Без медленных тестов
```

### С покрытием

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Проверка работоспособности

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "healthy", "redis": "connected", "database": "connected"}
```

### Создание пользователя

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "secret123"}'
```

### WebSocket подключение

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/ritual?fp=test-fingerprint');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Troubleshooting

### Redis не подключается

```bash
# Проверьте, запущен ли Redis
redis-cli ping
# Должен ответить: PONG
```

### Ошибки импорта

```bash
# Убедитесь, что вы в виртуальном окружении
which python
# Должен показать путь к venv
```

### База данных не создаётся

```bash
# Проверьте подключение
mysql -u user -p -e "SHOW DATABASES;"
```

# Cursed Board Backend Setup Guide

This guide will help you set up and run the Cursed Board backend application.

## Requirements

### System Requirements

- **Python**: 3.11 or higher
- **Redis**: 7.0 or higher
- **MySQL**: 8.0 or higher

### Operating Systems

The application is compatible with:
- Linux
- macOS
- Windows (with appropriate Python and database installations)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cursed-board/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

**Production Dependencies:**
```bash
pip install -r requirements.txt
```

**Development Dependencies (for testing):**
```bash
pip install -r requirements-dev.txt
```

#### Main Dependencies

From `requirements.txt`:
- **FastAPI** (>=0.109.0) - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** (>=2.5.0) - Data validation
- **SQLAlchemy** (>=2.0.25) - ORM for database
- **asyncmy** (>=0.2.9) - Async MySQL driver
- **Alembic** (>=1.13.0) - Database migrations
- **python-jose** - JWT token handling
- **passlib** + **bcrypt** - Password hashing
- **Celery** (>=5.3.0) - Background tasks
- **Redis** (>=5.0.0) - Caching and task queue
- **python-dotenv** - Environment variable management

#### Development Dependencies

From `requirements-dev.txt`:
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Code coverage
- **pytest-mock** - Mocking utilities
- **httpx** - HTTP client for testing
- **fakeredis** - Redis mock for tests
- **faker** - Test data generation
- **freezegun** - Time mocking

### 4. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
nano .env  # or use your preferred editor
```

## Environment Variables

Configure the following variables in your `.env` file:

### Application Settings

```env
APP_NAME=Cursed Forum
```
The name of your application.

```env
DEBUG=true
```
Enable debug mode for development. Set to `false` in production.

### Database Configuration (MySQL)

```env
DATABASE_HOST=localhost
```
MySQL server hostname or IP address.

```env
DATABASE_PORT=3306
```
MySQL server port (default: 3306).

```env
DATABASE_USER=cursed
```
MySQL username for the application.

```env
DATABASE_PASSWORD=your_password_here
```
MySQL password. **Change this to a secure password.**

```env
DATABASE_NAME=cursed_board
```
Name of the MySQL database.

### Authentication Settings

```env
SECRET_KEY=your-super-secret-key-change-in-production
```
Secret key for JWT token signing. **Must be changed in production.** Generate a secure random string.

```env
ALGORITHM=HS256
```
JWT signing algorithm (default: HS256).

```env
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```
JWT token expiration time in minutes (default: 1440 = 24 hours).

### Redis Configuration

```env
REDIS_HOST=localhost
```
Redis server hostname or IP address.

```env
REDIS_PORT=6379
```
Redis server port (default: 6379).

### Optional Settings

The following settings are available but have defaults:
- `REDIS_DB` - Redis database number (default: 0)
- `RITUAL_STATE_TTL` - Time-to-live for ritual state in seconds (default: 86400 = 24 hours)
- `RITUAL_COOKIE_NAME` - Cookie name for ritual tracking (default: "ritual_id")
- `RITUAL_FINGERPRINT_HEADER` - Header name for fingerprint (default: "X-Fingerprint")
- `CELERY_BROKER_DB` - Redis DB for Celery broker (default: 1)
- `CELERY_RESULT_DB` - Redis DB for Celery results (default: 2)

## Database Setup

### 1. Create MySQL Database

Log into MySQL:

```bash
mysql -u root -p
```

Create the database and user:

```sql
CREATE DATABASE cursed_board CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cursed'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON cursed_board.* TO 'cursed'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Replace `your_password_here` with the password you set in `.env`.

### 2. Database Tables

Tables will be created automatically by SQLAlchemy when you start the application. The application uses SQLAlchemy's `Base.metadata.create_all()` during startup.

**Note:** For production environments, consider using Alembic migrations for better control over schema changes.

### Database Models

The following tables will be created:
- `users` - User accounts
- `boards` - Forum boards
- `threads` - Discussion threads
- `posts` - User posts
- `media` - Media attachments (if applicable)

## Redis Setup

### Using Docker (Recommended for Development)

```bash
docker run -d \
  --name cursed-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### Local Installation

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS (using Homebrew):**
```bash
brew install redis
brew services start redis
```

**Windows:**
Download and install Redis from the official Windows port or use Docker.

### Verify Redis Connection

```bash
redis-cli ping
```

Expected response: `PONG`

## Running the Application

### Development Server

Start the FastAPI development server with auto-reload:

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at:
- **API Base**: http://localhost:8000/api
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Production Server

For production, use a production-grade ASGI server configuration:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use Gunicorn with Uvicorn workers:

```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Celery Worker (Background Tasks)

Start the Celery worker:

```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

### Celery Beat (Scheduled Tasks)

Start the Celery beat scheduler:

```bash
cd backend
celery -A app.celery_app beat --loglevel=info
```

**Note:** Celery is configured in the codebase but may not have active tasks yet. The infrastructure is ready for background task implementation.

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=app --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run Specific Test Types

**Unit Tests Only:**
```bash
pytest tests/unit
```

**Integration Tests Only:**
```bash
pytest tests/integration
```

**Marked Tests:**
```bash
pytest -m unit        # Run tests marked as unit
pytest -m integration # Run tests marked as integration
pytest -m slow        # Run slow tests
```

### Test Configuration

Test settings are defined in `pytest.ini`:
- Test discovery patterns: `test_*.py`
- Async mode: auto
- Markers: `unit`, `integration`, `slow`
- Verbose output with short traceback

## Health Check

Verify the application is running correctly:

```bash
curl http://localhost:8000/health
```

**Expected Response (healthy):**
```json
{
  "status": "healthy",
  "redis": "connected"
}
```

**Expected Response (degraded - Redis disconnected):**
```json
{
  "status": "degraded",
  "redis": "disconnected"
}
```

## Project Structure

```
backend/
├── app/
│   ├── core/           # Core configuration (database, auth, settings)
│   ├── models/         # SQLAlchemy models
│   ├── repositories/   # Data access layer
│   ├── routers/        # API endpoints
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic (Ritual Engine, etc.)
│   └── middleware/     # Custom middleware
├── tests/
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── main.py            # Application entry point
├── requirements.txt   # Production dependencies
├── requirements-dev.txt # Development dependencies
├── pytest.ini        # Pytest configuration
└── .env.example      # Environment variables template
```

## Troubleshooting

### Database Connection Issues

**Error:** `Can't connect to MySQL server`

**Solution:**
- Verify MySQL is running: `sudo systemctl status mysql`
- Check database credentials in `.env`
- Ensure the database exists: `mysql -u cursed -p -e "SHOW DATABASES;"`
- Check firewall settings if MySQL is on a remote host

### Redis Connection Issues

**Error:** `Error connecting to Redis`

**Solution:**
- Verify Redis is running: `redis-cli ping`
- Check Redis host and port in `.env`
- For Docker: `docker ps` to verify container is running
- Check Redis logs: `docker logs cursed-redis` or `sudo journalctl -u redis`

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
- Ensure you're in the `backend/` directory
- Activate the virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
- Check what's using port 8000: `lsof -i :8000` (Linux/macOS)
- Kill the process or use a different port: `uvicorn main:app --port 8001 --reload`

### Table Not Found Errors

**Error:** `Table 'cursed_board.users' doesn't exist`

**Solution:**
- Tables should be created automatically on startup
- Restart the application to trigger table creation
- Check database logs for permission issues
- Manually verify: `mysql -u cursed -p cursed_board -e "SHOW TABLES;"`

### JWT Token Issues

**Error:** `Could not validate credentials`

**Solution:**
- Ensure `SECRET_KEY` in `.env` hasn't changed (tokens become invalid if it changes)
- Check token expiration time
- Verify `Authorization: Bearer <token>` header format
- Generate a new token by creating a new session

### Permission Denied Errors

**Error:** `Permission denied` when starting services

**Solution:**
- On Linux: Don't run as root unless necessary
- Check file permissions: `ls -la`
- Ensure virtual environment is activated
- For Redis/MySQL: Check service user permissions

### Celery Not Starting

**Error:** Celery worker fails to start

**Solution:**
- Verify Redis is accessible (Celery uses Redis as broker)
- Check `CELERY_BROKER_URL` configuration in settings
- Ensure you're running from the `backend/` directory
- Check for Python import errors in task modules

## Development Tips

### Auto-Reload

The `--reload` flag watches for file changes and automatically restarts the server. Only use in development.

### API Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Database Inspection

Use a MySQL client to inspect the database:
```bash
mysql -u cursed -p cursed_board
```

Useful commands:
```sql
SHOW TABLES;
DESCRIBE users;
SELECT * FROM users LIMIT 5;
```

### Redis Inspection

Use Redis CLI to inspect stored data:
```bash
redis-cli
```

Useful commands:
```
KEYS *                    # List all keys
GET ritual:state:{user_id}  # Get user state
LRANGE ritual:queue:{user_id} 0 -1  # Get user's anomaly queue
```

### Logging

Set `DEBUG=true` in `.env` to enable detailed logging. Logs will show:
- Database queries
- Redis operations
- WebSocket connections
- Request/response details

## Next Steps

After setup:
1. Create a test user via `POST /api/users`
2. Create boards, threads, and posts via the API
3. Connect to WebSocket endpoint to test Ritual Engine
4. Use admin endpoints to trigger anomalies
5. Explore the interactive API docs at `/docs`

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Redis Documentation**: https://redis.io/docs/
- **Celery Documentation**: https://docs.celeryproject.org/

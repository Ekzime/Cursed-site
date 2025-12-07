# Cursed Board

Проклятый форум, где контент живёт своей жизнью.

## Особенности

- **Живые посты** — контент появляется и изменяется сам по себе
- **Система прогресса** — форум "узнаёт" пользователя со временем
- **Аномалии в реальном времени** — визуальные эффекты через WebSocket
- **Порча текста** — контент искажается по мере погружения

## Быстрый старт

```bash
# Клонирование
git clone <repo-url>
cd cursed-board

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # для тестов

# Настройка
cp .env.example .env
# Отредактируйте .env

# Запуск
uvicorn main:app --reload
```

## Документация

- [Установка и настройка](docs/SETUP.md)
- [API Reference](docs/API.md)
- [Ritual Engine](docs/RITUAL_ENGINE.md)
- [Архитектура](docs/architecture-v1.md)

## Тестирование

```bash
cd backend
pytest                     # все тесты
pytest tests/unit          # только unit
pytest tests/integration   # только integration
pytest --cov=app           # с покрытием
```

## Стек технологий

- **Backend:** FastAPI, SQLAlchemy, Celery
- **Database:** MySQL
- **Cache/Queue:** Redis
- **Real-time:** WebSocket

## Лицензия

MIT

# Архитектура v1 — Гибридная система

## Обзор

Гибридный подход: REST API для основного контента + WebSocket для "инъекций" аномалий в реальном времени.

Пользователь видит обычный форум, но контент начинает "жить своей жизнью" без явных действий со стороны пользователя.

## Стек технологий

- **Backend**: FastAPI + Celery + Redis
- **Database**: MySQL
- **Frontend**: React + Vite
- **Realtime**: WebSocket (встроенный в FastAPI)

## Общая схема

```
┌────────────────────────────────────────────────────────────────┐
│                         CLIENT                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Forum UI    │  │  WS Client   │  │  Anomaly Renderer    │  │
│  │  (React)     │  │  (скрытый)   │  │  (DOM манипуляции)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
         │                   │
         │ HTTP              │ WebSocket
         ▼                   ▼
┌────────────────────────────────────────────────────────────────┐
│                         SERVER                                  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  REST API    │  │  WS Handler  │  │  Ritual Engine       │  │
│  │  /threads    │  │  /ws/ritual  │  │                      │  │
│  │  /posts      │  │              │  │  - state tracker     │  │
│  │  /users      │  │              │  │  - anomaly generator │  │
│  └──────────────┘  └──────────────┘  │  - trigger system    │  │
│         │                   │        └──────────────────────┘  │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────────────────────────────────────────────────────┐
│  │                      Redis                                   │
│  │  ritual_state:{user_id} → RitualState                       │
│  │  anomaly_queue:{user_id} → list[Anomaly]                    │
│  └─────────────────────────────────────────────────────────────┘
│                            │                                    │
│  ┌─────────────────────────────────────────────────────────────┐
│  │                      Celery                                  │
│  │  - отложенные аномалии                                      │
│  │  - фоновая генерация контента                               │
│  │  - scheduled события                                        │
│  └─────────────────────────────────────────────────────────────┘
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐
│  │                    Database                                  │
│  │  threads, posts, users, media (базовый контент)             │
│  └─────────────────────────────────────────────────────────────┘
└────────────────────────────────────────────────────────────────┘
```

## Компоненты

### 1. REST API

Стандартный API форума:

```
GET  /api/boards              # список досок
GET  /api/boards/{id}/threads # треды на доске
GET  /api/threads/{id}        # тред с постами
GET  /api/users/{id}          # профиль юзера
POST /api/threads/{id}/posts  # новый пост (если разрешено)
```

Каждый запрос проходит через `RitualMiddleware`, который:
- Идентифицирует пользователя
- Обновляет `RitualState`
- Может модифицировать ответ (добавить аномальный пост, изменить дату)

### 2. WebSocket Handler

```
WS /ws/ritual
```

Подключается автоматически при загрузке страницы. Клиент не знает что соединение существует (скрытый UI).

**Входящие сообщения от сервера:**
```json
{
  "type": "new_post",
  "target": "thread_42",
  "data": { ... },
  "delay": 0,
  "persist": false
}
```

**Типы событий:**
- `new_post` — новый пост появился
- `post_edit` — текст изменился
- `post_corrupt` — текст "портится" (глитч-символы)
- `post_delete` — пост исчез
- `glitch` — визуальный эффект
- `flicker` — мерцание
- `notification` — фейковое уведомление
- `presence` — "X печатает..."
- `whisper` — текст появляется и исчезает

### 3. Ritual State

Хранится в Redis с TTL (например, 24 часа).

```python
@dataclass
class RitualState:
    user_id: str              # fingerprint / cookie
    progress: int             # 0-100, "глубина" проклятия

    # История
    viewed_threads: list[int]
    viewed_posts: list[int]
    time_on_site: int         # секунды
    first_visit: datetime
    last_activity: datetime

    # Триггеры
    triggers_hit: set[str]    # разблокированные события

    # Персонализация
    known_patterns: dict      # что "форум узнал" о пользователе
```

### 4. Ritual Engine

Центральная логика "проклятия":

```python
class RitualEngine:
    async def on_request(self, state: RitualState, request: Request) -> None:
        """Вызывается на каждый HTTP запрос"""
        state.progress += self.calculate_progress(request)
        self.check_triggers(state, request)

        if self.should_spawn_anomaly(state):
            anomaly = self.generate_anomaly(state)
            await self.queue_anomaly(state.user_id, anomaly)

    async def ws_loop(self, state: RitualState, ws: WebSocket) -> None:
        """Фоновый цикл для подключенного клиента"""
        while True:
            # Проверяем очередь аномалий
            anomaly = await self.pop_anomaly(state.user_id)
            if anomaly:
                await ws.send_json(anomaly.to_payload())

            # Случайные события
            if self.random_event_chance(state):
                event = self.generate_random_event(state)
                await ws.send_json(event)

            await asyncio.sleep(random.uniform(5, 30))
```

### 5. Trigger System

Триггеры разблокируют контент и аномалии:

```python
TRIGGERS = {
    "first_visit": lambda s: s.progress == 0,
    "deep_reader": lambda s: len(s.viewed_posts) > 20,
    "night_owl": lambda s: current_hour() in range(0, 5),
    "found_hidden": lambda s: "hidden_board" in s.viewed_threads,
    "the_pattern": lambda s: check_post_sequence(s.viewed_posts),
    "too_long": lambda s: s.time_on_site > 3600,
    "returnee": lambda s: (now() - s.first_visit).days > 7,
}

TRIGGER_EFFECTS = {
    "deep_reader": [
        UnlockAnomaly("posts_know_you"),
        IncreaseAnomalyChance(1.5),
    ],
    "night_owl": [
        UnlockBoard("nightmare"),
        UnlockAnomaly("shadow_posts"),
    ],
    "the_pattern": [
        UnlockEnding("truth"),
    ],
}
```

### 6. Celery Tasks

Фоновые задачи:

```python
@celery.task
def schedule_anomaly(user_id: str, anomaly_type: str, delay: int):
    """Отложенная аномалия"""
    # Выполнится через delay секунд
    pass

@celery.task
def generate_procedural_content():
    """Генерация нового контента по расписанию"""
    pass

@celery.task
def cleanup_stale_sessions():
    """Очистка старых сессий"""
    pass
```

## База данных

### Основные таблицы

```sql
-- Доски
CREATE TABLE boards (
    id INTEGER PRIMARY KEY,
    slug TEXT UNIQUE,        -- "general", "random", "hidden"
    name TEXT,
    description TEXT,
    is_hidden BOOLEAN,       -- скрытые доски
    unlock_trigger TEXT      -- какой триггер открывает
);

-- Треды
CREATE TABLE threads (
    id INTEGER PRIMARY KEY,
    board_id INTEGER REFERENCES boards(id),
    title TEXT,
    created_at TIMESTAMP,
    is_sticky BOOLEAN,
    is_locked BOOLEAN,
    anomaly_level INTEGER    -- 0-10, насколько "проклят" тред
);

-- Посты
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    thread_id INTEGER REFERENCES threads(id),
    user_id INTEGER REFERENCES users(id),
    content TEXT,
    created_at TIMESTAMP,
    is_anomaly BOOLEAN,      -- сгенерированный аномальный пост
    anomaly_type TEXT        -- тип аномалии если есть
);

-- Юзеры (NPC форума)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    registered_at TIMESTAMP, -- может быть аномальной датой
    avatar_url TEXT,
    is_anomaly BOOLEAN,
    anomaly_data JSON        -- доп. данные для аномальных юзеров
);

-- Медиа
CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    type TEXT,               -- "image", "video", "file"
    url TEXT,
    corruption_level INTEGER -- 0-10, насколько "испорчен" файл
);
```

## Frontend (React)

### Структура

```
src/
├── components/
│   ├── Board/
│   ├── Thread/
│   ├── Post/
│   └── Anomaly/           # рендеринг аномалий
├── hooks/
│   ├── useRitualSocket.ts # скрытый WS
│   └── useAnomalyQueue.ts
├── services/
│   ├── api.ts             # REST клиент
│   └── ritual.ts          # обработка аномалий
└── store/
    └── ritual.ts          # локальное состояние
```

### Скрытый WebSocket

```typescript
// Подключается автоматически, UI не показывает
const useRitualSocket = () => {
  useEffect(() => {
    const ws = new WebSocket('/ws/ritual');

    ws.onmessage = (event) => {
      const anomaly = JSON.parse(event.data);
      applyAnomaly(anomaly);
    };

    // Нет индикатора подключения в UI
    return () => ws.close();
  }, []);
};
```

### Применение аномалий

```typescript
const applyAnomaly = (anomaly: Anomaly) => {
  switch (anomaly.type) {
    case 'new_post':
      // Добавить пост в DOM без перезагрузки
      injectPost(anomaly.target, anomaly.data);
      break;
    case 'post_edit':
      // Плавно изменить текст
      morphText(anomaly.target, anomaly.data.newContent);
      break;
    case 'glitch':
      // Визуальный эффект
      applyGlitchEffect(anomaly.target, anomaly.data.duration);
      break;
    // ...
  }
};
```

## Поток данных

```
1. Пользователь открывает страницу
   ↓
2. React загружает контент через REST API
   ↓
3. RitualMiddleware обновляет RitualState в Redis
   ↓
4. Скрытый WebSocket подключается
   ↓
5. RitualEngine решает когда отправить аномалию
   ↓
6. Celery может отложить аномалию на потом
   ↓
7. Аномалия приходит через WS
   ↓
8. AnomalyRenderer модифицирует DOM
   ↓
9. Пользователь видит "живой" форум
```

## Идентификация пользователя

Комбинация методов:

1. **Cookie** `ritual_id` — основной идентификатор
2. **Fingerprint** — fallback если куки очищены
3. **Поведенческие паттерны** — скорость скролла, клики, время между действиями

Цель: пользователь не может легко "сбросить" прогресс ритуала.

## Масштабирование аномалий

Прогресс 0-100 влияет на:

| Progress | Частота аномалий | Типы аномалий |
|----------|------------------|---------------|
| 0-20     | Редко (1/час)    | Мелкие глитчи, странные даты |
| 21-50    | Иногда (1/15мин) | Новые посты, изменения текста |
| 51-80    | Часто (1/5мин)   | Персонализированные, "форум знает тебя" |
| 81-100   | Постоянно        | Полный хаос, концовки |

---

*Версия 1.0 — Декабрь 2024*

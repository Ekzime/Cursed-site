# Cursed Board - System Architecture

## Overview

Cursed Board is an experimental forum application where the interface responds to user behavior through subtle anomalies and content mutations. The backend implements a "Ritual Engine" that tracks user state across sessions and orchestrates paranormal-themed events based on user interactions.

### Core Concept

The application presents as a normal imageboard/forum but introduces progressively stranger anomalies as users interact with it:

- Posts that change when re-read
- UI elements that glitch or distort
- Hidden boards that unlock based on user behavior
- Content that appears personalized to watching patterns
- Real-time anomalies delivered via WebSocket

## Tech Stack

### Core Framework
- **FastAPI** - Async web framework for REST API and WebSocket endpoints
- **Python 3.11+** - Modern async/await support

### Database Layer
- **SQLAlchemy 2.0** - ORM with async support
- **MySQL 8.0+** - Primary data store via `asyncmy` driver
- **Alembic** - Database migrations (planned)

### Caching & State
- **Redis** - User ritual state persistence and WebSocket connection tracking
- **redis-py 5.0+** - Async Redis client

### Task Processing
- **Celery** - Background task queue (planned for scheduled anomalies)
- **Redis** - Celery broker and result backend

### Authentication
- **JWT** - Token-based authentication
- **Passlib + bcrypt** - Password hashing

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│                    (Browser/Frontend App)                        │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ HTTP/REST                          │ WebSocket
             │                                    │
┌────────────▼────────────────────────────────────▼───────────────┐
│                        FastAPI Application                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Middleware Stack (LIFO order)               │  │
│  │  1. CORS Middleware                                      │  │
│  │  2. RitualMiddleware                                     │  │
│  │     - Extracts user_id (fingerprint/cookie/UUID)        │  │
│  │     - Loads/Creates RitualState from Redis              │  │
│  │     - Attaches state to request.state                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routers                           │  │
│  │  - /api/users      - User registration, auth            │  │
│  │  - /api/boards     - Board listing, creation            │  │
│  │  - /api/threads    - Thread CRUD                        │  │
│  │  - /api/posts      - Post CRUD                          │  │
│  │  - /ws/ritual      - WebSocket anomaly stream           │  │
│  │  - /admin/ritual   - Ritual state management            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Ritual Engine Core                      │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  RitualEngine (Orchestrator)                       │ │  │
│  │  │  - Coordinates all ritual components               │ │  │
│  │  │  - Entry point: on_request(), on_thread_view()     │ │  │
│  │  └───────────┬────────────────────────────────────────┘ │  │
│  │              │                                           │  │
│  │  ┌───────────▼────────────────────────────────────────┐ │  │
│  │  │  Sub-Services                                      │ │  │
│  │  │  - RitualStateManager: Redis CRUD for user state  │ │  │
│  │  │  - TriggerChecker: Behavior-based event triggers  │ │  │
│  │  │  - ProgressEngine: Curse progression calculation  │ │  │
│  │  │  - AnomalyGenerator: Random anomaly creation      │ │  │
│  │  │  - AnomalyQueue: Redis queue for WebSocket events │ │  │
│  │  │  - ContentMutator: Text corruption/glitching      │ │  │
│  │  │  - ConnectionManager: Active WS connection state  │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬───────────────────────────────────┬────────────────┘
             │                                   │
             │                                   │
┌────────────▼──────────────┐      ┌────────────▼──────────────┐
│     MySQL Database        │      │      Redis Cache          │
│                           │      │                           │
│  - users                  │      │  - ritual_state:{user_id} │
│  - boards                 │      │  - anomaly_q:{user_id}    │
│  - threads                │      │  - ws_conn:{user_id}      │
│  - posts                  │      │  - Celery queues (future) │
│  - media                  │      │                           │
└───────────────────────────┘      └───────────────────────────┘
```

## Request Flow

### Standard HTTP Request Flow

```
1. Client Request
   └→ CORS Middleware (add headers)
      └→ RitualMiddleware
         ├─ Extract user_id from X-Fingerprint header / ritual_id cookie / new UUID
         ├─ Load RitualState from Redis (or create new)
         ├─ Attach to request.state.ritual_state
         └→ Route Handler
            ├─ Access RitualState via Depends(get_ritual_state)
            ├─ Call RitualEngine.on_request() to check triggers
            ├─ Query database for content
            ├─ Apply content mutations via ContentMutator
            └→ Response
               └─ Set ritual_id cookie (if new user)
```

### WebSocket Connection Flow

```
1. Client connects to /ws/ritual?fp={fingerprint}
   ├─ Extract user_id from query param or cookie
   ├─ Register connection in ConnectionManager (Redis)
   ├─ Send welcome message
   └─ Start two async tasks:
      ├─ Queue Listener (pop events from Redis, send to client)
      └─ Receive Listener (handle ping, heartbeat, activity reports)

2. Ritual Engine generates anomaly
   ├─ Push AnomalyEvent to AnomalyQueue (Redis list)
   └─ Queue Listener pops and sends to WebSocket

3. Client disconnects
   └─ Cleanup: Remove from ConnectionManager
```

### Ritual State Lifecycle

```
1. First Visit
   ├─ RitualMiddleware generates UUID or receives fingerprint
   ├─ RitualStateManager.create() creates new state
   │  └─ Defaults: progress=0, triggers_hit=[], viewed_threads=[], etc.
   └─ Saved to Redis with 24h TTL

2. Subsequent Requests
   ├─ RitualStateManager.get() loads from Redis
   ├─ TriggerChecker evaluates behavior patterns
   ├─ ProgressEngine calculates curse progression
   ├─ State updated and saved back to Redis
   └─ TTL refreshed on each save

3. State Expiry
   └─ After 24h of inactivity, Redis key expires (user forgotten)
```

## Data Flow

### REST + WebSocket Hybrid

Cursed Board uses a hybrid approach:

**REST API (HTTP):**
- User registration, login
- Board/thread/post CRUD operations
- Retrieve content with mutations applied inline

**WebSocket (/ws/ritual):**
- Real-time anomaly delivery
- UI glitches, notifications, sounds
- Does NOT deliver primary content (posts/threads)

**Why Hybrid?**
- REST ensures content is cacheable and SEO-friendly
- WebSocket enables real-time paranormal effects without polling
- Ritual state persists in Redis, accessible to both protocols

### Content Mutation Pipeline

```
Database → Raw Content
             ↓
   ContentMutator.mutate_post()
     ├─ Check RitualState.progress level
     ├─ Apply character substitutions (zalgo, glitch)
     ├─ Inject random typos/errors
     └─ Personalize based on known_patterns
             ↓
    Mutated Response → Client
```

## Configuration

### Environment Variables

Required variables (set in `.env`):

```bash
# Application
APP_NAME=Cursed Forum
DEBUG=false

# Database
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=cursed_user
DATABASE_PASSWORD=secure_password
DATABASE_NAME=cursed_board

# Authentication
SECRET_KEY=your-secret-key-here  # Used for JWT signing
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Ritual Engine
RITUAL_STATE_TTL=86400              # 24 hours
RITUAL_COOKIE_NAME=ritual_id
RITUAL_FINGERPRINT_HEADER=X-Fingerprint

# Celery (future use)
CELERY_BROKER_DB=1
CELERY_RESULT_DB=2
```

### Database URL Construction

The `Settings` class automatically constructs connection URLs:

```python
DATABASE_URL = mysql+asyncmy://{user}:{password}@{host}:{port}/{database}
REDIS_URL = redis://{host}:{port}/{db}
```

### Middleware Configuration

```python
# Order matters: last added = first executed
app.add_middleware(RitualMiddleware, ttl=settings.RITUAL_STATE_TTL)
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

## Application Lifecycle

### Startup Sequence

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Initialize Redis
    redis_client = await init_redis()
    app.state.redis = redis_client  # Shared with middleware

    yield  # Application runs

    # Shutdown
    await engine.dispose()
    await close_redis()
```

### Health Check

```
GET /health
{
  "status": "healthy" | "degraded",
  "redis": "connected" | "disconnected"
}
```

## Security Considerations

### User Identification

Cursed Board uses anonymous fingerprinting instead of forced registration:

1. **X-Fingerprint header** - Browser fingerprint from frontend (FingerprintJS, etc.)
2. **ritual_id cookie** - Fallback UUID for persistence
3. **New UUID** - Generated for first-time visitors

This allows tracking curse progression without authentication barriers.

### Authentication (Optional)

Registered users receive JWT tokens:

```
POST /api/users/login
→ Returns access_token (expires in 24h)

Subsequent requests:
Authorization: Bearer {token}
```

### CORS

Currently set to `allow_origins=["*"]` for development. In production:

```python
allow_origins=["https://cursedboard.example.com"]
```

## Performance Characteristics

### Redis as Session Store

- **Why Redis?** Ephemeral state, fast reads/writes, built-in TTL
- **TTL Strategy:** 24h expiry, refreshed on activity
- **Data Size:** ~1-5KB per user (JSON serialized RitualState)

### WebSocket Scaling

- **Connection Tracking:** Redis Set (`ws_conn:{user_id}`)
- **Anomaly Queue:** Redis List (`anomaly_q:{user_id}`)
- **Limitations:** Current implementation is single-server
- **Future:** Use Redis Pub/Sub for multi-server WebSocket

### Database Queries

- **Pagination:** All list endpoints should paginate (limit/offset)
- **Indexing:** Foreign keys and user_id/board_id fields indexed
- **N+1 Queries:** Use `selectinload()` for relationships

## Future Enhancements

### Celery Integration

Planned background tasks:

- Scheduled anomalies (trigger at specific times)
- NPC user post generation
- Board unlock events
- Data cleanup jobs

### Multi-Server WebSocket

Use Redis Pub/Sub to broadcast anomalies across app instances:

```python
# Publisher (any app instance)
await redis.publish(f"ritual:{user_id}", event_json)

# Subscriber (WebSocket server)
pubsub = redis.pubsub()
await pubsub.subscribe(f"ritual:{user_id}")
async for message in pubsub.listen():
    await websocket.send_json(message)
```

### Metrics & Monitoring

- Track trigger activation rates
- Monitor curse progression distribution
- Log anomaly delivery success rates
- Redis memory usage alerts

# Ritual Engine Documentation

## Overview

The Ritual Engine is the core orchestrator of the "curse" system in Cursed Board. It creates a progressively unsettling experience by tracking user behavior, generating anomalies, and mutating content based on a user's interaction level.

The engine coordinates multiple components to deliver a personalized horror experience that intensifies as users explore the board. It tracks progress through distinct levels, triggers anomalies at appropriate times, corrupts content, and maintains persistent state across sessions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Ritual Engine                              │
│                    (Main Orchestrator)                              │
└──────────────┬──────────────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│   State      │  │   Trigger    │
│  Manager     │  │   Checker    │
│              │  │              │
│ - Redis      │  │ - Behavior   │
│   Storage    │  │   Detection  │
│ - User State │  │ - Effects    │
└──────────────┘  └──────────────┘
       │                │
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│  Progress    │  │   Anomaly    │
│   Engine     │  │  Generator   │
│              │  │              │
│ - Levels     │  │ - Types      │
│ - Thresholds │  │ - Weights    │
│ - Rewards    │  │ - Severity   │
└──────────────┘  └──────────────┘
       │                │
       │                ▼
       │         ┌──────────────┐
       │         │   Anomaly    │
       │         │    Queue     │
       │         │              │
       │         │ - Redis FIFO │
       │         │ - WebSocket  │
       │         └──────────────┘
       │
       ▼
┌──────────────┐
│   Content    │
│   Mutator    │
│              │
│ - Corruption │
│ - Glitching  │
│ - Mutations  │
└──────────────┘
```

## Components

### RitualEngine
Main orchestrator that coordinates all subsystems.

**Key Methods:**
- `on_request(user_id, path, method)` - Process each incoming request
- `on_thread_view(user_id, thread_id)` - Handle thread viewing
- `on_post_view(user_id, post_id)` - Handle post viewing
- `mutate_post(post_data, state)` - Apply content mutations
- `queue_anomaly(user_id, event)` - Queue anomaly for delivery

### RitualStateManager
Manages user state persistence in Redis.

**Storage Format:**
- Key: `ritual_state:{user_id}`
- TTL: 24 hours (default)
- Format: JSON-encoded RitualState

**State Fields:**
- `user_id` - Unique user identifier
- `progress` - Progress value (0-100)
- `first_visit` - Timestamp of first visit
- `last_activity` - Timestamp of last activity
- `time_on_site` - Total seconds on site
- `viewed_threads` - List of viewed thread IDs (max 100)
- `viewed_posts` - List of viewed post IDs (max 500)
- `triggers_hit` - Set of activated trigger names
- `known_patterns` - Dict of personalization data

### ProgressEngine
Calculates and manages user progress through four distinct levels.

### TriggerChecker
Detects user behavior patterns and activates triggers that modify progress and anomaly generation.

### AnomalyGenerator
Creates random anomalies appropriate for the user's progress level.

### AnomalyQueue
Redis-backed FIFO queue for delivering anomalies to WebSocket connections.

**Queue Format:**
- Key: `anomaly_queue:{user_id}`
- TTL: 1 hour
- Max Size: 100 events

### ContentMutator
Corrupts and transforms text content based on user progress.

## Progress System

The progress system defines four levels that determine anomaly frequency, corruption chance, and overall experience intensity.

### Progress Levels

| Level | Range | Description | Anomaly Chance | Corruption Chance |
|-------|-------|-------------|----------------|-------------------|
| **LOW** | 0-20% | Rare anomalies, minimal corruption | 2% per request | 0% |
| **MEDIUM** | 21-50% | Occasional anomalies and corruption | 8% per request | 5% |
| **HIGH** | 51-80% | Frequent anomalies, noticeable corruption | 20% per request | 15% |
| **CRITICAL** | 81-100% | Constant anomalies, heavy corruption | 40% per request | 35% |

### Progress Sources

Progress is earned through various user actions:

**Thread Viewing:**
- First view: +1 progress
- Revisits: 0 progress

**Post Viewing:**
- First view: +1 progress (0.5 rounded up)
- Revisits: 0 progress

**Time on Site:**
- +0.1 progress per minute

**Trigger Activations:**
- Variable progress rewards based on trigger type

**Unique Board Exploration:**
- +2 progress per unique board visited

### Progress Calculation Example

```python
# User views 10 threads (first time each)
thread_progress = 10 * 1 = 10

# User views 30 posts (first time each)
post_progress = 30 * 1 = 30

# User spends 20 minutes on site
time_progress = 20 * 0.1 = 2

# User activates "DEEP_READER" trigger
trigger_progress = 5

# Total progress
total = 10 + 30 + 2 + 5 = 47 (MEDIUM level)
```

### Level Effects

**LOW (0-20%)**
- Subtle anomalies only (glitches, flickers, static)
- No content corruption
- Rare occurrence (2% chance per request)
- User may not notice anything unusual

**MEDIUM (21-50%)**
- More varied anomalies (whispers, presence, fake posts)
- Light corruption starts (5% chance)
- Anomalies occur occasionally (8% chance)
- User begins to notice something is off

**HIGH (51-80%)**
- Intense anomalies (shadows, eyes, recognition)
- Moderate corruption (15% chance)
- Frequent anomalies (20% chance)
- Content visibly corrupted
- Meta-messages may appear

**CRITICAL (81-100%)**
- Extreme anomalies (heartbeat, scroll hijacking, post deletion)
- Heavy corruption (35% chance)
- Constant anomalies (40% chance)
- Severe text corruption
- Fake edit timestamps
- Ghost posts appear
- System acknowledges user's presence

## Anomaly Generation

Anomalies are random events delivered via WebSocket that create unsettling effects in the frontend.

### Anomaly Types by Progress Level

**LOW Level:**
- `GLITCH` (30%) - Visual glitches and artifacts
- `FLICKER` (30%) - Screen flickers
- `STATIC` (20%) - Static noise effects
- `VIEWER_COUNT` (20%) - Fake viewer counts

**MEDIUM Level:**
- `GLITCH` (15%) - Visual glitches
- `FLICKER` (15%) - Screen flickers
- `WHISPER` (20%) - Creepy text messages
- `PRESENCE` (20%) - "You are being watched" messages
- `NEW_POST` (15%) - Fake new post notifications
- `POST_EDIT` (15%) - Posts appear to edit themselves

**HIGH Level:**
- `POST_CORRUPT` (15%) - Active post corruption
- `WHISPER` (15%) - Disturbing whispers
- `PRESENCE` (15%) - Presence indicators
- `SHADOW` (10%) - Shadow effects
- `NOTIFICATION` (15%) - Fake notifications
- `RECOGNITION` (10%) - "We remember you" messages
- `TYPING` (10%) - Someone is typing indicator
- `CURSOR` (10%) - Cursor manipulation

**CRITICAL Level:**
- `POST_CORRUPT` (12%) - Heavy post corruption
- `PRESENCE` (12%) - Strong presence effects
- `SHADOW` (10%) - Multiple shadows
- `EYES` (10%) - Eyes watching effect
- `RECOGNITION` (12%) - Personal recognition
- `MEMORY` (10%) - References to user's history
- `TYPING` (10%) - Unsettling typing messages
- `HEARTBEAT` (12%) - Heartbeat sounds/visuals
- `SCROLL` (6%) - Forced scrolling
- `POST_DELETE` (6%) - Posts disappear

### Anomaly Severity

Each anomaly has a severity level that affects its intensity:

| Severity | LOW | MEDIUM | HIGH | CRITICAL |
|----------|-----|--------|------|----------|
| **SUBTLE** | 70% | 30% | 0% | 0% |
| **MILD** | 30% | 40% | 20% | 0% |
| **MODERATE** | 0% | 30% | 40% | 20% |
| **INTENSE** | 0% | 0% | 40% | 50% |
| **EXTREME** | 0% | 0% | 0% | 30% |

### Special Messages

**Whisper Messages:**
- "...ты слышишь нас?..." (do you hear us?)
- "...не уходи..." (don't leave)
- "...мы знаем..." (we know)
- "...скоро..." (soon)
- "...оглянись..." (look behind you)
- "...ты не один..." (you're not alone)
- "...помнишь?..." (remember?)

**Recognition Messages:**
- "Добро пожаловать обратно." (Welcome back)
- "Мы ждали тебя." (We've been waiting for you)
- "Ты вернулся." (You've returned)
- "Мы помним твоё лицо." (We remember your face)
- "Время здесь течёт иначе." (Time flows differently here)

**Presence Messages:**
- "Кто-то смотрит на тебя." (Someone is watching you)
- "Ты не один здесь." (You're not alone here)
- "Они рядом." (They are near)
- "Что-то следит за тобой." (Something is following you)
- "Тень движется." (A shadow moves)

### Anomaly Generation Logic

```python
# Check if should generate anomaly
chance = base_chance[progress_level] * time_multiplier * trigger_multiplier

if random.random() < chance:
    # Select anomaly type from pool
    anomaly_type = weighted_choice(pool[progress_level])

    # Select severity
    severity = weighted_choice(severity_weights[progress_level])

    # Generate custom data
    custom_data = generate_custom_data(anomaly_type, user_state)

    # Create and queue event
    event = create_anomaly(anomaly_type, severity, custom_data)
    await queue.push(user_id, event)
```

## Time-of-Day Effects

The Ritual Engine adjusts anomaly behavior based on the time of day.

### Time Periods

| Period | Hours (UTC) | Anomaly Multiplier |
|--------|-------------|-------------------|
| **DAWN** | 5:00 - 7:59 | 0.8x |
| **MORNING** | 8:00 - 11:59 | 0.5x |
| **AFTERNOON** | 12:00 - 17:59 | 0.7x |
| **EVENING** | 18:00 - 21:59 | 1.0x |
| **NIGHT** | 22:00 - 1:59 | 1.5x |
| **WITCHING HOUR** | 2:00 - 4:59 | 2.5x |

### Night Effects

During night hours (22:00 - 5:59):
- Anomaly chance multiplied by 1.5x
- Corruption chance increased
- Darker anomaly types more likely
- Viewer counts inflated

### Witching Hour (2:00 - 4:59 AM)

The witching hour is a special period with maximum anomaly activity:

**Multipliers:**
- Base anomaly chance: 2.5x
- Additional witching hour bonus: 1.5x
- Total effective multiplier: 3.75x

**Burst Events:**
Special burst of multiple anomalies triggered upon entering witching hour:

| Progress Level | Burst Count |
|----------------|-------------|
| LOW | 3 anomalies |
| MEDIUM | 4 anomalies |
| HIGH | 6 anomalies |
| CRITICAL | 9 anomalies |

**Witching Hour Anomaly Types:**
- `SHADOW` - Shadow effects
- `EYES` - Eyes watching
- `WHISPER` - Disturbing whispers
- `PRESENCE` - Strong presence
- `HEARTBEAT` - Heartbeat effects

All witching hour anomalies are forced to `INTENSE` severity with staggered delays (2-5 seconds apart).

## Content Mutation

Content mutation corrupts and transforms text based on user progress, creating an increasingly disturbing reading experience.

### Mutation Styles

**Glitch** - Replace characters with block symbols
```
Original: "Hello world"
Glitched: "H█ll░ w▒rld"
```

**Zalgo** - Add combining diacritical marks for "cursed" text
```
Original: "Hello"
Zalgo:   "H̴̡̨e̸̢̛l̵̨̛l̶̢̀o̵̧͝"
```

**Redaction** - Black out words with blocks
```
Original: "This is a secret message"
Redacted: "This ████ a ██████ message"
```

**Word Replacement** - Replace specific words with creepy alternatives
```
Original: "Hello friend, need help?"
Replaced: "...привет... ты не один, помоги мне?"
```

**Insertion** - Insert creepy phrases into text
```
Original: "This is normal text"
Inserted: "This is normal НЕ УХОДИ text"
```

### Corruption Intensity

Corruption intensity scales linearly with progress:

```python
base_intensity = progress / 100

# Boost at critical level
if progress >= 80:
    base_intensity *= 1.3

# Range: 0.0 - 1.3
```

### Style Selection by Intensity

| Intensity | Styles |
|-----------|--------|
| 0.0 - 0.3 | glitch, insert |
| 0.3 - 0.6 | glitch, zalgo, replace, insert |
| 0.6 - 1.0 | glitch, zalgo, redact, replace |

### Word Replacements

| Original | Replacement |
|----------|-------------|
| привет (hello) | ...привет... |
| здравствуй (greetings) | они здесь (they are here) |
| помощь (help) | помоги мне (help me) |
| ответ (answer) | они слышат (they hear) |
| время (time) | время истекает (time is running out) |
| друг (friend) | ты не один (you're not alone) |
| один (alone) | никогда не один (never alone) |
| темно (dark) | они в темноте (they're in the darkness) |
| свет (light) | свет гаснет (light fades) |
| дом (home) | дом помнит (home remembers) |
| ночь (night) | ночь видит (night sees) |

### Creepy Insertions

Random phrases inserted into text:
- "..."
- "ОНИ ЗДЕСЬ" (THEY ARE HERE)
- "НЕ ОГЛЯДЫВАЙСЯ" (DON'T LOOK BACK)
- "ПОМОГИ" (HELP)
- "Я ВИЖУ ТЕБЯ" (I SEE YOU)
- "ТЫ НЕ ОДИН" (YOU'RE NOT ALONE)
- "СКОРО" (SOON)
- "МЫ ЖДЁМ" (WE'RE WAITING)
- "ОН СМОТРИТ" (HE'S WATCHING)
- "БЕГИ" (RUN)

### Meta-Messages

At HIGH and CRITICAL levels, meta-messages may appear that directly address the reader:

- "Ты ещё здесь?" (Are you still here?)
- "Зачем ты читаешь это?" (Why are you reading this?)
- "Мы знаем, что ты смотришь." (We know you're watching)
- "Ты чувствуешь это?" (Do you feel it?)
- "Не закрывай страницу." (Don't close the page)

These appear with 30% probability at HIGH/CRITICAL levels and are added to the post data as `_meta_message`.

### Ghost Posts

Ghost posts are fake posts generated during anomaly events that appear temporarily and then disappear.

**Ghost Post Characteristics:**
- ID: -1 (fake)
- Username: One of ["???", "█████", "Неизвестный", "[удалено]", "Наблюдатель", "Он", "..."]
- Content: Creepy message
- `_is_ghost`: true
- `_disappears_in`: 5000-15000ms

**Ghost Post Messages:**
- "..."
- "Помоги мне." (Help me)
- "Ты видишь это?" (Do you see this?)
- "Они знают, что ты здесь." (They know you're here)
- "НЕ УХОДИ" (DON'T LEAVE)
- "█████████████"
- "Я вижу тебя." (I see you)
- "Почему ты ещё читаешь?" (Why are you still reading?)
- "Выход закрыт." (The exit is closed)
- "Мы ждали тебя." (We've been waiting for you)

### Post Mutation Example

```python
# Original post
{
    "id": 123,
    "content": "This is a normal post about cats",
    "username": "user123",
    "created_at": "2024-01-01T12:00:00"
}

# At CRITICAL level (80%+ progress)
{
    "id": 123,
    "content": "Th█s is a ОНИ ЗДЕСЬ normal п░ст about ███s",
    "username": "user123",
    "created_at": "2024-01-01T12:00:00",
    "_corrupted": true,
    "_meta_message": "Ты ещё здесь?",
    "_fake_edit": "2024-01-01T12:05:23.123456"
}
```

### Thread Mutation

Threads can also be mutated:

**Title Corruption:**
- 50% chance at current intensity
- Always uses "glitch" style
- Intensity reduced by 50% for titles

**Fake Viewer Counts:**
- At HIGH/CRITICAL levels
- 40% chance to add fake viewers
- Adds 3-13 to view count
- Shows 2-7 "currently watching"

## State Management

### Redis Storage

**Key Format:** `ritual_state:{user_id}`

**TTL:** 24 hours (86400 seconds)

**Storage Method:**
- JSON-encoded RitualState object
- Atomic operations via Redis SETEX
- TTL refreshed on each save

### State Lifecycle

1. **Creation** - User's first visit creates new state
2. **Updates** - State updated on each request/action
3. **Persistence** - Saved to Redis with 24h TTL
4. **Expiration** - State expires after 24h of inactivity
5. **Refresh** - Active users keep their state fresh

### State Operations

**Get or Create:**
```python
state, is_new = await state_manager.get_or_create(user_id)
```

**Update Progress:**
```python
state.progress += delta
await state_manager.save(state)
```

**Add View History:**
```python
state.viewed_threads.append(thread_id)
if len(state.viewed_threads) > 100:
    state.viewed_threads = state.viewed_threads[-100:]
await state_manager.save(state)
```

**Record Trigger:**
```python
state.triggers_hit.add(trigger_name)
await state_manager.save(state)
```

### Connection Management

Active WebSocket connections are tracked separately:

**Key:** `ritual_connections`

**Format:** Redis Hash
- Key: user_id
- Value: "1" (connection marker)

**Heartbeat:** Connections should send heartbeats to stay registered

**Usage:**
```python
# Register connection
await connection_manager.connect(user_id)

# Check if connected
is_online = await connection_manager.is_connected(user_id)

# Disconnect
await connection_manager.disconnect(user_id)
```

## Request Flow

### Typical Request Lifecycle

```
1. User makes HTTP request
   │
   ▼
2. Middleware intercepts
   │
   ▼
3. RitualEngine.on_request(user_id, path, method)
   │
   ├─► Get or create RitualState
   │
   ├─► Check triggers
   │   ├─► Calculate trigger effects
   │   ├─► Apply progress deltas
   │   └─► Queue forced anomalies
   │
   ├─► Maybe generate random anomaly
   │   ├─► Check if user is connected
   │   ├─► Calculate anomaly chance
   │   ├─► Generate anomaly event
   │   └─► Push to anomaly queue
   │
   └─► Save updated state
   │
   ▼
4. Request continues to handler
   │
   ▼
5. Handler retrieves content
   │
   ▼
6. RitualEngine.mutate_post(post, state)
   │
   ├─► Check corruption chance
   │
   ├─► Calculate corruption intensity
   │
   ├─► Apply corruption
   │
   └─► Add meta-messages
   │
   ▼
7. Return mutated content to client
   │
   ▼
8. WebSocket delivers queued anomalies
```

### Thread/Post View Flow

```
1. User views thread/post
   │
   ▼
2. RitualEngine.on_thread_view(user_id, thread_id)
   │
   ├─► Calculate progress delta
   │   └─► +1 for first view, 0 for revisit
   │
   ├─► Update view history
   │   └─► Keep last 100 threads
   │
   ├─► Apply progress delta
   │
   └─► Save state
```

## Performance Considerations

### Redis Usage

**State Operations:**
- Get: Single GET operation
- Save: Single SETEX operation
- Typical latency: <1ms

**Queue Operations:**
- Push: RPUSH + EXPIRE (~2ms)
- Pop: BLPOP (blocking, timeout configurable)

**Connection Tracking:**
- HSET for updates
- HEXISTS for checks
- Very fast (<1ms)

### Optimization Tips

1. **Batch Operations** - Use Redis pipelines for multiple operations
2. **Limit View History** - Keep only last 100 threads, 500 posts
3. **Queue Trimming** - Limit queue to 100 events per user
4. **TTL Management** - Auto-expire inactive states after 24h
5. **Connection Checks** - Only generate anomalies for connected users

### Scaling Considerations

- Redis can handle 10K+ operations/second
- State size: ~2-5KB per user
- Queue size: ~1KB per event
- Memory usage: ~10KB per active user
- Recommended: Redis with persistence enabled

## Configuration

### Adjustable Parameters

**Progress Engine:**
```python
PROGRESS_PER_THREAD_VIEW = 1
PROGRESS_PER_POST_VIEW = 0.5
PROGRESS_PER_MINUTE = 0.1
```

**State Manager:**
```python
DEFAULT_TTL = 86400  # 24 hours
MAX_VIEWED_THREADS = 100
MAX_VIEWED_POSTS = 500
```

**Anomaly Queue:**
```python
DEFAULT_TTL = 3600  # 1 hour
MAX_QUEUE_SIZE = 100
```

**Anomaly Chances (per level):**
```python
BASE_ANOMALY_CHANCES = {
    ProgressLevel.LOW: 0.02,      # 2%
    ProgressLevel.MEDIUM: 0.08,   # 8%
    ProgressLevel.HIGH: 0.20,     # 20%
    ProgressLevel.CRITICAL: 0.40, # 40%
}
```

**Corruption Chances (per level):**
```python
CORRUPTION_CHANCES = {
    ProgressLevel.LOW: 0.0,       # 0%
    ProgressLevel.MEDIUM: 0.05,   # 5%
    ProgressLevel.HIGH: 0.15,     # 15%
    ProgressLevel.CRITICAL: 0.35, # 35%
}
```

## Example Usage

### Initialize Engine

```python
from redis.asyncio import Redis
from app.services.ritual_engine import RitualEngine

# Create Redis client
redis_client = Redis(host='localhost', port=6379, decode_responses=True)

# Initialize engine
engine = RitualEngine(redis_client)
```

### Process Request

```python
# On each request (in middleware)
state, is_new = await engine.on_request(
    user_id="user123",
    path="/api/threads/456",
    method="GET"
)

if is_new:
    print("New visitor!")
```

### Handle Content View

```python
# When user views thread
await engine.on_thread_view(user_id="user123", thread_id=456)

# When user views post
await engine.on_post_view(user_id="user123", post_id=789)
```

### Mutate Content

```python
# Get posts from database
posts = await db.get_thread_posts(thread_id)

# Get user state
state = await engine.get_user_state(user_id)

# Mutate each post
mutated_posts = [
    engine.mutate_post(post, state)
    for post in posts
]

# Return mutated content
return {"posts": mutated_posts}
```

### Queue Specific Anomaly

```python
from app.schemas.anomaly import AnomalyType

# Force a specific anomaly
await engine.queue_anomaly_for_type(
    user_id="user123",
    anomaly_type=AnomalyType.WHISPER,
    custom_data={"message": "Custom whisper message"}
)
```

### Admin Operations

```python
# Get user state
state = await engine.get_user_state("user123")
print(f"Progress: {state.progress}%")

# Set progress directly
await engine.set_user_progress("user123", 50)

# Reset user
await engine.reset_user_state("user123")

# Get connected users
connected = await engine.get_connected_users()
print(f"Connected: {len(connected)} users")
```

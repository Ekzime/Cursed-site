# Triggers Documentation

## Overview

Triggers are behavioral patterns that the Ritual Engine detects and responds to. They activate based on user actions, time of day, reading patterns, and other conditions. When triggered, they can award progress, increase anomaly chances, force specific anomalies, or unlock hidden content.

Triggers create a personalized experience by recognizing and responding to how users interact with the board, making the horror elements feel more intelligent and aware.

## Trigger System Architecture

```
User Action
    │
    ▼
TriggerChecker.check_new_triggers(state, path, method)
    │
    ├─► Build TriggerCheckContext
    │   ├─► User state
    │   ├─► Current request info
    │   └─► Time of day
    │
    ├─► Check each trigger condition
    │   ├─► Skip already-hit triggers
    │   └─► Evaluate condition function
    │
    ├─► Collect activated triggers
    │   └─► Create TriggerResult for each
    │
    └─► Return results
         │
         ▼
RitualEngine._process_triggers(user_id, state, results)
    │
    ├─► Aggregate effects
    │   ├─► Sum progress deltas
    │   ├─► Find max anomaly multiplier
    │   ├─► Collect forced anomalies
    │   └─► Gather unlocks
    │
    ├─► Apply progress changes
    │
    ├─► Record trigger activation
    │
    ├─► Update known patterns
    │
    └─► Queue forced anomalies
```

## Trigger Categories

### Visit-Based Triggers

Triggers that activate based on visit patterns and timing.

#### FIRST_VISIT
**Description:** Activates on user's very first visit to the board.

**Condition:**
```python
progress == 0
```

**Effect:**
- Progress: +5
- Message: "Welcome. You shouldn't have come here."
- Pattern set: `visit_count = 1`

**Notes:**
- One-time trigger
- Sets baseline for user's ritual progression

---

#### RETURNEE
**Description:** User returns after 7+ days since first visit.

**Condition:**
```python
days_since_first_visit >= 7
```

**Effect:**
- Progress: +10
- Message: "We've been waiting for you."
- Anomaly multiplier: 1.5x

**Notes:**
- Recognizes returning users
- Higher anomaly chance for dramatic reentry

---

#### FREQUENT_VISITOR
**Description:** User has visited 5 or more times.

**Condition:**
```python
visit_count >= 5
```

**Effect:**
- Progress: +8
- Message: "You keep coming back. Why?"
- Pattern set: `frequent = true`

**Detection:**
- Tracks `visit_count` in known_patterns
- Incremented on each session

---

#### LATE_NIGHT
**Description:** User visits during night hours (22:00 - 5:59).

**Condition:**
```python
is_night_hour() == True
```

**Effect:**
- Progress: +3
- Anomaly multiplier: 1.3x
- Pattern increment: `night_visits += 1`

**Time Range:**
- Night: 22:00 - 1:59
- Witching hour counts as late night

**Notes:**
- Re-triggers each night session
- Builds toward NIGHT_OWL trigger

---

#### WITCHING_HOUR
**Description:** User visits during the witching hour (2:00 - 4:59 AM).

**Condition:**
```python
is_witching_hour() == True
```

**Effect:**
- Progress: +15
- Anomaly multiplier: 2.0x
- Force anomaly: SHADOW or EYES
- Message: "The veil is thinnest now."

**Time Range:** 2:00 - 4:59 AM (UTC or configured timezone)

**Notes:**
- Most powerful time-based trigger
- Automatically triggers burst events
- Can re-trigger on each witching hour visit

---

### Reading Behavior Triggers

Triggers based on how users read and consume content.

#### DEEP_READER
**Description:** User has read 20+ posts.

**Condition:**
```python
len(viewed_posts) >= 20
```

**Effect:**
- Progress: +5
- Message: "You're digging deeper..."

**Notes:**
- Rewards thorough exploration
- One-time trigger

---

#### SPEED_READER
**Description:** User reads very fast (>5 posts per minute).

**Condition:**
```python
if time_on_site < 60:
    return False
posts_per_minute = len(viewed_posts) / (time_on_site / 60)
return posts_per_minute > 5
```

**Effect:**
- Progress: +3
- Message: "Why are you rushing?"
- Force anomaly: GLITCH

**Minimum Time:** 60 seconds on site

**Notes:**
- Detects skimming behavior
- Triggers visual disruption

---

#### SLOW_READER
**Description:** User reads slowly and carefully (>1 minute per post average).

**Condition:**
```python
if len(viewed_posts) < 5:
    return False
avg_time_per_post = time_on_site / len(viewed_posts)
return avg_time_per_post > 60
```

**Effect:**
- Progress: +7
- Message: "You're paying attention. Good."
- Anomaly multiplier: 1.2x

**Minimum Posts:** 5

**Notes:**
- Rewards careful reading
- Increases anomaly chances as "reward"

---

#### OBSESSIVE
**Description:** User re-reads the same content (>50% revisit ratio).

**Condition:**
```python
if len(viewed_threads) < 5:
    return False
unique_threads = set(viewed_threads)
revisit_ratio = 1 - (len(unique_threads) / len(viewed_threads))
return revisit_ratio > 0.5
```

**Effect:**
- Progress: +12
- Message: "Looking for something? Or someone?"
- Force anomaly: RECOGNITION
- Pattern set: `obsessive = true`

**Minimum Threads:** 5 thread views

**Notes:**
- Detects pattern-seeking or obsessive behavior
- Forces recognition anomaly (system acknowledges awareness)

---

#### EXPLORER
**Description:** User has viewed 15+ different threads.

**Condition:**
```python
len(set(viewed_threads)) >= 15
```

**Effect:**
- Progress: +6
- Message: "Curiosity will be your undoing."

**Notes:**
- Rewards broad exploration
- One-time trigger

---

### Progression Triggers

Triggers that activate at specific progress milestones.

#### HALFWAY
**Description:** User reaches 50% progress.

**Condition:**
```python
progress >= 50
```

**Effect:**
- Progress: +5
- Message: "There's no turning back now."
- Unlock board: "depths" (if implemented)

**Notes:**
- Marks transition to HIGH level
- One-time trigger
- May unlock hidden content

---

#### ALMOST_THERE
**Description:** User reaches 80% progress.

**Condition:**
```python
progress >= 80
```

**Effect:**
- Progress: +5
- Message: "You're almost one of us."
- Force anomaly: HEARTBEAT

**Notes:**
- Marks entry to CRITICAL level
- Forces heartbeat effect
- One-time trigger

---

#### ENLIGHTENED
**Description:** User reaches 100% progress.

**Condition:**
```python
progress >= 100
```

**Effect:**
- Progress: 0 (no further progress needed)
- Message: "You are one of us now."
- Force anomaly: EYES
- Unlock thread: Special ending thread (if implemented)

**Notes:**
- Maximum progression achieved
- May unlock special ending content
- One-time trigger

---

### Time-Based Triggers

Triggers related to duration and time spent on the site.

#### TOO_LONG
**Description:** User has spent 1+ hour on the site.

**Condition:**
```python
time_on_site >= 3600  # 1 hour in seconds
```

**Effect:**
- Progress: +10
- Message: "You should take a break. Or not."
- Anomaly multiplier: 1.4x

**Notes:**
- One-time trigger
- Subtle suggestion that the system is aware of time

---

#### MARATHON
**Description:** User has spent 3+ hours on the site.

**Condition:**
```python
time_on_site >= 10800  # 3 hours in seconds
```

**Effect:**
- Progress: +20
- Message: "Time doesn't matter here anymore."
- Force anomaly: MEMORY
- Anomaly multiplier: 1.8x

**Notes:**
- Rewards/punishes extended sessions
- Forces memory anomaly (references past views)
- One-time trigger

---

#### NIGHT_OWL
**Description:** User has visited during night hours 3+ times.

**Condition:**
```python
known_patterns.get("night_visits", 0) >= 3
```

**Effect:**
- Progress: +8
- Message: "The darkness suits you."
- Pattern set: `night_owl = true`

**Notes:**
- Requires multiple night sessions
- Builds from LATE_NIGHT trigger
- One-time trigger

---

#### DAWN_VISITOR
**Description:** User visits during dawn (5:00 - 7:59).

**Condition:**
```python
get_time_of_day() == "dawn"
```

**Effect:**
- Progress: +2
- Message: "The night is ending. Did you survive?"

**Time Range:** 5:00 - 7:59

**Notes:**
- Quieter than night triggers
- Can re-trigger each dawn session

---

### Interaction Triggers

Triggers based on user interactions and content creation.

#### POSTED
**Description:** User creates a post (reply).

**Condition:**
```python
current_method == "POST" and "/posts" in current_path
```

**Effect:**
- Progress: +4
- Message: "Your words are now part of this place."
- Pattern set: `has_posted = true`

**Notes:**
- Activates on POST request to posts endpoint
- One-time trigger for first post
- Acknowledges user's contribution

---

#### THREAD_CREATOR
**Description:** User creates a new thread.

**Condition:**
```python
current_method == "POST" and
"/threads" in current_path and
"/posts" not in current_path
```

**Effect:**
- Progress: +8
- Message: "You've created something. It will outlive you."
- Force anomaly: NEW_POST
- Pattern set: `has_created_thread = true`

**Notes:**
- More significant than POSTED
- Forces fake new post anomaly
- One-time trigger

---

### Special Triggers

Unique triggers with special conditions.

#### FOUND_HIDDEN
**Description:** User discovers hidden content.

**Condition:**
```python
hidden_indicators = ["hidden", "secret", "void", "nightmare"]
return any(ind in current_path.lower() for ind in hidden_indicators)
```

**Effect:**
- Progress: +15
- Message: "You found what you weren't meant to see."
- Unlock board: "void" (if implemented)
- Anomaly multiplier: 2.0x

**Path Indicators:**
- "hidden"
- "secret"
- "void"
- "nightmare"

**Notes:**
- Rewards exploration off the beaten path
- One-time trigger
- May unlock even deeper content

---

#### PATTERN_SEEKER
**Description:** User views threads in sequential order, suggesting pattern-seeking behavior.

**Condition:**
```python
if len(viewed_threads) < 5:
    return False

sequential_count = 0
for i in range(1, len(viewed_threads)):
    if abs(viewed_threads[i] - viewed_threads[i - 1]) == 1:
        sequential_count += 1

return sequential_count >= 3
```

**Effect:**
- Progress: +10
- Message: "You're looking for patterns. There are none. Or are there?"
- Pattern set: `seeking = true`
- Force anomaly: MEMORY

**Minimum Threads:** 5

**Sequential Requirement:** 3+ threads with sequential IDs

**Notes:**
- Detects deliberate pattern investigation
- System acknowledges the search
- May lead to ARG-style content

---

## Trigger Effects

Triggers can produce multiple types of effects:

### Progress Rewards

Direct progress point awards that move the user through the progression levels.

**Range:** +2 to +20 progress points

**Examples:**
- FIRST_VISIT: +5
- MARATHON: +20
- WITCHING_HOUR: +15

### Anomaly Chance Multipliers

Temporary or permanent increases to anomaly generation probability.

**Range:** 1.2x to 2.0x

**Examples:**
- SLOW_READER: 1.2x
- LATE_NIGHT: 1.3x
- FOUND_HIDDEN: 2.0x

**Application:**
```python
final_chance = base_chance * max_multiplier * time_multiplier
```

### Forced Anomalies

Specific anomaly types that are immediately queued and delivered.

**Examples:**
- WITCHING_HOUR: Forces SHADOW or EYES
- SPEED_READER: Forces GLITCH
- OBSESSIVE: Forces RECOGNITION
- ALMOST_THERE: Forces HEARTBEAT

**Implementation:**
```python
if effect.force_anomaly:
    anomaly_type = AnomalyType(effect.force_anomaly)
    event = anomaly_generator.generate_specific(
        anomaly_type,
        state,
        triggered_by="trigger_name"
    )
    await anomaly_queue.push(user_id, event)
```

### Messages

Text messages displayed to the user, often breaking the fourth wall.

**Examples:**
- "Welcome. You shouldn't have come here."
- "You're paying attention. Good."
- "There's no turning back now."
- "Time doesn't matter here anymore."

### Hidden Content Unlocks

Unlock access to hidden boards or threads.

**Board Unlocks:**
- HALFWAY: "depths"
- FOUND_HIDDEN: "void"

**Thread Unlocks:**
- ENLIGHTENED: Special ending thread

**Implementation:**
```python
if effect.unlock_board:
    # Add board to user's accessible boards
    unlocks_boards.append(effect.unlock_board)

if effect.unlock_thread:
    # Add thread to user's accessible threads
    unlocks_threads.append(effect.unlock_thread)
```

### Pattern Setting

Update user's known_patterns dict for tracking complex behaviors.

**Examples:**
- FIRST_VISIT: `visit_count = 1`
- OBSESSIVE: `obsessive = true`
- POSTED: `has_posted = true`
- LATE_NIGHT: `night_visits += 1`

**Usage:**
```python
state.known_patterns["key"] = value
```

## Trigger Detection Logic

### TriggerCheckContext

The context object contains all information needed to evaluate triggers:

```python
@dataclass
class TriggerCheckContext:
    user_id: str
    progress: int
    viewed_threads: List[int]
    viewed_posts: List[int]
    time_on_site: int  # seconds
    first_visit_timestamp: float
    last_activity_timestamp: float
    triggers_hit: Set[str]
    known_patterns: Dict[str, Any]
    current_path: Optional[str]
    current_method: Optional[str]
    is_night: bool
    is_witching: bool
    time_of_day: str
```

### Condition Functions

Each trigger has a condition function that receives the context:

```python
TriggerCondition = Callable[[TriggerCheckContext], bool]
```

**Example - Simple condition:**
```python
TriggerType.FIRST_VISIT: lambda ctx: ctx.progress == 0
```

**Example - Complex condition:**
```python
TriggerType.OBSESSIVE: lambda ctx: self._check_obsessive(ctx)

def _check_obsessive(self, ctx: TriggerCheckContext) -> bool:
    if len(ctx.viewed_threads) < 5:
        return False
    unique_threads = set(ctx.viewed_threads)
    revisit_ratio = 1 - (len(unique_threads) / len(ctx.viewed_threads))
    return revisit_ratio > 0.5
```

### Activation Logic

```python
def check_trigger(trigger_type, ctx):
    # Get condition function
    condition = conditions[trigger_type]

    # Check if already activated (for one-time triggers)
    already_hit = trigger_type.value in ctx.triggers_hit

    # Evaluate condition
    condition_met = condition(ctx)

    if not condition_met:
        return TriggerResult(activated=False)

    # Get effect definition
    effect = TRIGGER_EFFECTS[trigger_type]

    return TriggerResult(
        trigger_type=trigger_type,
        activated=True,
        first_activation=not already_hit,
        effect=effect,
        metadata={...}
    )
```

### First Activation vs Re-Activation

Some triggers can re-activate on each matching request, while others are one-time only.

**One-Time Effects (only on first activation):**
- Progress rewards
- Messages
- Unlocks
- Pattern setting

**Recurring Effects (on every activation):**
- Anomaly chance multipliers
- Forced anomalies (for some triggers)

**Implementation:**
```python
if result.first_activation:
    # Apply progress
    state.progress += effect.progress_delta

    # Show message
    if effect.message:
        messages.append(effect.message)

    # Record trigger
    state.triggers_hit.add(trigger_type.value)

# Always apply multiplier
max_multiplier = max(max_multiplier, effect.anomaly_chance_multiplier)
```

## Trigger Combinations

Multiple triggers can activate simultaneously, with effects aggregating:

### Example Scenario

**User:** Returns after 10 days, visits at 3:00 AM, starts reading

**Activated Triggers:**
1. RETURNEE (7+ days)
2. LATE_NIGHT (night hours)
3. WITCHING_HOUR (2-5 AM)

**Aggregated Effects:**
```python
Progress: +5 (RETURNEE) +3 (LATE_NIGHT) +15 (WITCHING_HOUR) = +23 total

Anomaly Multiplier: max(1.5, 1.3, 2.0) = 2.0x

Messages:
- "We've been waiting for you."
- "The veil is thinnest now."

Forced Anomalies:
- SHADOW (from WITCHING_HOUR)

Final State:
- Progress jumped from 35 to 58 (MEDIUM → HIGH)
- Anomaly chance: 8% * 2.0 * 2.5 (time) = 40% chance
- Shadow anomaly queued
- User immediately notices increased activity
```

## Implementation Example

### Check Triggers on Request

```python
# In RitualEngine.on_request
trigger_results = self.trigger_checker.check_new_triggers(
    state,
    path="/api/threads/123",
    method="GET"
)

if trigger_results:
    await self._process_triggers(user_id, state, trigger_results)
```

### Process Trigger Effects

```python
async def _process_triggers(user_id, state, results):
    # Aggregate effects
    effects = trigger_checker.get_applicable_effects(results)

    # Apply progress
    state.progress += effects["total_progress_delta"]

    # Record triggers
    for result in results:
        if result.first_activation:
            state.triggers_hit.add(result.trigger_type.value)
            logger.info(f"Trigger: {result.trigger_type.value}")

    # Update patterns
    for key, value in effects["patterns_to_set"].items():
        state.known_patterns[key] = value

    # Queue forced anomalies
    for anomaly_type_str in effects["force_anomalies"]:
        anomaly_type = AnomalyType(anomaly_type_str)
        event = anomaly_generator.generate_specific(
            anomaly_type,
            state,
            triggered_by="trigger"
        )
        await anomaly_queue.push(user_id, event)
```

### Custom Trigger Creation

To add a new trigger:

1. **Define trigger type** in `app/schemas/trigger.py`:
```python
class TriggerType(str, Enum):
    CUSTOM_TRIGGER = "custom_trigger"
```

2. **Define effect** in `TRIGGER_EFFECTS`:
```python
TRIGGER_EFFECTS = {
    TriggerType.CUSTOM_TRIGGER: TriggerEffect(
        progress_delta=5,
        message="Custom message",
        anomaly_chance_multiplier=1.5,
    )
}
```

3. **Add condition** in `TriggerChecker._build_conditions()`:
```python
TriggerType.CUSTOM_TRIGGER: lambda ctx: self._check_custom(ctx)

def _check_custom(self, ctx: TriggerCheckContext) -> bool:
    # Custom logic here
    return ctx.progress > 50 and len(ctx.viewed_posts) > 100
```

## Trigger Analytics

Triggers provide valuable insights into user behavior:

### Tracking Trigger Activation

```python
# Get user's activated triggers
state = await engine.get_user_state(user_id)
activated_triggers = state.triggers_hit

print(f"User has activated: {len(activated_triggers)} triggers")
print(f"Triggers: {', '.join(activated_triggers)}")
```

### Common Patterns

**Power Users:**
- MARATHON + DEEP_READER + EXPLORER

**Night Dwellers:**
- NIGHT_OWL + WITCHING_HOUR + TOO_LONG

**Investigators:**
- PATTERN_SEEKER + FOUND_HIDDEN + OBSESSIVE

**Casual Users:**
- FIRST_VISIT + SPEED_READER

### Progression Paths

Different trigger combinations lead to different progression rates:

**Fast Path (reaches CRITICAL quickly):**
- WITCHING_HOUR (+15)
- MARATHON (+20)
- FOUND_HIDDEN (+15)
- OBSESSIVE (+12)
- Total: +62 progress from just 4 triggers

**Slow Path (gradual progression):**
- FIRST_VISIT (+5)
- LATE_NIGHT (+3)
- DEEP_READER (+5)
- POSTED (+4)
- Total: +17 progress from 4 triggers

## Best Practices

### For Game Designers

1. **Balance Progress Rewards** - Don't let single triggers jump too many levels
2. **Create Narrative Arcs** - Trigger messages should tell a story
3. **Reward Exploration** - Hidden content triggers should feel special
4. **Acknowledge Behavior** - Use triggers to make the system feel aware
5. **Time Matters** - Night triggers create atmosphere

### For Developers

1. **Keep Conditions Fast** - Triggers check on every request
2. **Avoid Heavy Computation** - Use simple comparisons
3. **Test Edge Cases** - What if user has 0 threads viewed?
4. **Log Activations** - Monitor trigger frequency
5. **Make Them Configurable** - Allow tuning thresholds

### For Content Creators

1. **Write Unsettling Messages** - Break the fourth wall
2. **Build Anticipation** - Progress messages should foreshadow
3. **Create Mystery** - Vague messages are more effective
4. **Vary Tone** - Some helpful, some threatening
5. **Reference Context** - Use trigger metadata in messages

## Summary Table

| Trigger | Category | Progress | Multiplier | One-Time | Special Effect |
|---------|----------|----------|------------|----------|----------------|
| FIRST_VISIT | Visit | +5 | 1.0x | Yes | Sets visit_count |
| RETURNEE | Visit | +10 | 1.5x | Yes | - |
| FREQUENT_VISITOR | Visit | +8 | 1.0x | Yes | - |
| LATE_NIGHT | Visit | +3 | 1.3x | No | Increments night_visits |
| WITCHING_HOUR | Visit | +15 | 2.0x | No | Forces SHADOW/EYES |
| DEEP_READER | Reading | +5 | 1.0x | Yes | - |
| SPEED_READER | Reading | +3 | 1.0x | Yes | Forces GLITCH |
| SLOW_READER | Reading | +7 | 1.2x | Yes | - |
| OBSESSIVE | Reading | +12 | 1.0x | Yes | Forces RECOGNITION |
| EXPLORER | Reading | +6 | 1.0x | Yes | - |
| HALFWAY | Progress | +5 | 1.0x | Yes | Unlocks "depths" |
| ALMOST_THERE | Progress | +5 | 1.0x | Yes | Forces HEARTBEAT |
| ENLIGHTENED | Progress | 0 | 1.0x | Yes | Forces EYES, unlocks ending |
| TOO_LONG | Time | +10 | 1.4x | Yes | - |
| MARATHON | Time | +20 | 1.8x | Yes | Forces MEMORY |
| NIGHT_OWL | Time | +8 | 1.0x | Yes | - |
| DAWN_VISITOR | Time | +2 | 1.0x | No | - |
| POSTED | Interaction | +4 | 1.0x | Yes | Sets has_posted |
| THREAD_CREATOR | Interaction | +8 | 1.0x | Yes | Forces NEW_POST |
| FOUND_HIDDEN | Special | +15 | 2.0x | Yes | Unlocks "void" |
| PATTERN_SEEKER | Special | +10 | 1.0x | Yes | Forces MEMORY |

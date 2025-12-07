# Cursed Board API Documentation

## Base URL

```
http://localhost:8000/api
```

All API endpoints are prefixed with `/api` except for WebSocket and admin endpoints.

## Authentication

The API uses JWT (JSON Web Token) based authentication with Bearer tokens.

### How Authentication Works

1. Create a user account via `POST /api/users`
2. Obtain a JWT token (login endpoint to be implemented)
3. Include the token in the `Authorization` header for protected endpoints:
   ```
   Authorization: Bearer <your-jwt-token>
   ```

### Token Details

- **Algorithm**: HS256
- **Expiration**: 1440 minutes (24 hours) by default
- **Token Payload**: Contains user ID in the `sub` field

### Protected Endpoints

The following endpoints require authentication:
- `POST /api/threads` - Create thread
- `POST /api/posts` - Create post
- `PUT /api/posts/{post_id}` - Update post
- `DELETE /api/posts/{post_id}` - Delete post

## API Endpoints

### Users

#### Create User

```http
POST /api/users
```

Create a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "created_at": "2025-12-08T12:00:00"
}
```

**Errors:**
- `409 Conflict` - Username already exists
- `400 Bad Request` - Failed to create user

#### Get User by ID

```http
GET /api/users/{user_id}
```

Retrieve user information by ID.

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "created_at": "2025-12-08T12:00:00"
}
```

**Errors:**
- `404 Not Found` - User not found

### Boards

#### Get All Boards

```http
GET /api/boards
```

Get all visible boards (excludes hidden boards).

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "slug": "general",
    "name": "General",
    "description": "General discussion",
    "is_hidden": false,
    "created_at": "2025-12-08T12:00:00"
  }
]
```

#### Get Board by ID

```http
GET /api/boards/{board_id}
```

Retrieve a specific board by ID.

**Response:** `200 OK`
```json
{
  "id": 1,
  "slug": "general",
  "name": "General",
  "description": "General discussion",
  "is_hidden": false,
  "created_at": "2025-12-08T12:00:00"
}
```

**Errors:**
- `404 Not Found` - Board not found

#### Get Board by Slug

```http
GET /api/boards/slug/{slug}
```

Retrieve a specific board by its slug.

**Response:** `200 OK`
```json
{
  "id": 1,
  "slug": "general",
  "name": "General",
  "description": "General discussion",
  "is_hidden": false,
  "created_at": "2025-12-08T12:00:00"
}
```

**Errors:**
- `404 Not Found` - Board not found

#### Create Board

```http
POST /api/boards
```

Create a new board.

**Request Body:**
```json
{
  "slug": "string",
  "name": "string",
  "description": "string",
  "is_hidden": false,
  "unlock_trigger": "trigger_name"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "slug": "general",
  "name": "General",
  "description": "General discussion",
  "is_hidden": false,
  "created_at": "2025-12-08T12:00:00"
}
```

**Errors:**
- `409 Conflict` - Board with this slug already exists

#### Update Board

```http
PUT /api/boards/{board_id}
```

Update an existing board.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "is_hidden": false,
  "unlock_trigger": "trigger_name"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "slug": "general",
  "name": "Updated Name",
  "description": "Updated description",
  "is_hidden": false,
  "created_at": "2025-12-08T12:00:00"
}
```

**Errors:**
- `404 Not Found` - Board not found

#### Delete Board

```http
DELETE /api/boards/{board_id}
```

Delete a board.

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Board not found

### Threads

#### Get Threads by Board

```http
GET /api/threads/board/{board_id}?limit=20&offset=0
```

Get all threads in a specific board with pagination.

**Query Parameters:**
- `limit` (optional): Maximum number of threads to return (default: 20, max: 100)
- `offset` (optional): Number of threads to skip (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "board_id": 1,
    "title": "Thread Title",
    "created_at": "2025-12-08T12:00:00",
    "updated_at": "2025-12-08T12:30:00",
    "is_sticky": false,
    "is_locked": false,
    "anomaly_level": 0,
    "post_count": 5,
    "last_post_at": "2025-12-08T12:30:00"
  }
]
```

**Errors:**
- `404 Not Found` - Board not found

#### Get Thread by ID

```http
GET /api/threads/{thread_id}
```

Retrieve a specific thread.

**Response:** `200 OK`
```json
{
  "id": 1,
  "board_id": 1,
  "title": "Thread Title",
  "created_at": "2025-12-08T12:00:00",
  "updated_at": "2025-12-08T12:30:00",
  "is_sticky": false,
  "is_locked": false,
  "anomaly_level": 0
}
```

**Errors:**
- `404 Not Found` - Thread not found

#### Get Thread Posts

```http
GET /api/threads/{thread_id}/posts?limit=100&offset=0
```

Get all posts in a thread with pagination.

**Query Parameters:**
- `limit` (optional): Maximum number of posts to return (default: 100, max: 500)
- `offset` (optional): Number of posts to skip (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "thread_id": 1,
    "user_id": 1,
    "content": "Post content",
    "created_at": "2025-12-08T12:00:00",
    "updated_at": "2025-12-08T12:00:00",
    "is_anomaly": false,
    "anomaly_type": null
  }
]
```

**Errors:**
- `404 Not Found` - Thread not found

#### Create Thread

```http
POST /api/threads
```

Create a new thread. **Requires authentication.**

**Request Body:**
```json
{
  "board_id": 1,
  "title": "Thread Title"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "board_id": 1,
  "title": "Thread Title",
  "created_at": "2025-12-08T12:00:00",
  "updated_at": "2025-12-08T12:00:00",
  "is_sticky": false,
  "is_locked": false,
  "anomaly_level": 0
}
```

**Errors:**
- `404 Not Found` - Board not found
- `403 Forbidden` - Cannot create thread in hidden board
- `401 Unauthorized` - Authentication required

#### Update Thread

```http
PUT /api/threads/{thread_id}
```

Update a thread's properties.

**Request Body:**
```json
{
  "title": "Updated Title",
  "is_sticky": true,
  "is_locked": false
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "board_id": 1,
  "title": "Updated Title",
  "created_at": "2025-12-08T12:00:00",
  "updated_at": "2025-12-08T12:30:00",
  "is_sticky": true,
  "is_locked": false,
  "anomaly_level": 0
}
```

**Errors:**
- `404 Not Found` - Thread not found

#### Delete Thread

```http
DELETE /api/threads/{thread_id}
```

Delete a thread and all its posts.

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Thread not found

### Posts

#### Get Post by ID

```http
GET /api/posts/{post_id}
```

Retrieve a specific post.

**Response:** `200 OK`
```json
{
  "id": 1,
  "thread_id": 1,
  "user_id": 1,
  "content": "Post content",
  "created_at": "2025-12-08T12:00:00",
  "updated_at": "2025-12-08T12:00:00",
  "is_anomaly": false,
  "anomaly_type": null
}
```

**Errors:**
- `404 Not Found` - Post not found

#### Get Posts by User

```http
GET /api/posts/user/{user_id}?limit=20&offset=0
```

Get all posts by a specific user.

**Query Parameters:**
- `limit` (optional): Maximum number of posts to return (default: 20, max: 100)
- `offset` (optional): Number of posts to skip (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "thread_id": 1,
    "user_id": 1,
    "content": "Post content",
    "created_at": "2025-12-08T12:00:00",
    "updated_at": "2025-12-08T12:00:00",
    "is_anomaly": false,
    "anomaly_type": null
  }
]
```

#### Create Post

```http
POST /api/posts
```

Create a new post in a thread. **Requires authentication.**

**Request Body:**
```json
{
  "thread_id": 1,
  "content": "Post content"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "thread_id": 1,
  "user_id": 1,
  "content": "Post content",
  "created_at": "2025-12-08T12:00:00",
  "updated_at": "2025-12-08T12:00:00",
  "is_anomaly": false,
  "anomaly_type": null
}
```

**Errors:**
- `404 Not Found` - Thread not found
- `403 Forbidden` - Thread is locked
- `401 Unauthorized` - Authentication required

#### Update Post

```http
PUT /api/posts/{post_id}
```

Update a post's content. **Requires authentication.** Users can only edit their own posts.

**Request Body:**
```json
{
  "content": "Updated content"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "thread_id": 1,
  "user_id": 1,
  "content": "Updated content",
  "created_at": "2025-12-08T12:00:00",
  "updated_at": "2025-12-08T12:30:00",
  "is_anomaly": false,
  "anomaly_type": null
}
```

**Errors:**
- `404 Not Found` - Post not found
- `403 Forbidden` - You can only edit your own posts
- `401 Unauthorized` - Authentication required

#### Delete Post

```http
DELETE /api/posts/{post_id}
```

Delete a post. **Requires authentication.** Users can only delete their own posts.

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Post not found
- `403 Forbidden` - You can only delete your own posts
- `401 Unauthorized` - Authentication required

## WebSocket Protocol

### Connection

```
ws://localhost:8000/ws/ritual?fp={fingerprint}
```

Establish a WebSocket connection for real-time anomaly delivery.

**Query Parameters:**
- `fp` (optional): User fingerprint for identification

**Alternative Identification:**
- Cookie: `ritual_id` - Used if fingerprint is not provided

**Connection Flow:**
1. Client connects with fingerprint or cookie
2. Server validates user identification
3. Server accepts connection and sends welcome message
4. Server starts listening for anomalies in user's queue
5. Client must send heartbeat messages to keep connection alive

### Client Messages

#### Ping

```json
{
  "type": "ping"
}
```

Ping the server to check connection. Server responds with pong.

#### Heartbeat

```json
{
  "type": "heartbeat"
}
```

Keep the connection alive. Must be sent within 60 seconds of the last activity to prevent disconnection.

#### Activity Report

```json
{
  "type": "activity",
  "data": {
    "time_spent": 30,
    "viewed_thread": 123,
    "viewed_post": 456
  }
}
```

Report user activity to the Ritual Engine.

**Activity Data Fields:**
- `time_spent` (optional): Time spent on site in seconds
- `viewed_thread` (optional): Thread ID that was viewed
- `viewed_post` (optional): Post ID that was viewed

#### Close

```json
{
  "type": "close"
}
```

Gracefully close the WebSocket connection.

### Server Messages

#### Welcome

```json
{
  "type": "welcome",
  "user_id": "fingerprint_or_cookie_id"
}
```

Sent immediately after connection is established.

#### Pong

```json
{
  "type": "pong"
}
```

Response to a ping message.

#### Anomaly

```json
{
  "type": "anomaly",
  "payload": {
    "id": "uuid-string",
    "anomaly_type": "glitch",
    "severity": "mild",
    "target": "page",
    "post_id": null,
    "thread_id": null,
    "data": {
      "effect": "rgb_split"
    },
    "duration_ms": 500,
    "delay_ms": 0,
    "timestamp": "2025-12-08T12:00:00"
  }
}
```

Anomaly event delivered to the client.

**Anomaly Types:**
- Content: `new_post`, `post_edit`, `post_corrupt`, `post_delete`
- Visual: `glitch`, `flicker`, `static`
- Presence: `presence`, `shadow`, `eyes`
- Audio: `whisper`, `ambient`, `heartbeat`
- UI: `notification`, `cursor`, `scroll`, `typing`
- Meta: `viewer_count`, `recognition`, `memory`

**Severity Levels:**
- `subtle` - Barely noticeable
- `mild` - Noticeable but dismissable
- `moderate` - Clearly abnormal
- `intense` - Disturbing
- `extreme` - Maximum effect

**Target Types:**
- `page` - Whole page effect
- `post` - Specific post (check `post_id`)
- `thread` - Specific thread (check `thread_id`)
- `user` - User-specific
- `cursor` - Cursor effects
- `text` - Text content

### Heartbeat Requirement

Connections will timeout after 60 seconds of inactivity. Clients should send heartbeat messages at least every 30 seconds to maintain the connection.

## Admin Endpoints

Base path: `/admin/ritual`

**Note:** These endpoints should be protected in production.

### State Management

#### Get User State

```http
GET /admin/ritual/state/{user_id}
```

Get a user's current ritual state including progress, viewed content, and triggers.

**Response:** `200 OK`
```json
{
  "state": {
    "user_id": "fingerprint123",
    "progress": 45,
    "viewed_threads": [1, 2, 3],
    "viewed_posts": [1, 2, 3, 4, 5],
    "time_on_site": 1200,
    "first_visit": "2025-12-08T10:00:00",
    "last_activity": "2025-12-08T12:00:00",
    "triggers_hit": ["first_visit", "time_threshold"],
    "known_patterns": {}
  },
  "level": "medium",
  "description": "Иногда происходит странное"
}
```

**Errors:**
- `404 Not Found` - User state not found

#### Reset User State

```http
POST /admin/ritual/state/{user_id}/reset
```

Reset a user's state to initial values.

**Response:** `200 OK`
```json
{
  "message": "State reset successfully",
  "state": {
    "user_id": "fingerprint123",
    "progress": 0,
    "viewed_threads": [],
    "viewed_posts": [],
    "time_on_site": 0,
    "first_visit": "2025-12-08T12:00:00",
    "last_activity": "2025-12-08T12:00:00",
    "triggers_hit": [],
    "known_patterns": {}
  }
}
```

#### Set User Progress

```http
POST /admin/ritual/state/{user_id}/progress
```

Set a user's progress to a specific value.

**Request Body:**
```json
{
  "progress": 75
}
```

**Response:** `200 OK`
```json
{
  "message": "Progress set to 75",
  "state": {
    "user_id": "fingerprint123",
    "progress": 75,
    "viewed_threads": [1, 2, 3],
    "viewed_posts": [1, 2, 3, 4, 5],
    "time_on_site": 1200,
    "first_visit": "2025-12-08T10:00:00",
    "last_activity": "2025-12-08T12:00:00",
    "triggers_hit": ["first_visit"],
    "known_patterns": {}
  },
  "level": "high"
}
```

**Errors:**
- `400 Bad Request` - Progress must be between 0 and 100
- `404 Not Found` - User state not found

#### Delete User State

```http
DELETE /admin/ritual/state/{user_id}
```

Completely delete a user's ritual state.

**Response:** `200 OK`
```json
{
  "message": "State deleted successfully"
}
```

**Errors:**
- `404 Not Found` - User state not found

### Anomaly Control

#### Trigger Anomaly

```http
POST /admin/ritual/anomaly/{user_id}
```

Trigger a specific anomaly for a user. The anomaly will be queued and delivered via WebSocket.

**Request Body:**
```json
{
  "anomaly_type": "glitch",
  "severity": "mild",
  "target_id": null,
  "custom_data": {
    "effect": "custom_effect"
  }
}
```

**Response:** `200 OK`
```json
{
  "message": "Anomaly queued",
  "event": {
    "type": "anomaly",
    "payload": {
      "id": "uuid-string",
      "anomaly_type": "glitch",
      "severity": "mild",
      "target": "page",
      "post_id": null,
      "thread_id": null,
      "data": {
        "effect": "custom_effect"
      },
      "duration_ms": 500,
      "delay_ms": 0,
      "timestamp": "2025-12-08T12:00:00"
    }
  }
}
```

**Errors:**
- `404 Not Found` - User state not found

#### List Anomaly Types

```http
GET /admin/ritual/anomaly/types
```

List all available anomaly types and severity levels.

**Response:** `200 OK`
```json
{
  "types": [
    "new_post", "post_edit", "post_corrupt", "post_delete",
    "glitch", "flicker", "static",
    "presence", "shadow", "eyes",
    "whisper", "ambient", "heartbeat",
    "notification", "cursor", "scroll", "typing",
    "viewer_count", "recognition", "memory"
  ],
  "severities": [
    "subtle", "mild", "moderate", "intense", "extreme"
  ]
}
```

#### Broadcast Anomaly

```http
POST /admin/ritual/broadcast
```

Broadcast an anomaly to all connected users. Use with caution!

**Request Body:**
```json
{
  "anomaly_type": "glitch",
  "severity": "mild",
  "target_id": null,
  "custom_data": {}
}
```

**Response:** `200 OK`
```json
{
  "message": "Anomaly broadcast to 5 users",
  "anomaly_type": "glitch"
}
```

### Information Endpoints

#### Get Active Connections

```http
GET /admin/ritual/connections
```

Get information about active WebSocket connections.

**Response:** `200 OK`
```json
{
  "total_connections": 5,
  "connected_users": [
    "fingerprint123",
    "fingerprint456",
    "fingerprint789"
  ]
}
```

#### Get Progress Levels

```http
GET /admin/ritual/levels
```

Get progress level thresholds and descriptions.

**Response:** `200 OK`
```json
{
  "levels": {
    "low": {
      "range": "0-20",
      "description": "Редкие аномалии"
    },
    "medium": {
      "range": "21-50",
      "description": "Иногда происходит странное"
    },
    "high": {
      "range": "51-80",
      "description": "Они знают о тебе"
    },
    "critical": {
      "range": "81-100",
      "description": "Ты один из нас"
    }
  }
}
```

#### Get Ritual Stats

```http
GET /admin/ritual/stats
```

Get overall ritual system statistics.

**Response:** `200 OK`
```json
{
  "active_connections": 5,
  "total_states": 100,
  "level_distribution": {
    "low": 40,
    "medium": 35,
    "high": 20,
    "critical": 5
  }
}
```

## Error Responses

All API errors follow a standard format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `204 No Content` - Request succeeded with no response body
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Authenticated but not authorized for this action
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists (e.g., duplicate username)
- `422 Unprocessable Entity` - Validation error in request data
- `500 Internal Server Error` - Server error

### Example Error Response

```json
{
  "detail": "User not found"
}
```

For validation errors (422), the response includes detailed field information:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

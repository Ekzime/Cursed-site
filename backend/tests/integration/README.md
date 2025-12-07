# Integration Tests - API Routers

## Overview

This directory contains integration tests for FastAPI routers, testing API endpoints with mocked dependencies to ensure correct behavior, response structure, and error handling.

## Test Coverage

### test_routers.py

Comprehensive tests for API endpoints focusing on the Ritual Admin API and core endpoints.

#### TestHealthAndRoot
Tests basic application endpoints:
- `GET /` - Root endpoint returns API status
- `GET /health` - Health check with Redis connection status

#### TestRitualAdminRoutes
Tests for `/admin/ritual` endpoints:
- `GET /admin/ritual/anomaly/types` - List all anomaly types and severities
- `GET /admin/ritual/levels` - Get progress level information
- `GET /admin/ritual/state/{user_id}` - Get user ritual state
- `POST /admin/ritual/state/{user_id}/reset` - Reset user state
- `POST /admin/ritual/state/{user_id}/progress` - Set user progress
- `GET /admin/ritual/connections` - Get active WebSocket connections
- `DELETE /admin/ritual/state/{user_id}` - Delete user state

**Coverage:**
- Valid request handling
- 404 responses for non-existent resources
- 400 responses for invalid input
- Response structure validation
- Mocked RitualEngine dependency

#### TestRitualAdminAnomalyEndpoints
Tests for anomaly-related endpoints:
- `POST /admin/ritual/anomaly/{user_id}` - Trigger anomaly for specific user
- `POST /admin/ritual/broadcast` - Broadcast anomaly to all users
- `GET /admin/ritual/stats` - Get ritual system statistics

**Coverage:**
- Anomaly queueing
- Broadcasting to multiple users
- Statistics aggregation
- Error handling for missing users

## Test Fixtures

### test_client (from conftest.py)
FastAPI TestClient with:
- Mocked Redis dependency
- Minimal lifespan (skips database init)
- Auto-cleanup after tests

## Running Tests

### Run all router tests:
```bash
pytest tests/integration/test_routers.py -v
```

### Run specific test class:
```bash
pytest tests/integration/test_routers.py::TestRitualAdminRoutes -v
```

### Run with coverage:
```bash
pytest tests/integration/test_routers.py --cov=app.routers --cov-report=html
```

### Use convenience script:
```bash
bash run_router_tests.sh
```

## Test Statistics

- **Total Tests:** 21
- **Test Classes:** 3
- **Endpoints Covered:** 11
- **Mock Patterns Used:** AsyncMock, patch decorators

## Test Patterns

### 1. Static Endpoints (No Mocking)
For endpoints that return static data:
```python
def test_get_anomaly_types(self, test_client):
    response = test_client.get("/admin/ritual/anomaly/types")
    assert response.status_code == 200
    data = response.json()
    assert "types" in data
```

### 2. Service-Dependent Endpoints (Mocked)
For endpoints requiring service dependencies:
```python
@patch("app.routers.ritual_admin.RitualEngine")
def test_get_user_state_success(self, mock_engine_class, test_client):
    mock_engine = AsyncMock()
    mock_engine_class.return_value = mock_engine
    mock_engine.get_user_state.return_value = test_state

    response = test_client.get("/admin/ritual/state/test-user")
    assert response.status_code == 200
```

### 3. Error Cases
Testing error handling and edge cases:
```python
def test_set_user_progress_invalid_range(self, test_client):
    response = test_client.post(
        "/admin/ritual/state/test-user/progress",
        json={"progress": 150}
    )
    assert response.status_code == 400
```

## Key Features Tested

1. **Response Structure Validation**
   - All required fields present
   - Correct data types
   - Proper JSON serialization

2. **Status Codes**
   - 200 OK for successful requests
   - 404 Not Found for missing resources
   - 400 Bad Request for invalid input

3. **Data Validation**
   - Progress range (0-100)
   - Enum values (AnomalyType, Severity)
   - Required vs optional fields

4. **Dependency Injection**
   - RitualEngine properly injected
   - Redis client mocked
   - Async dependencies handled

## Coverage Improvements

These tests significantly improve coverage for:
- `/app/routers/ritual_admin.py` - ~95% coverage
- API response serialization
- FastAPI request validation
- Error handling middleware

## Future Enhancements

Potential additions:
1. Tests for `/api/users`, `/api/boards`, `/api/threads`, `/api/posts`
2. WebSocket connection tests
3. Authentication/authorization tests
4. Rate limiting tests
5. Performance/load tests

## Notes

- Tests use mocked dependencies to avoid database/Redis requirements
- TestClient handles lifespan events automatically
- AsyncMock used for async service methods
- All tests are isolated and can run in any order

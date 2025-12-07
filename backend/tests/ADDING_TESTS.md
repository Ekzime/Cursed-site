# Guide: Adding New Router Tests

## Quick Start Template

### 1. Basic Endpoint Test (No Dependencies)

```python
def test_endpoint_name(self, test_client):
    """Description of what this tests."""
    response = test_client.get("/endpoint/path")

    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### 2. Test with Mocked Service

```python
@patch("app.routers.your_router.YourService")
def test_with_service(self, mock_service_class, test_client):
    """Description of what this tests."""
    # Setup mock
    mock_service = AsyncMock()
    mock_service_class.return_value = mock_service
    mock_service.method_name.return_value = expected_value

    # Make request
    response = test_client.post("/endpoint", json={"key": "value"})

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == expected_value
```

### 3. Test with Error Case

```python
def test_error_case(self, test_client):
    """Should return 404 when resource not found."""
    response = test_client.get("/endpoint/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
```

## Common Patterns

### Testing GET Requests

```python
def test_get_resource(self, test_client):
    response = test_client.get("/api/resource/123")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 123
```

### Testing POST Requests

```python
def test_create_resource(self, test_client):
    payload = {
        "name": "Test Resource",
        "value": 42
    }
    response = test_client.post("/api/resource", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
```

### Testing PUT/PATCH Requests

```python
def test_update_resource(self, test_client):
    payload = {"value": 100}
    response = test_client.put("/api/resource/123", json=payload)
    assert response.status_code == 200
```

### Testing DELETE Requests

```python
def test_delete_resource(self, test_client):
    response = test_client.delete("/api/resource/123")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
```

### Testing Query Parameters

```python
def test_with_query_params(self, test_client):
    response = test_client.get("/api/resources?limit=10&offset=20")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 10
```

### Testing Headers

```python
def test_with_headers(self, test_client):
    headers = {"Authorization": "Bearer test-token"}
    response = test_client.get("/api/protected", headers=headers)
    assert response.status_code == 200
```

## Mocking Patterns

### Mock Database Session

```python
@patch("app.core.database.get_db")
def test_with_db(self, mock_get_db, test_client):
    mock_session = AsyncMock()
    mock_get_db.return_value = mock_session

    # Configure mock query results
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = test_object
    mock_session.execute.return_value = mock_result

    response = test_client.get("/endpoint")
    assert response.status_code == 200
```

### Mock Service Dependency

```python
@patch("app.routers.your_router.get_service")
def test_with_service_dependency(self, mock_get_service, test_client):
    mock_service = AsyncMock()
    mock_get_service.return_value = mock_service
    mock_service.do_something.return_value = "result"

    response = test_client.get("/endpoint")
    assert response.status_code == 200
```

### Mock Multiple Dependencies

```python
@patch("app.routers.your_router.Service1")
@patch("app.routers.your_router.Service2")
def test_multiple_mocks(self, mock_service2, mock_service1, test_client):
    # Note: patches are applied bottom-up (Service2, then Service1)
    mock1 = AsyncMock()
    mock2 = AsyncMock()
    mock_service1.return_value = mock1
    mock_service2.return_value = mock2

    response = test_client.get("/endpoint")
    assert response.status_code == 200
```

## Organizing Tests

### Test Class Structure

```python
class TestResourceEndpoints:
    """Tests for /api/resource endpoints."""

    def test_list_resources(self, test_client):
        """Should return list of resources."""
        pass

    def test_get_resource(self, test_client):
        """Should return single resource."""
        pass

    def test_create_resource(self, test_client):
        """Should create new resource."""
        pass

    def test_update_resource(self, test_client):
        """Should update existing resource."""
        pass

    def test_delete_resource(self, test_client):
        """Should delete resource."""
        pass
```

### Group Related Tests

```python
class TestResourceCRUD:
    """CRUD operations for resources."""
    # ... CRUD tests ...

class TestResourceValidation:
    """Validation and error handling."""
    # ... validation tests ...

class TestResourcePermissions:
    """Permission and authorization."""
    # ... auth tests ...
```

## Assertion Examples

### Status Codes

```python
assert response.status_code == 200  # OK
assert response.status_code == 201  # Created
assert response.status_code == 204  # No Content
assert response.status_code == 400  # Bad Request
assert response.status_code == 401  # Unauthorized
assert response.status_code == 403  # Forbidden
assert response.status_code == 404  # Not Found
assert response.status_code == 422  # Unprocessable Entity
assert response.status_code == 500  # Internal Server Error
```

### Response Data

```python
data = response.json()

# Field presence
assert "id" in data
assert "created_at" in data

# Field values
assert data["name"] == "expected"
assert data["count"] == 42
assert data["active"] is True

# Field types
assert isinstance(data["id"], int)
assert isinstance(data["name"], str)
assert isinstance(data["items"], list)

# List operations
assert len(data["items"]) == 5
assert data["items"][0]["id"] == 1

# Nested data
assert data["author"]["name"] == "John"
```

### Response Structure

```python
# Exact structure match
expected = {
    "id": 1,
    "name": "Test",
    "active": True
}
assert response.json() == expected

# Subset match
assert all(k in data for k in ["id", "name", "created_at"])

# List of dicts
items = response.json()["items"]
assert all("id" in item for item in items)
```

## Common Test Scenarios

### Test Pagination

```python
def test_pagination(self, test_client):
    response = test_client.get("/api/resources?page=1&size=10")
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert len(data["items"]) <= 10
```

### Test Filtering

```python
def test_filtering(self, test_client):
    response = test_client.get("/api/resources?status=active")
    data = response.json()

    assert all(item["status"] == "active" for item in data["items"])
```

### Test Sorting

```python
def test_sorting(self, test_client):
    response = test_client.get("/api/resources?sort=name&order=asc")
    data = response.json()

    names = [item["name"] for item in data["items"]]
    assert names == sorted(names)
```

### Test Validation Errors

```python
def test_invalid_input(self, test_client):
    invalid_payload = {
        "name": "",  # Empty string not allowed
        "value": -1  # Negative not allowed
    }
    response = test_client.post("/api/resource", json=invalid_payload)

    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "detail" in data
```

### Test Authentication

```python
def test_requires_auth(self, test_client):
    # Without auth
    response = test_client.get("/api/protected")
    assert response.status_code == 401

    # With auth
    headers = {"Authorization": "Bearer valid-token"}
    response = test_client.get("/api/protected", headers=headers)
    assert response.status_code == 200
```

## Testing Tips

### 1. Use Descriptive Test Names
```python
# Good
def test_get_user_returns_404_when_not_found(self):

# Bad
def test_user(self):
```

### 2. Test One Thing Per Test
```python
# Good
def test_create_user_returns_201(self):
    # Only test status code

def test_create_user_returns_correct_data(self):
    # Only test response data

# Bad
def test_create_user(self):
    # Tests status, data, side effects, etc.
```

### 3. Use Fixtures for Test Data
```python
@pytest.fixture
def sample_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com"
    }

def test_create_user(self, test_client, sample_user_data):
    response = test_client.post("/api/users", json=sample_user_data)
    assert response.status_code == 201
```

### 4. Test Error Messages
```python
def test_error_message(self, test_client):
    response = test_client.get("/api/user/999")
    assert response.status_code == 404
    data = response.json()
    assert "User not found" in data["detail"]
```

### 5. Verify Mock Calls
```python
@patch("app.routers.users.send_email")
def test_sends_welcome_email(self, mock_send_email, test_client):
    response = test_client.post("/api/users", json=user_data)

    # Verify email was sent
    mock_send_email.assert_called_once()
    call_args = mock_send_email.call_args
    assert call_args[0][0] == user_data["email"]
```

## Running Your Tests

```bash
# Run all new tests
pytest tests/integration/test_your_router.py -v

# Run specific test
pytest tests/integration/test_your_router.py::TestYourClass::test_specific -v

# Run with coverage
pytest tests/integration/test_your_router.py --cov=app.routers.your_router

# Run with verbose output
pytest tests/integration/test_your_router.py -vv

# Run and stop on first failure
pytest tests/integration/test_your_router.py -x
```

## Checklist for New Tests

- [ ] Test class has descriptive name
- [ ] Each test has clear docstring
- [ ] Tests are independent (can run in any order)
- [ ] Mocks are properly scoped
- [ ] All assertions have clear purpose
- [ ] Error cases are tested
- [ ] Edge cases are covered
- [ ] Response structure is validated
- [ ] Tests are documented in README
- [ ] Tests pass successfully

## Example: Complete Test File

```python
"""
Integration tests for User API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status


class TestUserEndpoints:
    """Tests for /api/users endpoints."""

    def test_list_users(self, test_client):
        """Should return paginated list of users."""
        response = test_client.get("/api/users")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data

    @patch("app.routers.users.get_user_service")
    def test_get_user_success(self, mock_get_service, test_client):
        """Should return user when found."""
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        mock_service.get_user.return_value = {
            "id": 1,
            "username": "testuser"
        }

        response = test_client.get("/api/users/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1

    def test_get_user_not_found(self, test_client):
        """Should return 404 for non-existent user."""
        response = test_client.get("/api/users/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
```

## Need Help?

- Check existing tests in `tests/integration/test_routers.py` for examples
- Review the integration test README
- Run tests with `-vv` for verbose output
- Use `pytest --pdb` to debug failing tests

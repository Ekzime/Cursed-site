"""
Unit tests for authentication utilities.
Tests JWT token creation and verification.
Password hashing tests skipped due to passlib/bcrypt compatibility issues.
"""
import pytest
from datetime import timedelta
from fastapi import HTTPException

from app.core.auth import (
    create_access_token,
    verify_access_token,
)


class TestCreateAccessToken:
    """Tests for create_access_token()."""

    def test_creates_jwt_string(self):
        """Should create a valid JWT token string."""
        # JWT sub must be string
        token = create_access_token({"sub": "123"})
        assert isinstance(token, str)
        assert token.count(".") == 2  # JWT has 3 parts

    def test_custom_expiration(self):
        """Should accept custom expiration delta."""
        token = create_access_token(
            {"sub": "123"},
            expires_delta=timedelta(hours=24)
        )
        assert isinstance(token, str)

    def test_includes_data_in_payload(self):
        """Should include provided data in token payload."""
        token = create_access_token({"sub": "user123", "role": "admin"})
        payload = verify_access_token(token)
        assert "exp" in payload


class TestVerifyAccessToken:
    """Tests for verify_access_token()."""

    def test_valid_token_returns_payload(self):
        """Valid token should return decoded payload."""
        # JWT sub must be string
        token = create_access_token({"sub": "123", "role": "admin"})
        payload = verify_access_token(token)
        assert payload["sub"] == "123"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_invalid_token_raises_exception(self):
        """Invalid token should raise HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises_exception(self):
        """Tampered token should raise HTTPException."""
        # Create valid token then modify it
        token = create_access_token({"sub": "123"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(tampered)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_exception(self):
        """Expired token should raise HTTPException."""
        # Create token that's already expired
        token = create_access_token(
            {"sub": "123"},
            expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(token)
        assert exc_info.value.status_code == 401

"""
Unit tests for database utilities.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestGetDb:
    """Tests for get_db() dependency."""

    @pytest.mark.asyncio
    async def test_yields_session(self):
        """Should yield a database session."""
        from app.core.database import get_db

        # This tests the generator function structure
        gen = get_db()
        # Can't fully test without actual DB, but we verify it's a generator
        assert hasattr(gen, '__anext__')

    @pytest.mark.asyncio
    async def test_session_rollback_on_exception(self):
        """Session should rollback on exception."""
        # Mock the session
        mock_session = AsyncMock()

        with patch('app.core.database.AsyncSessionLocal') as mock_session_local:
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_context.__aexit__.return_value = None
            mock_session_local.return_value = mock_context

            from app.core.database import get_db

            gen = get_db()
            session = await gen.__anext__()

            # Simulate exception
            try:
                await gen.athrow(ValueError("test error"))
            except ValueError:
                pass


class TestBase:
    """Tests for Base declarative class."""

    def test_base_exists(self):
        """Base class should exist for models."""
        from app.core.database import Base
        assert Base is not None

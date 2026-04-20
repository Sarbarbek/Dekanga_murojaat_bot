"""
db.py uchun unit testlar (mock bilan, haqiqiy DB shart emas).
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.db import Database, get_now_utc5


# ─── get_now_utc5 ─────────────────────────────────────────────────────────────

class TestGetNowUtc5:
    def test_returns_string(self):
        result = get_now_utc5()
        assert isinstance(result, str)

    def test_format_is_correct(self):
        """Format: YYYY-MM-DD HH:MM:SS"""
        result = get_now_utc5()
        # Bu format strptime bilan tekshiriladi
        dt = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        assert dt is not None


# ─── Database.__init__ ────────────────────────────────────────────────────────

class TestDatabaseInit:
    def test_initial_pool_is_none(self):
        db = Database(host="localhost", user="u", password="p", db="d", port=5432)
        assert db.pool is None

    def test_stores_connection_params(self):
        db = Database(host="myhost", user="myuser", password="mypass", db="mydb", port=1234)
        assert db._host == "myhost"
        assert db._user == "myuser"
        assert db._password == "mypass"
        assert db._db == "mydb"
        assert db._port == 1234


# ─── Database._get_pool ───────────────────────────────────────────────────────

class TestGetPool:
    def test_raises_if_pool_not_initialized(self):
        db = Database(host="h", user="u", password="p", db="d")
        with pytest.raises(RuntimeError, match="init"):
            db._get_pool()

    def test_returns_pool_when_set(self):
        db = Database(host="h", user="u", password="p", db="d")
        mock_pool = MagicMock()
        db.pool = mock_pool
        assert db._get_pool() is mock_pool


# ─── Database.create_murojaat ────────────────────────────────────────────────

class TestCreateMurojaat:
    @pytest.mark.asyncio
    async def test_create_returns_id(self):
        db = Database(host="h", user="u", password="p", db="d")

        # Connection mock
        mock_row = {"id": 42}
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        result = await db.create_murojaat(
            user_id=1,
            full_name="Test User",
            passport="AA1234567",
            phone="+998901234567",
            group_name="ISE_N-23UA",
            department_key="kun",
            body_text="Test murojaat",
            file_id=None,
            file_type="text",
        )
        assert result == 42

    @pytest.mark.asyncio
    async def test_create_calls_fetchrow(self):
        db = Database(host="h", user="u", password="p", db="d")

        mock_row = {"id": 1}
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        await db.create_murojaat(
            user_id=5,
            full_name="Ali Valiyev",
            passport="BB9876543",
            phone="+99890",
            group_name="MPFS_N-23UA",
            department_key="mag",
            body_text="Murojaat matni",
            file_id="file123",
            file_type="photo",
        )
        mock_conn.fetchrow.assert_called_once()


# ─── Database.set_answer ──────────────────────────────────────────────────────

class TestSetAnswer:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        db = Database(host="h", user="u", password="p", db="d")

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        result = await db.set_answer(
            appeal_id=1, answer_text="Javob berildi", answered_by=100
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_updated(self):
        db = Database(host="h", user="u", password="p", db="d")

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 0")

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        result = await db.set_answer(
            appeal_id=999, answer_text="Javob", answered_by=100
        )
        assert result is False


# ─── Database.get_murojaat_info ───────────────────────────────────────────────

class TestGetMurojaatInfo:
    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self):
        db = Database(host="h", user="u", password="p", db="d")

        mock_row = MagicMock()
        mock_row.__iter__ = MagicMock(return_value=iter([("user_id", 5), ("department_key", "kun")]))
        mock_row.keys = MagicMock(return_value=["user_id", "department_key"])

        # asyncpg row ni dict() ga o'girish uchun
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"user_id": 5, "department_key": "kun"})

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        result = await db.get_murojaat_info(1)
        assert result is not None
        assert result["user_id"] == 5
        assert result["department_key"] == "kun"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        db = Database(host="h", user="u", password="p", db="d")

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        result = await db.get_murojaat_info(9999)
        assert result is None


# ─── Database.export_murojaatlar ─────────────────────────────────────────────

class TestExportMurojaatlar:
    @pytest.mark.asyncio
    async def test_all_status_no_condition(self):
        """status='all' bo'lganda WHERE status qo'shilmasligi kerak."""
        db = Database(host="h", user="u", password="p", db="d")

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        result = await db.export_murojaatlar(status="all", department_key="total")
        # status='all' + total => WHERE bo'lmaydi
        call_query = mock_conn.fetch.call_args[0][0]
        assert "WHERE" not in call_query
        assert result == []

    @pytest.mark.asyncio
    async def test_new_status_adds_condition(self):
        db = Database(host="h", user="u", password="p", db="d")

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        await db.export_murojaatlar(status="new", department_key="total")
        call_query = mock_conn.fetch.call_args[0][0]
        assert "WHERE" in call_query

    @pytest.mark.asyncio
    async def test_order_by_id_asc(self):
        """Eksport ORDER BY id ASC bo'lishi kerak."""
        db = Database(host="h", user="u", password="p", db="d")

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextMock(mock_conn))
        db.pool = mock_pool

        await db.export_murojaatlar(status="all")
        call_query = mock_conn.fetch.call_args[0][0]
        assert "ORDER BY id ASC" in call_query


# ─── Helper: async context manager ────────────────────────────────────────────

class AsyncContextMock:
    """asyncpg pool.acquire() uchun async context manager mock."""
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        pass

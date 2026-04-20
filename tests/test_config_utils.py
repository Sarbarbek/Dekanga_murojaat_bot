"""
config.py va utils.py uchun unit testlar.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch

from app.config import _parse_ids, Settings
from app.utils import get_admin_role, is_admin, is_super_admin
from tests.conftest import make_settings


# ─── _parse_ids ───────────────────────────────────────────────────────────────

class TestParseIds:
    def test_single_id(self):
        assert _parse_ids("123") == [123]

    def test_multiple_ids(self):
        result = _parse_ids("1, 2, 3")
        assert sorted(result) == [1, 2, 3]

    def test_empty_string(self):
        assert _parse_ids("") == []

    def test_whitespace_only(self):
        assert _parse_ids("  ") == []

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            _parse_ids("abc, 123")

    def test_trailing_comma(self):
        assert _parse_ids("1,2,") == [1, 2]


# ─── is_admin ─────────────────────────────────────────────────────────────────

class TestIsAdmin:
    def setup_method(self):
        self.settings = make_settings(
            super_admin_ids=[100],
            kun_ids=[200],
            kech_ids=[300],
            mag_ids=[400],
        )

    def test_super_admin_is_admin(self):
        assert is_admin(self.settings, 100) is True

    def test_kun_dekan_is_admin(self):
        assert is_admin(self.settings, 200) is True

    def test_kech_dekan_is_admin(self):
        assert is_admin(self.settings, 300) is True

    def test_mag_dekan_is_admin(self):
        assert is_admin(self.settings, 400) is True

    def test_random_user_not_admin(self):
        assert is_admin(self.settings, 999) is False

    def test_zero_id_not_admin(self):
        assert is_admin(self.settings, 0) is False


# ─── is_super_admin ───────────────────────────────────────────────────────────

class TestIsSuperAdmin:
    def setup_method(self):
        self.settings = make_settings(
            super_admin_ids=[100],
            kun_ids=[200],
        )

    def test_super_admin_recognized(self):
        assert is_super_admin(self.settings, 100) is True

    def test_dekan_is_not_super_admin(self):
        assert is_super_admin(self.settings, 200) is False

    def test_unknown_user_is_not_super_admin(self):
        assert is_super_admin(self.settings, 999) is False


# ─── get_admin_role ───────────────────────────────────────────────────────────

class TestGetAdminRole:
    def setup_method(self):
        self.settings = make_settings(
            super_admin_ids=[100],
            kun_ids=[200],
            kech_ids=[300],
            mag_ids=[400],
        )

    def test_super_admin_role_is_total(self):
        assert get_admin_role(self.settings, 100) == "total"

    def test_kun_dekan_role(self):
        assert get_admin_role(self.settings, 200) == "kun"

    def test_kech_dekan_role(self):
        assert get_admin_role(self.settings, 300) == "kech"

    def test_mag_dekan_role(self):
        assert get_admin_role(self.settings, 400) == "mag"

    def test_unknown_role_is_none(self):
        assert get_admin_role(self.settings, 999) is None


# ─── load_settings ────────────────────────────────────────────────────────────

class TestLoadSettings:
    def test_missing_bot_token_raises(self):
        """BOT_TOKEN o'rnatilmagan bo'lsa RuntimeError chiqishi kerak."""
        with patch.dict("os.environ", {
            "BOT_TOKEN": "",
            "ADMIN_IDS": "1",
            "KUN_DEKAN_IDS": "",
            "KECH_DEKAN_IDS": "",
            "MAG_DEKAN_IDS": "",
        }):
            from app.config import load_settings
            with pytest.raises(RuntimeError, match="BOT_TOKEN is not set"):
                load_settings()

    def test_all_admin_ids_merged(self):
        """Barcha admin IDlar (super+dekanlar) birlashtirilishi kerak."""
        with patch.dict("os.environ", {
            "BOT_TOKEN": "some_token",
            "ADMIN_IDS": "1",
            "KUN_DEKAN_IDS": "2",
            "KECH_DEKAN_IDS": "3",
            "MAG_DEKAN_IDS": "4",
            "PGHOST": "localhost",
            "PGUSER": "u",
            "PGPASSWORD": "p",
            "PGDATABASE": "d",
            "PGPORT": "5432",
        }):
            from app.config import load_settings
            s = load_settings()
            assert set(s.admin_ids) == {1, 2, 3, 4}
            assert s.super_admin_ids == [1]

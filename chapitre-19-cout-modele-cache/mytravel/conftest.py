"""Tests run offline: a fake key and a throwaway database."""

import os

import pytest

os.environ["OPENROUTER_API_KEY"] = "test-key"
os.environ["MYTRAVEL_DB"] = ":memory:"


@pytest.fixture(autouse=True)
def empty_cache():
    from app import cache  # after the environment is set
    cache.connection.execute("DELETE FROM cache")

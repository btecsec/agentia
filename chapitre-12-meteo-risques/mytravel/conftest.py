"""Tests run offline: a fake key and a throwaway database."""

import os

os.environ["OPENROUTER_API_KEY"] = "test-key"
os.environ["MYTRAVEL_DB"] = ":memory:"

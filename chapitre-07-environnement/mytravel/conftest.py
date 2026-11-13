"""Tests run offline: a fake key, never sent anywhere."""

import os

os.environ["OPENROUTER_API_KEY"] = "test-key"

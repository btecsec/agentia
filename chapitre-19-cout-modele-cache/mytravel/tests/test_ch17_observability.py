"""Chapter 17: every step is logged and shown."""

import json

from app import web
from app.logs import log


def test_log_is_one_json_line(capsys):
    log("search", query="visa", results=2)
    line = json.loads(capsys.readouterr().out)
    assert line["event"] == "search" and line["results"] == 2
    assert line["severity"] == "INFO"


def test_search_is_logged(monkeypatch, capsys):
    monkeypatch.setattr(web, "search_engine", lambda q, d: [])
    web.search_web("visa Pérou", ["gouv.fr"])
    assert '"event": "search"' in capsys.readouterr().out

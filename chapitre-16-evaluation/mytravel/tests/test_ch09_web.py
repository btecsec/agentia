"""Chapter 9: official sources only, and a failure is not a crash."""

import pytest

from app import tools, web
from app.sources import OFFICIAL

AD = {"title": "Visa fast", "url": "https://www.bing.com/aclick?x=1",
      "snippet": "Buy"}
GOV = {"title": "Japon", "snippet": "Passeport valide",
       "url": "https://www.diplomatie.gouv.fr/fr/japon/"}


def test_is_allowed_subdomain_yes_lookalike_no():
    domains = ["diplomatie.gouv.fr"]
    assert web.is_allowed("https://www.diplomatie.gouv.fr/a", domains)
    assert not web.is_allowed(
        "https://diplomatie.gouv.fr.evil.com/a", domains)
    assert not web.is_allowed("http://www.diplomatie.gouv.fr/", domains)


def test_government_sites_are_official():
    assert web.is_allowed("https://www.mofa.go.jp/visa.html",
                          OFFICIAL["entry"])


def test_search_keeps_allowed_sites_only(monkeypatch):
    monkeypatch.setattr(web, "search_engine", lambda q, d: [AD, GOV])
    found = web.search_web("visa Japon", OFFICIAL["entry"])
    assert [r["url"] for r in found] == [GOV["url"]]


def test_search_failure_returns_empty(monkeypatch):
    def broken(query, domains):
        raise RuntimeError("engine down")
    monkeypatch.setattr(web, "search_engine", broken)
    assert web.search_web("visa", OFFICIAL["entry"]) == []


def test_read_page_refuses_other_site():
    with pytest.raises(ValueError):
        web.read_page("https://example.com/", OFFICIAL["entry"])


def test_search_official_says_when_nothing_found(monkeypatch):
    monkeypatch.setattr(web, "search_engine", lambda q, d: [])
    answer = tools.search_official.invoke(
        {"topic": "entry", "query": "visa Japon"})
    assert "No official source" in answer


def test_a_broken_url_is_never_allowed():
    assert not web.is_allowed("https://[diplomatie.gouv.fr/x",
                              ["diplomatie.gouv.fr"])

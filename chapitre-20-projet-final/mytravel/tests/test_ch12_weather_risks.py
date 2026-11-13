"""Chapter 12: live weather, official travel advice, and the
same tools served to other agents over MCP."""

import asyncio
from datetime import date, timedelta

import httpx
from mcp import Client

from app import tools
from mcp_server import server

TOKYO = {"results": [{"name": "Tokyo", "country": "Japon",
                      "latitude": 35.69, "longitude": 139.69}]}
DAYS = {"daily": {"time": ["d1"], "temperature_2m_min": [8.0],
                  "temperature_2m_max": [14.0],
                  "precipitation_sum": [2.1]}}


def fake_get(calls):
    def get(url, params=None, **kwargs):
        calls.append(url)
        body = TOKYO if "geocoding" in url else DAYS
        return httpx.Response(200, json=body,
                              request=httpx.Request("GET", url))
    return get


def trip_in(days):
    start = date.today() + timedelta(days=days)
    return {"city": "Tokyo", "start": str(start),
            "end": str(start + timedelta(days=3))}


def test_weather_soon_uses_the_forecast(monkeypatch):
    calls = []
    monkeypatch.setattr(tools.httpx, "get", fake_get(calls))
    answer = tools.weather.invoke(trip_in(2))
    assert "api.open-meteo.com" in calls[-1]
    assert "8 to 14 °C" in answer


def test_weather_far_away_uses_last_year(monkeypatch):
    calls = []
    monkeypatch.setattr(tools.httpx, "get", fake_get(calls))
    answer = tools.weather.invoke(trip_in(90))
    assert "archive-api.open-meteo.com" in calls[-1]
    assert "last year" in answer


def test_travel_advice_reads_diplomatie(monkeypatch):
    page = {"url": "https://www.diplomatie.gouv.fr/fr/japon/",
            "title": "Japon", "snippet": ""}
    monkeypatch.setattr(tools, "search_web", lambda q, d: [page])
    monkeypatch.setattr(tools, "read_page",
                        lambda url, d: "Vigilance normale")
    answer = tools.travel_advice.invoke({"country": "Japon"})
    assert "Vigilance normale" in answer
    assert page["url"] in answer


def test_mcp_server_lists_both_tools():
    async def names():
        async with Client(server) as client:  # in-process
            return [t.name for t in (await client.list_tools()).tools]
    assert sorted(asyncio.run(names())) == ["travel_advice",
                                            "weather"]


def test_mcp_client_gets_the_same_weather(monkeypatch):
    monkeypatch.setattr(tools.httpx, "get", fake_get([]))

    async def call():
        async with Client(server) as client:
            return await client.call_tool("weather", trip_in(2))
    result = asyncio.run(call())
    assert "8 to 14 °C" in result.content[0].text

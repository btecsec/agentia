"""The tools of the myTravel agents.

A tool is a Python function the model may decide to call. The
docstring is not decoration: the model reads it to choose.
Everything here is live: the web and the ECB rates.
"""

from urllib.parse import quote, urlencode

import httpx
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool

from app.sources import OFFICIAL
from app.web import read_page, search_web

ALL_OFFICIAL = sorted({d for ds in OFFICIAL.values() for d in ds})


def show(results):
    """Search results as numbered lines the model can cite."""
    return "\n\n".join(
        f"[{n}] {r['title']}\n{r['url']}\n{r['snippet']}"
        for n, r in enumerate(results, start=1))


@wrap_tool_call
def tool_errors(request, handler):
    """Around every tool call: a failure becomes a message.

    A bad date, a site down, a city not found: the model reads
    what went wrong and tries again, instead of the whole answer
    crashing. It is the chapter 1 rule: an error is a text.
    """
    try:
        return handler(request)
    except Exception as error:
        return ToolMessage(f"Tool error: {error}. Fix the call, "
                           "or say you could not find it.",
                           tool_call_id=request.tool_call["id"])


# --- Official information: chapter 9 -----------------------------

@tool
def search_official(topic: str, query: str) -> str:
    """Search official government and health websites.

    topic is one of: entry (visa, passport, entry rules), health
    (vaccines, health risks), baggage (luggage, customs).
    """
    domains = OFFICIAL.get(topic, OFFICIAL["entry"])
    results = search_web(query, domains)
    if not results:
        return "No official source found. Say so; do not guess."
    return show(results)


@tool
def read_official_page(url: str) -> str:
    """Read an official page found by search_official."""
    try:
        return f"{url}\n{read_page(url, ALL_OFFICIAL)}"
    except (ValueError, httpx.HTTPError) as error:
        return f"Could not read {url}: {error}"


# --- Hotels: chapter 10 -------------------------------------------

def booking_url(city, checkin, checkout, adults):
    query = urlencode({"ss": city, "checkin": checkin,
                       "checkout": checkout,
                       "group_adults": adults})
    return f"https://www.booking.com/searchresults.fr.html?{query}"


@tool
def hotel_links(city: str, checkin: str, checkout: str,
                adults: int, hotel: str = "") -> str:
    """A Booking.com search link, prefilled. Dates: YYYY-MM-DD.

    hotel: the name of one hotel, to open that hotel, not the city.
    """
    place = f"{hotel}, {city}" if hotel else city
    return booking_url(place, checkin, checkout, adults)


@tool
def exchange_rate(currency: str) -> str:
    """Today's rate of 1 euro in a currency code (JPY, USD...)."""
    code = currency.upper()
    url = "https://api.frankfurter.dev/v1/latest"
    data = httpx.get(url, params={"base": "EUR", "symbols": code},
                     timeout=15).json()
    if code not in data.get("rates", {}):
        return f"No ECB rate for {code}."
    rate = data["rates"][code]
    return f"1 EUR = {rate} {code} (ECB, {data['date']})"


# --- Flights and cars: chapter 11 ---------------------------------

def flights_url(origin, destination, depart, back, adults):
    trip = (f"Flights from {origin} to {destination} on {depart} "
            f"through {back} for {adults} adults")
    # Google reads the sentence only on its English page: hl=en.
    return ("https://www.google.com/travel/flights?hl=en&q="
            + quote(trip))


def cars_url(city, start, end):
    return f"https://www.kayak.fr/cars/{quote(city)}/{start}/{end}"


@tool
def flight_links(origin: str, destination: str, depart: str,
                 back: str, adults: int) -> str:
    """A Google Flights search link. Dates: YYYY-MM-DD."""
    return flights_url(origin, destination, depart, back, adults)


@tool
def car_links(city: str, start: str, end: str) -> str:
    """A Kayak car rental search link. Dates: YYYY-MM-DD."""
    return cars_url(city, start, end)

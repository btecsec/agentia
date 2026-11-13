"""Real flight offers: chapter 11.

Travelpayouts keeps the fares travelers found on Aviasales these
last days: a real flight, a real seller, a real price, and the
link to buy it. For every day of a month, so it also finds the
nearest days when nobody looked at yours.
"""

import os
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
from langchain_core.tools import tool

PLACES = "https://autocomplete.travelpayouts.com/places2"
FARES = ("https://api.travelpayouts.com/aviasales/v3/"
         "prices_for_dates")
MAX_SHIFT = 10  # days before or after: further is another trip
MAX_GAP = 3  # nights more or fewer, if none has the same number


def city_code(city):
    """The code that covers every airport of a city: PAR."""
    found = httpx.get(PLACES, timeout=15, params={
        "term": city, "locale": "en", "types[]": "city"}).json()
    if not found:
        raise ValueError(f"no airport found for {city}")
    return found[0]["code"]


def fares(origin, destination, depart, back=""):
    """Round trips seen lately; depart is a day or a month."""
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:  # the agent reads this and gives links instead
        raise RuntimeError("no TRAVELPAYOUTS_TOKEN in .env: real "
                           "prices unavailable")
    return httpx.get(FARES, timeout=15, params={
        "origin": city_code(origin),
        "destination": city_code(destination),
        "departure_at": depart, "return_at": back,
        "one_way": "false", "currency": "eur", "sorting": "price",
        "limit": 1000, "token": token}).json()["data"] or []


def months(first, last):
    """Every YYYY-MM from one day to another."""
    found, day = [], first.replace(day=1)
    while day <= last:
        found.append(f"{day:%Y-%m}")
        day = (day + timedelta(days=32)).replace(day=1)
    return found


def around(origin, destination, start, end, shift):
    """Offers that move the whole trip at most shift days, for the
    same number of nights, or the nearest number seen: the
    cheapest of each pair of days, cheapest first."""
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    shift = timedelta(days=min(shift, MAX_SHIFT))
    low = max(first - shift, date.today() + timedelta(days=1))
    seen = [fare for month in months(low, first + shift)
            for fare in fares(origin, destination, month)]
    found = {}
    for fare in sorted(seen, key=lambda f: f["price"]):
        out = date.fromisoformat(fare["departure_at"][:10])
        back = date.fromisoformat(fare["return_at"][:10])
        gap = abs((back - out) - (last - first)).days
        if (low <= out and abs(out - first) <= shift
                and gap <= MAX_GAP):
            found.setdefault((out, back), (gap, fare))
    nearest = min((gap for gap, _ in found.values()), default=0)
    return [fare for gap, fare in found.values() if gap == nearest]


def seen_on(link):
    """The day a traveler saw this price: search_date=21102026."""
    day = parse_qs(urlparse(link).query)["search_date"][0]
    return f"{datetime.strptime(day, '%d%m%Y'):%Y-%m-%d}"


def offer(fare, adults):
    """One fare, as a line the model can quote."""
    # /search/PAR1212LIS16121: the last digit is the travelers.
    path, query = fare["link"].split("?", 1)
    link = f"https://www.aviasales.com{path[:-1]}{adults}?{query}"
    nights = (date.fromisoformat(fare["return_at"][:10])
              - date.fromisoformat(fare["departure_at"][:10])).days
    return (
        f"- {fare['price']} € par adulte, soit "
        f"{fare['price'] * adults} € pour {adults} : aller le "
        f"{fare['departure_at'][:16]} de {fare['origin_airport']}, "
        f"retour le {fare['return_at'][:10]} ({nights} nuits), vol "
        f"{fare['airline']} {fare['flight_number']}, "
        f"escales : {fare['transfers']} à l'aller, "
        f"{fare['return_transfers']} au retour, vendu par "
        f"{fare['gate']}, "
        f"prix vu le {seen_on(fare['link'])}. Réserver : {link}")


@tool
def flight_offers(origin: str, destination: str, depart: str,
                  back: str, adults: int) -> str:
    """Real round-trip offers, cheapest first, each with its
    seller and the link to buy. Dates: YYYY-MM-DD.
    """
    found = fares(origin, destination, depart, back)
    title = "Aviasales, offres réelles à ces dates :"
    if not found:  # nobody looked at these days: the nearest ones
        found = around(origin, destination, depart, back, 3)
        title = ("Aucune offre vue à ces dates exactes. Offres "
                 "réelles les plus proches (départ à 3 jours "
                 "près, durée la plus proche) :")
    if not found:
        return "No offer seen near these dates. Say so."
    return "\n".join([title] + [offer(f, adults)
                                for f in found[:3]])

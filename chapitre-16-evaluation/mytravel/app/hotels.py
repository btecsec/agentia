"""Hotels at today's price: chapter 10.

Xotelo reads TripAdvisor's prices, free and without a key: for a
hotel and two dates, the price of a night, seller by seller
(Booking.com, Agoda, Trip.com...). A real price, never a guess.
"""

import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import httpx
from langchain_core.tools import tool

from app.tools import booking_url
from app.web import search_web

HOTELS = "https://data.xotelo.com/api"
HOTELS_PER_CITY = 5  # the best rated: a choice, not a catalog


def city_key(city):
    """TripAdvisor's code for a city, g189158 for Lisbon: read in
    the addresses of its hotel pages."""
    pages = search_web(f"hôtel {city} avis tripadvisor",
                       ["tripadvisor.com"], max_results=8)
    codes = re.findall(r"Hotel_Review-(g\d+)-",
                       " ".join(page["url"] for page in pages))
    if not codes:
        raise ValueError(f"no TripAdvisor hotel page for {city}")
    return Counter(codes).most_common(1)[0][0]


def best_hotels(city):
    """The best value hotels of a city, rated 4 out of 5 or more."""
    found = httpx.get(f"{HOTELS}/list", timeout=30, params={
        "location_key": city_key(city), "sort": "best_value",
        "limit": 10}).json()["result"]["list"]
    return [hotel for hotel in found
            if hotel["review_summary"]["rating"] >= 4
            ][:HOTELS_PER_CITY]


def rooms(adults):
    return -(-adults // 2)  # two per room, rounded up


def night(hotel, checkin, checkout, adults):
    """The cheapest room for one night on these dates, with its
    seller; None if nobody sells it."""
    found = httpx.get(f"{HOTELS}/rates", timeout=30, params={
        "hotel_key": hotel["key"], "chk_in": checkin,
        "chk_out": checkout, "adults": adults,
        "rooms": rooms(adults), "currency": "EUR"}).json()
    rates = (found["result"] or {}).get("rates") or []
    return min(rates, key=lambda rate: rate["rate"], default=None)


def hotel_text(hotel, rate, checkin, checkout, adults):
    """One hotel and its price, as a line the model can quote."""
    reviews = hotel["review_summary"]
    link = booking_url(hotel["name"], checkin, checkout, adults)
    return (
        f"- {hotel['name']} ({reviews['rating']}/5, "
        f"{reviews['count']} avis) : {rate['rate']} € la nuit "
        f"chez {rate['name']}, {rooms(adults)} chambre(s). "
        f"Avis et vendeurs : {hotel['url']} Sur Booking.com à "
        f"ces dates : {link}")


@tool
def hotel_offers(city: str, checkin: str, checkout: str,
                 adults: int) -> str:
    """The best value hotels of a city, with today's price of a
    night on these dates and its seller. Dates: YYYY-MM-DD.
    """
    hotels = best_hotels(city)
    # One request per hotel: sent together, not one by one.
    with ThreadPoolExecutor() as pool:
        rates = list(pool.map(
            lambda hotel: night(hotel, checkin, checkout, adults),
            hotels))
    lines = [hotel_text(hotel, rate, checkin, checkout, adults)
             for hotel, rate in zip(hotels, rates) if rate]
    if not lines:
        return "No room sold on these dates. Say so."
    return "\n".join(["Prix du jour, une nuit, sur TripAdvisor :"]
                     + lines)

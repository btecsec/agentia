"""Stays, flight and hotel priced together: chapter 20.

The flights of chapter 11 and the hotels of chapter 10, on the
same days, with one total, like a package on a travel website,
on the best days for a traveler who can move. The travel
agencies' own packages are read beside them.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from app import flights, hotels
from app.sources import BOOKING
from app.tools import show
from app.web import search_web

DAYS_PER_STAY = 4  # the pairs of days with the cheapest flights


def shifted(start, end, shift):
    """The days asked, then the whole trip moved: same nights."""
    first = date.fromisoformat(start)
    last = date.fromisoformat(end)
    shift = min(shift, flights.MAX_SHIFT)
    moves = dict.fromkeys([0, -shift, shift, -shift // 2,
                           shift // 2])  # no twice the same move
    tomorrow = date.today() + timedelta(days=1)
    return [(f"{first + timedelta(move)}",
             f"{last + timedelta(move)}") for move in moves
            if first + timedelta(move) >= tomorrow]


def stay(out, back, fare, hotel, adults):
    """A flight, a hotel or both on the same days, and the
    total."""
    nights = (date.fromisoformat(back)
              - date.fromisoformat(out)).days
    found = {"out": out, "back": back, "nights": nights, "total": 0}
    if fare:
        found.update(fare=fare, total=fare["price"] * adults)
    if hotel:
        rate = hotels.night(hotel, out, back, adults)
        if rate is None:  # full on these days: out of the ranking
            return None
        found.update(hotel=hotel, rate=rate)
        found["total"] += (rate["rate"] * hotels.rooms(adults)
                           * nights)
    return found


def stays(trip):
    """Every flight and hotel pair on the cheapest days, the
    cheapest total first."""
    wanted, days = trip["agents"], []
    if "transport" in wanted:  # the days of the cheapest flights
        found = flights.around(trip["origin"], trip["destination"],
                               trip["start"], trip["end"],
                               trip["flexible"])
        days = [(f["departure_at"][:10], f["return_at"][:10], f)
                for f in found[:DAYS_PER_STAY]]
    if not days and "hotel" in wanted:  # no flight: hotels alone
        # Moved only if no flight was asked: else, the days asked.
        shift = 0 if "transport" in wanted else trip["flexible"]
        days = [(*pair, None) for pair in shifted(
            trip["start"], trip["end"], shift)]
    chosen = (hotels.best_hotels(trip["destination"])
              if "hotel" in wanted else [None])
    pairs = [(*day, hotel) for day in days for hotel in chosen]
    # One request per pair: sent together, not one after another.
    with ThreadPoolExecutor() as pool:
        found = pool.map(
            lambda pair: stay(*pair, trip["travelers"]), pairs)
    return sorted(filter(None, found), key=lambda s: s["total"])


def value(stay):
    """Price for quality: euros per point of rating. 500 € at 4.5
    beats 450 € at 4: a better hotel is worth a little more."""
    hotel = stay.get("hotel")
    return stay["total"] / (hotel["review_summary"]["rating"]
                            if hotel else 1)


def choices(found):
    """The cheapest stay of each hotel, best value first: hotels
    to choose from, not the same hotel three times."""
    best = {}
    for stay in found:  # cheapest first: the first one stays
        hotel = stay.get("hotel") or {"key": stay["fare"]["link"]}
        best.setdefault(hotel["key"], stay)
    return sorted(best.values(), key=value)


def stay_text(stay, adults):
    """One stay, as lines the model can quote."""
    lines = [f"- Du {stay['out']} au {stay['back']}, "
             f"{stay['nights']} nuits :"]
    if "fare" in stay:
        lines.append("  Vol " + flights.offer(stay["fare"],
                                              adults)[2:])
    if "hotel" in stay:
        lines.append("  Hôtel " + hotels.hotel_text(
            stay["hotel"], stay["rate"], stay["out"],
            stay["back"], adults)[2:])
    lines.append(f"  Total : {stay['total']} € pour {adults}")
    return "\n".join(lines)


def packages(city):
    """The travel agencies' packages for a city: a catalog price,
    "dès 302 €" a person, not the price on the days asked."""
    return show(search_web(f"séjour {city} vol + hôtel pas cher",
                           BOOKING["packages"], max_results=6))

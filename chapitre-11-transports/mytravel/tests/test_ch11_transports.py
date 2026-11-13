"""Chapter 11: real flight offers, and links for the rest."""

import pytest

from app import flights, tools


def test_flights_url_is_prefilled():
    url = tools.flights_url("Paris", "Tokyo", "2027-03-10",
                            "2027-03-20", 2)
    assert url.startswith("https://www.google.com/travel/flights")
    assert "Tokyo" in url and "2027-03-20" in url
    # In French, Google ignores the sentence and opens its home.
    assert "hl=en" in url and "2%20adults" in url


def test_cars_url_is_prefilled():
    url = tools.cars_url("Lisbonne", "2027-05-02", "2027-05-06")
    assert url == ("https://www.kayak.fr/cars/Lisbonne/"
                   "2027-05-02/2027-05-06")


def fare(leave, back, price):
    return {"departure_at": f"{leave}T08:00:00+01:00",
            "return_at": f"{back}T18:00:00Z", "price": price,
            "origin_airport": "ORY", "airline": "TP",
            "flight_number": 433, "transfers": 0,
            "return_transfers": 0, "gate": "TAP",
            "link": "/search/PAR0305LIS07051?search_date=01042027"}


def test_an_offer_has_its_seller_its_day_and_its_link():
    line = flights.offer(fare("2027-05-03", "2027-05-07", 90), 2)
    assert "180 € pour 2" in line and "vendu par TAP" in line
    assert "prix vu le 2027-04-01" in line
    assert "aviasales.com/search/PAR0305LIS07052?" in line


def test_nearest_offers_stay_in_the_window(monkeypatch):
    seen = [fare("2027-05-03", "2027-05-07", 90),  # kept
            fare("2027-05-03", "2027-05-07", 95),  # same days
            fare("2027-05-20", "2027-05-24", 30),  # too far
            fare("2027-05-03", "2027-05-05", 20),  # shorter
            fare("2027-05-02", "2027-05-06", 150)]  # dates asked
    monkeypatch.setattr(flights, "fares", lambda *a: seen)
    found = flights.around("Paris", "Lisbonne", "2027-05-02",
                           "2027-05-06", 3)
    assert [f["price"] for f in found] == [90, 150]
    # None lasts 4 nights: the nearest length, not nothing.
    seen = [fare("2027-05-03", "2027-05-08", 90),  # 5 nights
            fare("2027-05-02", "2027-05-08", 80),  # 6 nights
            fare("2027-05-02", "2027-05-12", 10)]  # 10 nights
    found = flights.around("Paris", "Lisbonne", "2027-05-02",
                           "2027-05-06", 3)
    assert [f["price"] for f in found] == [90]


def test_no_token_no_price(monkeypatch):
    monkeypatch.delenv("TRAVELPAYOUTS_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="TRAVELPAYOUTS_TOKEN"):
        flights.fares("Paris", "Lisbonne", "2027-05")

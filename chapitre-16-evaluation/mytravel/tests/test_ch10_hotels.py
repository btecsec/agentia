"""Chapter 10: hotels at today's price, with their seller."""

import httpx

from app import hotels, tools


def test_booking_url_is_prefilled():
    url = tools.booking_url("Lisbonne", "2027-05-02", "2027-05-06", 2)
    assert url.startswith("https://www.booking.com/searchresults")
    assert "checkin=2027-05-02" in url and "group_adults=2" in url


def test_a_hotel_link_searches_that_hotel():
    url = tools.hotel_links.invoke({
        "city": "Lisbonne", "checkin": "2027-05-02",
        "checkout": "2027-05-06", "adults": 2,
        "hotel": "My Story Rossio"})
    assert "ss=My+Story+Rossio%2C+Lisbonne" in url


def test_the_city_code_is_read_in_tripadvisor_addresses(
        monkeypatch):
    url = ("https://www.tripadvisor.com/Hotel_Review-g189158-"
           "d1-Reviews-Casa.html")
    monkeypatch.setattr(hotels, "search_web",
                        lambda *a, **k: [{"url": url}] * 2)
    assert hotels.city_key("Lisbonne") == "g189158"


def test_hotel_offers_give_the_price_and_its_seller(monkeypatch):
    monkeypatch.setattr(hotels, "best_hotels", lambda city: [
        {"name": name, "key": name, "url":
         f"https://www.tripadvisor.com/Hotel_Review-g1-{name}",
         "review_summary": {"rating": 4.5, "count": 900}}
        for name in ["Casa", "Full"]])
    monkeypatch.setattr(hotels, "night", lambda hotel, *a: (
        {"name": "Agoda", "rate": 80}
        if hotel["key"] == "Casa" else None))
    answer = hotels.hotel_offers.invoke({
        "city": "Lisbonne", "checkin": "2027-05-02",
        "checkout": "2027-05-06", "adults": 3})
    assert "80 € la nuit chez Agoda, 2 chambre(s)" in answer
    assert "Full" not in answer  # no room: no price, no line


def test_exchange_rate_reads_the_ecb(monkeypatch):
    def get(url, **kwargs):
        assert "frankfurter" in url
        return httpx.Response(200, json={
            "date": "2026-10-26", "rates": {"JPY": 176.15}},
            request=httpx.Request("GET", url))
    monkeypatch.setattr(tools.httpx, "get", get)
    answer = tools.exchange_rate.invoke({"currency": "jpy"})
    assert "176.15 JPY" in answer

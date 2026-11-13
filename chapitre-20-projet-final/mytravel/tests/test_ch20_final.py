"""Chapter 20: flight and hotel priced together, the best value first."""

from app import flights, graph, hotels


def fare(leave, back, price):
    return {"departure_at": f"{leave}T08:00:00+01:00",
            "return_at": f"{back}T18:00:00Z", "price": price,
            "origin_airport": "ORY", "airline": "TP",
            "flight_number": 433, "transfers": 0,
            "return_transfers": 0, "gate": "TAP",
            "link": "/search/PAR0305LIS07051?search_date=01042027"}


def test_stays_rank_total_and_rating(monkeypatch):
    # The node alone, outside a streamed graph: nobody listens.
    monkeypatch.setattr(graph, "get_stream_writer",
                        lambda: lambda text: None)
    # Cheapest flight on the 3rd, but the hotels are dearer then.
    monkeypatch.setattr(flights, "around", lambda *a: [
        fare("2027-05-03", "2027-05-07", 90),
        fare("2027-05-02", "2027-05-06", 150)])
    monkeypatch.setattr(hotels, "best_hotels", lambda city: [
        {"name": name, "key": name, "url":
         f"https://www.tripadvisor.com/Hotel_Review-g1-{name}",
         "review_summary": {"rating": rating, "count": 900}}
        for name, rating in [("Bof", 3.5), ("Casa", 4.5)]])
    monkeypatch.setattr(hotels, "night", lambda h, day, *a: {
        "name": "Agoda", "rate": (200 if day == "2027-05-03"
                                  else 80 if h["key"] == "Casa"
                                  else 70)})
    agency = "https://www.ovoyages.com/lisbonne"
    monkeypatch.setattr(graph, "packages", lambda city: (
        f"[1] Lisbonne dès 211 € /pers. {agency}"))
    trip = {"origin": "Paris", "destination": "Lisbonne",
            "start": "2027-05-01", "end": "2027-05-05",
            "flexible": 3, "travelers": 2,
            "agents": ["transport", "hotel", "weather"]}
    moved = graph.best_stays({"trip": trip})
    # 2 x 150 + 80 x 1 room x 4 nights = 620, against 980.
    # Bof is cheaper, 580, but Casa gives more per euro.
    report = moved["reports"][0][1]
    assert moved["trip"]["start"] == "2027-05-02"
    assert moved["trip"]["agents"] == ["weather"]
    assert report.index("Total : 620 €") < report.index("580 €")
    # The agencies' packages beside the stays, their link allowed.
    assert moved["reports"][1][0] == "packages"
    assert agency in moved["found"]
    # No flight seen: the hotels still priced, on the days asked.
    monkeypatch.setattr(flights, "around", lambda *a: [])
    alone = graph.best_stays({"trip": trip})
    assert alone["trip"]["start"] == "2027-05-01"
    assert alone["trip"]["agents"] == ["transport", "weather"]

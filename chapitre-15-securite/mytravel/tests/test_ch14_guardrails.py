"""Chapter 14: checks on the way in and out, a human says yes."""

import httpx
from fastapi.testclient import TestClient

import server
from app import agents, graph, tools
from app.graph import Trip
from app.guardrails import check_message, clean_answer
from fakes import fake_model, tool_call

DIPLO = "https://www.diplomatie.gouv.fr/fr/japon/"
EVIL = ["https://evil.com", "https://cheap-visa.example.com/x"]

TRIP = Trip(destination="Lisbonne", country="Portugal",
            start="2027-05-02", end="2027-05-06", origin="Paris",
            travelers=2, booking=True)


def test_card_number_is_refused():
    assert check_message("ma carte 4111 1111 1111 1111")
    assert check_message("Un week-end à Rome ?") is None


def test_a_card_hidden_in_more_digits_is_refused():
    assert check_message("code 123 4111 1111 1111 1111")


def test_two_dates_are_not_a_card():
    assert check_message("Porto 2027-05-02 2027-05-06") is None


def test_unknown_links_are_removed():
    text, sources = clean_answer(
        "Voir [ici](https://www.diplomatie.gouv.fr/fr/portugal/) "
        "et [promo](https://cheap-visa.example.com/x).",
        ["https://www.diplomatie.gouv.fr/fr/portugal/", *EVIL])
    assert "cheap-visa" not in text and "promo" in text
    assert sources == ["https://www.diplomatie.gouv.fr/fr/portugal/"]


def test_booking_waits_for_a_yes(monkeypatch):
    model = fake_model(structured=[TRIP])
    monkeypatch.setattr(graph, "get_chat_model", lambda *a: model)
    reply = graph.ask_mytravel("Prépare la réservation", "conv-b1")
    assert "Lisbonne" in reply["confirm"]
    assert reply["answer"] == ""
    *_, done = graph.stream_confirm("conv-b1", True)
    assert "booking.com" in done["answer"]
    assert done["confirm"] is None


def test_a_no_prepares_nothing(monkeypatch):
    model = fake_model(structured=[TRIP])
    monkeypatch.setattr(graph, "get_chat_model", lambda *a: model)
    graph.ask_mytravel("Prépare la réservation", "conv-b2")
    *_, done = graph.stream_confirm("conv-b2", False)
    assert "booking.com" not in done["answer"]


def test_confirm_without_pending_booking_is_404():
    client = TestClient(server.app)
    reply = client.post("/api/confirm", json={
        "conversation": "conv-nothing", "approved": True})
    assert reply.status_code == 404


def test_google_redirects_are_removed():
    text, sources = clean_answer(
        "[vols](https://www.google.com/travel/flights?q=Rome) "
        "[piège](https://www.google.com/url?q=https://evil.example)",
        ["https://www.google.com/travel/flights?q=Rome",
         "https://www.google.com/url?q=https://evil.example"])
    assert sources == ["https://www.google.com/travel/flights?q=Rome"]
    assert "evil" not in text


def test_every_shape_of_untrusted_link_is_removed():
    for text in ["voir (https://evil.com)",
                 '[x](https://evil.com "t")',
                 "[x](//evil.com)", "[x](HTTPS://evil.com)",
                 "www.evil.com"]:
        cleaned, sources = clean_answer(text, EVIL)
        assert "evil.com" not in cleaned and sources == [], text


def test_a_trusted_link_in_brackets_is_kept():
    url = DIPLO
    cleaned, sources = clean_answer(f"Lis la fiche ({url}).", [url])
    assert url in cleaned and sources == [url]


def test_markdown_around_a_link_is_not_part_of_it():
    url = DIPLO
    for text in [f"**{url}**", f"*{url}*", f"{url}: visa",
                 f"[{url}]({url})"]:
        cleaned, sources = clean_answer(text, [url])
        assert sources == [url] and "retiré" not in cleaned, text


def test_www_links_get_https_in_the_text():
    cleaned, sources = clean_answer("Voir www.booking.com/x.",
                                    ["https://www.booking.com/x"])
    assert "<https://www.booking.com/x>." in cleaned


def test_a_link_cited_in_other_brackets_is_kept():
    # Some models cite as 【url】: the bracket is not in the link.
    cleaned, sources = clean_answer(f"Visa【{DIPLO}】.",
                                    [DIPLO])
    assert cleaned == f"Visa【<{DIPLO}>】."
    assert sources == [DIPLO]


def test_raw_html_links_are_removed():
    cleaned, sources = clean_answer(
        'Voir <a href="&#104;ttps://evil.com">ici</a>.', EVIL)
    assert "<a" not in cleaned and "evil" not in cleaned
    assert "ici" in cleaned and sources == []


def test_a_broken_url_does_not_break_the_answer():
    cleaned, sources = clean_answer("Voir https://[evil.com/x ici.",
                                    EVIL)
    assert "evil" not in cleaned and sources == []


def test_a_link_no_tool_returned_is_removed():
    # The model rewrote the Kayak link: it would open another page.
    cleaned, sources = clean_answer(
        "[Kayak](https://www.kayak.fr/cars/Lisbon?start=2027-06-10)",
        ["https://www.kayak.fr/cars/Lisbon/2027-06-10/2027-06-15"])
    assert cleaned == "Kayak" and sources == []


def test_an_agent_keeps_the_links_its_tools_returned(monkeypatch):
    model = fake_model(
        tool_call("car_links", city="Lisbon", start="2027-06-10",
                  end="2027-06-15"),
        tool_call("read_official_page", url=DIPLO),
        "Une voiture : https://www.kayak.com/cars/Lisbon")
    monkeypatch.setattr(agents, "get_chat_model", lambda *a: model)
    monkeypatch.setattr(tools, "read_page", busy_site)
    monkeypatch.setitem(agents.AGENTS["transport"], "tools",
                        [tools.car_links, tools.read_official_page])
    report, found = agents.run_agent("transport", {}, "Auto ?")
    kayak = tools.cars_url("Lisbon", "2027-06-10", "2027-06-15")
    assert found == [kayak]  # the page that failed proves nothing
    assert kayak in report  # written by the code, not the model


def busy_site(url, domains):
    raise httpx.ConnectError("site down")


def test_nothing_hides_after_a_kept_link():
    cleaned, sources = clean_answer(
        f'[Visa]({DIPLO} "https://evil.com")', [DIPLO])
    assert cleaned == f"[Visa]({DIPLO})" and sources == [DIPLO]


def test_a_link_is_read_as_the_browser_reads_it():
    # The tool said "&", the model wrote "&amp;": the same link.
    url = "https://www.booking.com/x?ss=Porto&checkin=2027-05-02"
    cleaned, sources = clean_answer(
        f"Voir {url.replace('&', '&amp;')}.", [url])
    assert sources == [url] and cleaned == f"Voir <{url}>."

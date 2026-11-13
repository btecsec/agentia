"""The websites myTravel trusts, by subject.

This is not data to keep up to date: it is a trust policy. The
pages themselves are read live, on the day of the question.
The first three of a list are the ones the search engine is
pointed at. A domain also covers its subdomains: "gov" covers
travel.state.gov, "go.jp" covers www.mofa.go.jp.
"""

# Government sites of the main destinations: a visa rule is
# written by the country that issues the visa.
GOVERNMENTS = ["gouv.fr", "gov", "gov.uk", "europa.eu", "go.jp",
               "go.th", "go.kr", "gov.au", "govt.nz", "gc.ca",
               "admin.ch", "belgium.be", "gob.mx", "gov.br",
               "gov.in", "gov.sg", "gov.ma", "gouv.qc.ca"]

OFFICIAL = {
    # Visa, passport, entry rules.
    "entry": ["diplomatie.gouv.fr", "france-visas.gouv.fr",
              "service-public.fr", *GOVERNMENTS],
    # Vaccines, health risks, insurance abroad.
    "health": ["pasteur.fr", "who.int", "ameli.fr",
               "santepubliquefrance.fr", *GOVERNMENTS],
    # What goes in the suitcase (aviation security), what customs
    # allow, what an airline accepts.
    "baggage": ["ecologie.gouv.fr", "douane.gouv.fr",
                "airfrance.fr", "easa.europa.eu", *GOVERNMENTS],
    # Safety, natural risks.
    "safety": ["diplomatie.gouv.fr", "gdacs.org", "who.int"],
}

# Where offers and reviews are found: read, never booked.
BOOKING = {
    "hotels": ["booking.com", "hotels.com", "expedia.fr",
               "tripadvisor.fr", "tripadvisor.com"],
    "flights": ["kayak.fr", "skyscanner.fr", "airfrance.fr",
                "opodo.fr", "aviasales.com"],
    "cars": ["kayak.fr", "rentalcars.com", "europcar.fr",
             "sixt.fr", "hertz.fr"],
}

# Every site a link in an answer may point to.
TRUSTED = sorted({domain for group in (OFFICIAL, BOOKING)
                  for domains in group.values()
                  for domain in domains} | {"open-meteo.com"})
# Google, for its flight search only: google.com/url?q=... would
# send the traveler anywhere.
GOOGLE_FLIGHTS = "https://www.google.com/travel/flights?"

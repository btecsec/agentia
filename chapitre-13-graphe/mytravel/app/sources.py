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

# Chapitre 11 — Vols et voiture : de vraies offres

Trois outils : `flight_offers` (`app/flights.py` : offres réelles Travelpayouts, avec vendeur, date et lien ; `TRAVELPAYOUTS_TOKEN` dans `.env`), `flight_links` (Google Flights), `car_links` (Kayak). L'agent a huit outils.

Ce dossier contient **l'application myTravel telle qu'elle est à la fin du
chapitre** (`mytravel/`). Compare-le au dossier du chapitre précédent : la
différence est ce que ce chapitre ajoute. Code en anglais, livre en français.
Les tests n'ont besoin ni de clé ni de réseau.

## Installation (une fois, à la racine du dépôt)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # colle OPENROUTER_API_KEY
                                # (TAVILY_API_KEY facultative)
```

## Lancer

```bash
cd chapitre-11-transports/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 27 passed
```

À essayer : « Un vol Lyon-Lisbonne du 2027-05-02 au 2027-05-06, et une voiture ? »

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

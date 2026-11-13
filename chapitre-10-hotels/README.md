# Chapitre 10 — Hôtels : les vrais prix du jour

Trois outils : `hotel_offers` (`app/hotels.py` : le prix du jour d'une nuit, vendeur par vendeur, via Xotelo), `hotel_links` (lien Booking prérempli), `exchange_rate` (taux BCE).

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
cd chapitre-10-hotels/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 22 passed
```

À essayer : « Un hôtel calme à Porto du 2027-05-02 au 2027-05-06 pour deux. »

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

# Chapitre 9 — Recherche web officielle : visas, passeport, bagages, santé

`app/web.py` (Tavily ou DuckDuckGo, filtre de domaines, lecture de page), `app/sources.py` (sites de confiance), `app/tools.py` (deux outils), et chaque appel d'outil affiché en direct dans la page.

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
cd chapitre-09-recherche-web/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 17 passed
```

À essayer : « Il me faut un visa pour le Japon, 10 jours en mars ? »

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

# Chapitre 13 — Le graphe myTravel : des agents qui travaillent ensemble

`app/graph.py` (Mission, agents en parallèle avec `Send`, Synthèse) et `app/agents.py` (cinq spécialistes) ; `graph.stream` montre chaque agent qui démarre, puis la synthèse mot à mot.

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
cd chapitre-13-graphe/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 38 passed
```

À essayer : « Plan complet pour Rome, 4 jours en mai, 800 €, départ de Lyon. »

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

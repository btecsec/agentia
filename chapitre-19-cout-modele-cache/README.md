# Chapitre 19 — Coût, choix du modèle et cache

`app/cache.py` (les recherches gardées 24 heures), `MODELE_RAPIDE` pour les spécialistes, et `MODELE_PAYANT`, proposé seulement si tout est saturé, après ton accord.

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
cd chapitre-19-cout-modele-cache/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 80 passed
```

À essayer : pose deux fois « Visa pour le Japon ? » (la deuxième fois, aucune ligne `search` dans le terminal), puis `python evaluate.py` avant et après avoir réglé `MODELE_RAPIDE`.

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

# Chapitre 20 — Séjours clé en main et bilan

`app/stays.py` : les offres de vol (ch. 11) et d'hôtel (ch. 10) combinées en séjours clé en main, avec un total, au meilleur rapport qualité-prix, aux jours les moins chers pour un voyageur flexible ; à côté, les séjours des agences de voyages. C'est myTravel 1.0, à lancer dès le chapitre 6.

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
                                # TRAVELPAYOUTS_TOKEN : offres de vol
```

## Lancer

```bash
cd chapitre-20-projet-final/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 81 passed
```

À essayer, avec `TRAVELPAYOUTS_TOKEN` : « Un séjour à Lisbonne à deux, vol et hôtel, du 3 au 7 février depuis Paris, je suis flexible de trois jours. » L'étape « Séjours clé en main » s'affiche avant les agents, puis la réponse s'ouvre sur trois séjours avec leur total.

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

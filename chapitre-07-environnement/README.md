# Chapitre 7 — L'environnement : une API, une page, une réponse en direct

Le squelette : `server.py` (FastAPI), `static/index.html` (la page de chat), `app/chat.py` (la réponse du modèle, token par token, en flux SSE), `app/modele.py` (OpenRouter).

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
cd chapitre-07-environnement/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 6 passed
```

À essayer : Pose n'importe quelle question, puis ouvre http://localhost:8000/docs.

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

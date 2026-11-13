# Chapitre 8 — Mémoire : la conversation

Un agent LangGraph avec checkpointer SQLite (`app/assistant.py`, `app/memory.py`), un identifiant de conversation envoyé par la page, la réponse diffusée avec `stream_mode="messages"`.

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
cd chapitre-08-memoire/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 10 passed
```

À essayer : « Je pars à Lisbonne », puis « Et en mai ? ». Redémarre le serveur : il s'en souvient. Dis « Je suis belge », puis demande un visa : il ne redemande pas.

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

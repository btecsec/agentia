# Chapitre 15 — Sécurité : l'agent est une surface d'attaque

`app/security.py` : contenu web isolé, redirections contrôlées, limite de débit, en-têtes de sécurité.

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
cd chapitre-15-securite/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 66 passed
```

À essayer : Envoie onze messages en une minute ; regarde les en-têtes dans F12.

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

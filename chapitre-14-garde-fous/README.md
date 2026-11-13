# Chapitre 14 — Garde-fous et humain dans la boucle

`app/guardrails.py` (carte bancaire refusée, liens filtrés), `interrupt` avant la fiche de réservation, la carte « Oui / Non ».

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
cd chapitre-14-garde-fous/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 57 passed
```

À essayer : « Ma carte : 4111 1111 1111 1111 » (numéro de test), puis « Prépare la réservation » après un plan.

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

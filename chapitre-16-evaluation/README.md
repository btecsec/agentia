# Chapitre 16 — Évaluer myTravel

`app/evaluation.py`, `evaluate.py`, `data/eval_cases.json` ; les étapes (`steps`) de chaque réponse.

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
cd chapitre-16-evaluation/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 70 passed
```

À essayer : `python evaluate.py` (utilise ta clé et ton quota).

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

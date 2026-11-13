# Chapitre 12 — Météo et risques

Deux outils : `weather` (Open-Meteo, prévision ou l'an dernier) et `travel_advice` (diplomatie.gouv.fr). Dix outils : l'agent hésite. Et `mcp_server.py` prête ces deux outils à d'autres agents (Claude Code...) par MCP.

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
cd chapitre-12-meteo-risques/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
pytest                          # 32 passed
python mcp_server.py            # serveur MCP : http://127.0.0.1:8001/mcp
```

À essayer : « Quel temps à Lisbonne la semaine prochaine ? », puis un plan complet.

Puis ouvre les fichiers, essaie de comprendre seul, et reviens lire
« On lit le code ensemble » dans `CHAPITRE.md`.

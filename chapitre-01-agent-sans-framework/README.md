# Chapitre 1 — Qu'est-ce qu'un agent IA ? (sans framework)

Code source du chapitre 1. Un agent complet en Python pur : un modèle, trois outils factices
(recherche, calcul, météo simulée), une boucle ReAct, une mémoire et une gestion de la
fenêtre de contexte. **Le code est en anglais, le texte du livre en français.**

## Contenu du dossier

| Fichier | Rôle |
|---------|------|
| `tools.py` | Les trois outils factices et leurs descriptions JSON pour le modèle |
| `agent.py` | La classe `Agent` : toute la boucle ReAct tient ici |
| `memory.py` | Estimation de tokens et coupe propre de l'historique |
| `main.py` | Une conversation de trois questions, avec le détail Reason / Act / Observe |
| `modele.py` | Le client OpenRouter, seul endroit où un fournisseur est nommé. `python modele.py` liste les modèles gratuits qui savent appeler des outils |
| `tests/test_agent.py` | 20 tests, **sans clé d'API** (faux client) |

## Installation

```bash
# Une seule fois, à la racine du dépôt
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # puis colle ta clé OpenRouter dedans

# Puis, dans le dossier du chapitre
cd chapitre-01-agent-sans-framework
python modele.py                # modèles gratuits utilisables aujourd'hui
```

## Lancer l'agent

```bash
python main.py
```

Sous Windows, si les accents ou le symbole `°` s'affichent mal : `set PYTHONUTF8=1`.

## Lancer les tests

```bash
pytest                          # 20 tests, aucune clé nécessaire
pytest tests/test_agent.py::test_turn_limit_stops_a_looping_agent -v
```

# Chapitre 3 — LangGraph : orchestrer des workflows complexes

Code source du chapitre 3. Un workflow « rédiger → critiquer → réécrire » en graphe d'état
LangGraph, avec routage conditionnel, garde-fou, visualisation, sauvegarde SQLite et pause
avant réécriture. Indépendant de myTravel. **Code en anglais, texte du livre en français.**

## Contenu du dossier

| Fichier | Rôle |
|---------|------|
| `graph.py` | L'état, les trois nœuds, la fonction de routage, `build_graph`, `drawing` (Mermaid) |
| `main.py` | Lance le graphe, affiche le dessin et suit l'exécution nœud par nœud |
| `modele.py` | Client OpenRouter + `get_chat_model()`. `python modele.py` liste les modèles gratuits |
| `tests/test_graph.py` | 13 tests, **sans clé ni réseau** (modèle scripté) |

## Installation

```bash
# Une seule fois, à la racine du dépôt
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # puis colle ta clé OpenRouter dedans

# Puis, dans le dossier du chapitre
cd chapitre-03-langgraph
```

## Lancer le graphe

```bash
python main.py
```

Un fichier `checkpoints.sqlite` apparaît (ignoré par git) : c'est l'état sauvegardé du graphe.
Supprime-le pour repartir de zéro.

## Lancer les tests

```bash
pytest                          # 13 tests, hors ligne
pytest tests/test_graph.py::test_pause_before_rewrite_then_resume -v
```

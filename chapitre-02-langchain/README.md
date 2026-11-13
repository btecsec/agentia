# Chapitre 2 — LangChain : construire un agent rapidement

Code source du chapitre 2. L'agent du chapitre 1 réécrit avec LangChain (`create_agent`),
avec de vrais outils (Wikipedia, Open-Meteo, Frankfurter : gratuits, sans clé) et une mémoire
par `thread_id`. **Code en anglais, texte du livre en français.**

## Contenu du dossier

| Fichier | Rôle |
|---------|------|
| `tools.py` | Quatre outils `@tool` : recherche Wikipedia, calcul sûr, météo, taux de change |
| `agent.py` | `build_agent` (PromptTemplate + `create_agent` + checkpointer) et `ask` |
| `main.py` | Une conversation de trois questions sur un même fil |
| `modele.py` | Client OpenRouter + `get_chat_model()` pour LangChain. `python modele.py` liste les modèles gratuits |
| `tests/test_agent.py` | 12 tests, **sans clé ni réseau** (faux modèle, faux réseau) |

## Installation

```bash
# Une seule fois, à la racine du dépôt
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # puis colle ta clé OpenRouter dedans

# Puis, dans le dossier du chapitre
cd chapitre-02-langchain
```

## Lancer l'agent

```bash
python main.py
```

Sous Windows, si les accents s'affichent mal : `set PYTHONUTF8=1`.

## Lancer les tests

```bash
pytest                          # 12 tests, hors ligne
pytest tests/test_agent.py::test_memory_is_kept_per_thread -v
```

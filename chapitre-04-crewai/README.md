# Chapitre 4 — CrewAI : une équipe d'agents par rôle

Code source du chapitre 4. Une mini-équipe CrewAI (chercheur, rédacteur, vérificateur) qui produit
un paragraphe de contenu, en processus séquentiel ou hiérarchique. Indépendant de myTravel.
**Code en anglais, texte du livre en français.**

> **Python 3.13 ou plus ancien.** CrewAI ne supporte pas encore Python 3.14. Sur 3.14, les tests
> de ce chapitre sont *ignorés* (skipped), pas en échec. Voir « Installation » plus bas.

## Contenu du dossier

| Fichier | Rôle |
|---------|------|
| `crew.py` | Les trois agents, l'outil `lookup_city`, les trois tâches, `build_crew` |
| `main.py` | Lance l'équipe sur « Lisbon » et affiche la sortie de chaque rôle |
| `modele.py` | Client OpenRouter + `get_crew_llm()` pour CrewAI. `python modele.py` liste les modèles gratuits |
| `tests/test_crew.py` | 13 tests, **sans clé ni réseau** (modèle scripté) |

## Installation

```bash
# Depuis le dossier du chapitre : son requirements.txt y est.
cd chapitre-04-crewai

# CrewAI exige Python 3.13 ou plus ancien (pas 3.14).
py -3.13 -m venv .venv-crewai   # Windows
.venv-crewai\Scripts\activate
# python3.13 -m venv .venv-crewai && source .venv-crewai/bin/activate   # macOS / Linux
pip install -r requirements.txt

# Clé OpenRouter : copie .env.example (racine du dépôt) en .env, puis colle ta clé.
```

## Lancer l'équipe

```bash
python main.py
```

Derrière un antivirus ou un proxy qui intercepte le HTTPS, une erreur `CERTIFICATE_VERIFY_FAILED`
se corrige en pointant `SSL_CERT_FILE` vers le fichier de certificats de l'outil.

## Lancer les tests

```bash
pytest                          # 13 tests, hors ligne
pytest tests/test_crew.py::test_sequential_crew_always_makes_three_model_calls -v
```

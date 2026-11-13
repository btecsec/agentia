# Chapitre 5 — Agents no-code : n8n, Make et autres

Code source du chapitre 5. Un scénario « recherche Wikipedia → synthèse par un modèle → e-mail »
sous forme de workflow **n8n** importable, et son équivalent en **Python** (`pipeline.py`).
Indépendant de myTravel. **Code en anglais, texte du livre en français.**

## Contenu du dossier

| Fichier | Rôle |
|---------|------|
| `workflows/research-summary-email.n8n.json` | Le workflow n8n : six nœuds, aucun secret (références d'identifiants à renseigner) |
| `docker-compose.yml` | Lance n8n chez toi sur http://localhost:5678 |
| `pipeline.py` | Le même scénario en Python : `fetch_summary`, `summarize`, `build_email`, `deliver`, `run` |
| `main.py` | Lance `pipeline.run` ; l'e-mail est écrit dans `outbox/summary.eml` si `SMTP_HOST` n'est pas défini |
| `modele.py` | Client OpenRouter. `python modele.py` liste les modèles gratuits |
| `tests/test_workflow.py` | 12 tests, **sans clé, sans réseau, sans n8n** : le workflow est un fichier JSON, on le teste |

## Installation

```bash
# Une seule fois, à la racine du dépôt
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # puis colle ta clé OpenRouter dedans

# Puis, dans le dossier du chapitre
cd chapitre-05-no-code
```

## Lancer la version Python

```bash
python main.py                  # sujet par défaut : Lisbon
python main.py "Kyoto"
```

## Lancer n8n (facultatif, demande Docker)

```bash
docker compose up -d            # puis http://localhost:5678
# Workflows > Import from file > workflows/research-summary-email.n8n.json
# Credentials : un « Header Auth » (Authorization: Bearer <ta clé OpenRouter>) et un « SMTP »
docker compose down             # arrêt ; les workflows restent dans le volume
```

Le fichier de workflow a été validé par les tests du dossier (structure, connexions, absence de
secret), mais n'a pas été importé dans toutes les versions de n8n. Si un nœud est refusé à
l'import, recrée-le à la main avec les réglages du fichier.

## Lancer les tests

```bash
pytest                          # 12 tests, hors ligne
```

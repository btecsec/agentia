# Agents IA : développer son propre assistant IA de voyage

Code source du livre **« Agents IA : développer son propre assistant IA de voyage »**.
Un dossier par chapitre, chacun se lance seul.

## Deux parties, deux façons de ranger le code

**Partie 1 — Fondamentaux (chapitres 1 à 5).** Un dossier autonome par chapitre :
un agent sans framework, puis LangChain, LangGraph, CrewAI et le no-code.

**Parties 2 à 5 — myTravel (chapitres 6 à 20).** Un assistant de voyage web : une page
de chat, une API FastAPI, sept agents LangGraph, des sources officielles lues en direct.
L'application **finie** est dans `chapitre-20-projet-final/mytravel/`, et le chapitre 6
invite à la lancer avant tout ; à partir du chapitre 7, chaque dossier contient
**l'application telle qu'elle est à la fin du chapitre**. Compare deux dossiers
voisins : la différence est ce que le chapitre t'apprend.

Deux règles valent pour tout myTravel :

- **aucune donnée en dur** : visas, météo, conseils aux voyageurs, prix sont lus en
  direct, sur des sites de confiance ;
- le code ne contient **que ce qui sert**, sans abstraction inutile : des fonctions,
  un fichier par rôle.

| # | Chapitre | Dossier |
|---|----------|---------|
| 1 | Qu'est-ce qu'un agent IA ? (sans framework) | `chapitre-01-agent-sans-framework/` |
| 2 | LangChain | `chapitre-02-langchain/` |
| 3 | LangGraph | `chapitre-03-langgraph/` |
| 4 | CrewAI : des agents par rôle | `chapitre-04-crewai/` |
| 5 | Agents no-code | `chapitre-05-no-code/` |
| 6 | Spécifications de myTravel | `chapitre-06-specifications/` |
| 7 | L'environnement : une API, une page, une réponse en direct | `chapitre-07-environnement/mytravel/` |
| 8 | Mémoire : la conversation | `chapitre-08-memoire/mytravel/` |
| 9 | Recherche web officielle | `chapitre-09-recherche-web/mytravel/` |
| 10 | Hôtels : les vrais prix du jour | `chapitre-10-hotels/mytravel/` |
| 11 | Vols et voiture : de vraies offres | `chapitre-11-transports/mytravel/` |
| 12 | Météo et risques | `chapitre-12-meteo-risques/mytravel/` |
| 13 | Le graphe myTravel | `chapitre-13-graphe/mytravel/` |
| 14 | Garde-fous et humain dans la boucle | `chapitre-14-garde-fous/mytravel/` |
| 15 | Sécurité | `chapitre-15-securite/mytravel/` |
| 16 | Évaluation | `chapitre-16-evaluation/mytravel/` |
| 17 | Observabilité | `chapitre-17-observabilite/mytravel/` |
| 18 | Déploiement sur Google Cloud Run | `chapitre-18-deploiement/mytravel/` |
| 19 | Coût, choix du modèle et cache | `chapitre-19-cout-modele-cache/mytravel/` |
| 20 | Séjours clé en main et bilan (l'application finie) | `chapitre-20-projet-final/mytravel/` |

## Démarrage rapide

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt   # une seule fois pour tout le livre
cp .env.example .env              # OPENROUTER_API_KEY (+ TAVILY_API_KEY, TRAVELPAYOUTS_TOKEN)

cd chapitre-20-projet-final/mytravel
uvicorn server:app --reload       # puis http://localhost:8000
```

L'environnement est **partagé** à la racine : un seul `.venv`, un seul `.env`, un seul
`requirements.txt`. CrewAI (chapitre 4) demande Python 3.13 ou plus ancien.

## Une seule clé, et elle est gratuite

**Tout le livre passe par [OpenRouter](https://openrouter.ai).** Le client est construit
par `modele.py` (partie 1) ou `app/modele.py` (myTravel), seul endroit où l'adresse du
fournisseur apparaît. Le modèle par défaut est **gratuit** (suffixe `:free`). OpenRouter
demande une carte à l'inscription, mais ne prélève rien tant que tu restes sur un slug
`:free`. Les quotas gratuits sont bas, et un plan complet consomme six à dix requêtes :
`python -m app.modele` liste les modèles gratuits capables d'appeler des outils.

La recherche web utilise Tavily si `TAVILY_API_KEY` est renseignée (gratuit, 1 000
recherches par mois), sinon DuckDuckGo, sans clé.

## Tests

Les tests tournent **sans clé et sans réseau** : le modèle et la recherche sont remplacés
par des doublures.

```bash
pytest chapitre-13-graphe/mytravel    # un chapitre
python verifier.py                    # tous, un processus par dossier
```

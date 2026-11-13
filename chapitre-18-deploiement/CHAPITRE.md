# Chapitre 18 — Déploiement sur Google Cloud Run

> **Dossier GitHub associé :** `chapitre-18-deploiement/`

**À la fin de ce chapitre, tu sauras :**

- expliquer ce qu'est une image Docker, et en écrire une pour myTravel ;
- garder les clés hors de l'image, dans Secret Manager ;
- mettre myTravel en ligne sur Google Cloud Run avec une seule commande ;
- faire tourner les tests à chaque `git push` avec GitHub Actions ;
- connaître les limites d'un premier déploiement : disque éphémère, une seule copie.

## « Ça marche sur ma machine »

C'est la phrase la plus célèbre de l'informatique, et elle a toujours raison. Sur ta machine, il y a ton Python, ton `.venv`, ton `.env`, tes certificats, ton dossier. Sur un serveur, il n'y a rien de tout ça. La moitié des pannes de mise en production viennent d'une différence entre les deux qu'on n'avait pas vue : une bibliothèque dans une autre version, une variable d'environnement oubliée, un fichier qui n'a pas été copié.

**Docker** règle ce problème en emballant tout. Une **image** Docker est un paquet qui contient un système minimal, Python, les bibliothèques, et ton code. On la construit une fois, et elle tourne pareil partout. Un **conteneur**, c'est une image en train de tourner.

**Google Cloud Run** prend ton image et la fait tourner pour toi. Pas de serveur à installer, pas de système à mettre à jour. Il lui donne une adresse https publique, démarre une copie quand une requête arrive, l'arrête quand plus personne ne vient, et ne facture que le temps où elle travaille. Pour un projet comme myTravel, l'offre gratuite couvre largement l'usage d'un développeur et de ses amis.

## Ce que fait chaque pièce

**Le `Dockerfile`** décrit l'image : partir d'un Python officiel, installer les dépendances, copier le code, lancer uvicorn. Il ne contient **aucune clé**. Une image peut être copiée, partagée, inspectée : une clé dedans est une clé publiée.

**Secret Manager** est le coffre de Google Cloud. On y range `OPENROUTER_API_KEY` (et `TAVILY_API_KEY` si tu en as une). Au démarrage, Cloud Run lit le coffre et passe les valeurs au conteneur comme variables d'environnement. Pour myTravel, rien ne change : `os.environ.get("OPENROUTER_API_KEY")`, comme avec le `.env`.

**`gcloud run deploy --source .`** fait tout en une commande : il envoie le dossier à Google, construit l'image avec le `Dockerfile` (service Cloud Build), la range (Artifact Registry) et la démarre (Cloud Run).

**GitHub Actions** fait tourner les tests sur une machine neuve à chaque `git push`. Si un test échoue, tu le sais avant de déployer. C'est la **CI**, l'intégration continue.

> 💡 **À retenir** — L'image contient le code, jamais les secrets. Les secrets vivent dans un coffre, et arrivent au conteneur sous forme de variables d'environnement.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

```text
chapitre-18-deploiement/mytravel/
├── Dockerfile                 ← NOUVEAU : l'image
├── .dockerignore              ← NOUVEAU : ce qui n'entre pas dedans
├── requirements.txt           ← NOUVEAU : dépendances de l'image
└── .github/workflows/ci.yml   ← NOUVEAU : les tests à chaque push
```

| Fichier | Rôle |
|---|---|
| `Dockerfile` | construit l'image : Python 3.13, dépendances, code, uvicorn sur `$PORT` |
| `requirements.txt` | seulement ce dont myTravel a besoin, pas tout le livre |
| `.github/workflows/ci.yml` | installe, lance `pytest` sur GitHub à chaque push |

Le fichier `.dockerignore` liste ce qui ne doit **pas** entrer dans l'image : `.env`, les bases `*.db`, les tests, les caches.

### Les tests, en local

```bash
cd chapitre-18-deploiement/mytravel
pytest                    # 75 passed
```

Si Docker est installé sur ta machine, tu peux aussi construire et lancer l'image en local, exactement comme Cloud Run le fera :

```bash
docker build -t mytravel .
docker run -p 8080:8080 -e PORT=8080 \
  -e OPENROUTER_API_KEY=sk-or-... mytravel
```

Puis http://localhost:8080.

### Déployer sur Cloud Run, pas à pas

**1. Le compte et le projet.** Crée un compte sur cloud.google.com. Comme pour OpenRouter, une carte est demandée pour activer la facturation, même pour rester dans l'offre gratuite. Installe l'outil en ligne de commande `gcloud` (cloud.google.com/sdk), puis :

```bash
gcloud init                       # connexion, choix du projet
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

**2. La clé dans le coffre.**

```bash
printf "sk-or-v1-..." | gcloud secrets create openrouter-key \
  --data-file=-
```

Cloud Run tourne sous un « compte de service », une identité de machine. Il faut lui donner le droit de lire ce secret. Remplace `NUMERO` par le numéro de ton projet (`gcloud projects list` l'affiche) :

```bash
SA=NUMERO-compute@developer.gserviceaccount.com
gcloud secrets add-iam-policy-binding openrouter-key \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor"
```

**3. Le déploiement**, depuis le dossier `mytravel/` :

```bash
gcloud run deploy mytravel --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --max-instances 1 \
  --set-secrets OPENROUTER_API_KEY=openrouter-key:latest
```

Quelques minutes plus tard, `gcloud` affiche une adresse en `https://mytravel-....run.app`. Ouvre-la : c'est ton myTravel, en ligne. Envoie le lien à quelqu'un. Il n'a besoin de rien installer.

`--allow-unauthenticated` rend le site public : sans ce drapeau, seuls les comptes Google autorisés y accèdent. `--max-instances 1` est expliqué plus bas, et c'est important.

**4. Les logs.** Dans la console Google Cloud, ouvre *Cloud Run*, puis le service *mytravel*, onglet *Journaux*. Tu retrouves les lignes JSON du chapitre 17, et tu peux filtrer par champ : `jsonPayload.event="search"`.

**5. Les mises à jour.** Tu changes le code, tu relances la même commande `gcloud run deploy`. Cloud Run démarre la nouvelle version, bascule le trafic dessus, et garde l'ancienne : en cas de problème, l'onglet *Révisions* permet de revenir en arrière en un clic.

### À toi d'abord

Lis le `Dockerfile` ligne par ligne et réponds : pourquoi `COPY requirements.txt .` est-il copié **avant** le reste du code, dans une ligne à part ?

## On lit le code ensemble

### Le `Dockerfile`

<!-- code: mytravel/Dockerfile -->
```dockerfile
# The image Cloud Run starts. Small, and without any secret:
# the keys are given to Cloud Run, not baked into the image.
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Never run as root inside the container.
RUN useradd --create-home mytravel && chown -R mytravel /app
USER mytravel

# Cloud Run tells the container which port to listen on: $PORT.
CMD exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}
```

Je le lis comme une recette, de haut en bas, parce que Docker l'exécute dans cet ordre.

`FROM python:3.13-slim` : l'image de départ, un Debian minimal avec Python. *Slim* veut dire sans compilateurs ni outils inutiles, donc une image plus petite et moins de failles possibles. Pourquoi 3.13 alors que tu as peut-être 3.14 ? Parce que toutes nos dépendances publient leurs paquets pour 3.13 ; en production, on choisit la version la plus éprouvée.

Réponse à ta question : Docker construit l'image en **couches**, une par instruction, et garde chaque couche en cache. Tant que `requirements.txt` ne change pas, la couche `pip install` est réutilisée telle quelle, même si tu as changé tout le code. Copier les dépendances d'abord, le code ensuite, fait passer une reconstruction de trois minutes à dix secondes.

`useradd` puis `USER mytravel` : le serveur ne tourne pas en administrateur (*root*). Si une faille permettait un jour d'exécuter du code dans le conteneur, l'attaquant n'aurait que les droits d'un utilisateur ordinaire.

La dernière ligne lance uvicorn. `--host 0.0.0.0` lui fait accepter les connexions venues de l'extérieur du conteneur (par défaut, il n'écoute que lui-même). Et `${PORT:-8080}` : Cloud Run dit au conteneur sur quel port écouter via la variable `PORT`, et `:-8080` donne une valeur par défaut quand on la lance soi-même. Un conteneur qui écouterait sur 8000 alors que Cloud Run attend 8080 ne démarrerait jamais.

### La CI

<!-- code: mytravel/.github/workflows/ci.yml -->
```yaml
# Every push: the tests run on a clean machine. Red = no deploy.
name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements.txt pytest
      - run: pytest
```

À chaque `push` ou *pull request*, GitHub prend une machine Ubuntu neuve, récupère le code, installe Python et les dépendances, et lance `pytest`. Rien de ta machine n'y est : si un test ne passe que chez toi parce qu'un fichier traîne dans ton dossier, la CI le dira. Et nos tests n'ont besoin ni de clé ni de réseau : la CI n'a aucun secret à connaître.

Un détail pratique : GitHub ne lit les fichiers `.github/workflows/` qu'à la **racine** d'un dépôt. Pour que cette CI tourne, copie le dossier `mytravel/` dans son propre dépôt GitHub.

### Les limites de ce premier déploiement

Deux limites, que je préfère te dire maintenant plutôt que tu les découvres.

**Le disque est éphémère.** Sur Cloud Run, le disque d'un conteneur disparaît à chaque redémarrage, et un conteneur sans visite s'arrête au bout de quelques minutes. Conséquence : `mytravel.db` repart de zéro, donc les conversations et le cache aussi. Pour un assistant de démonstration, c'est acceptable. Pour un vrai produit, on range ces données dans une base qui survit : Cloud SQL (PostgreSQL), avec le checkpointer PostgreSQL de LangGraph à la place de `SqliteSaver`. Le reste du code ne change pas.

**Une seule copie.** `--max-instances 1` interdit à Cloud Run de lancer plusieurs copies quand le trafic monte. Pourquoi se limiter ? Parce que deux copies auraient chacune leur fichier SQLite et leur limite de débit en mémoire : une conversation commencée sur l'une serait inconnue de l'autre. Une copie, c'est cohérent. Le jour où il en faut plus, c'est le même chantier que le disque : une base partagée.

> ⚠️ **Piège classique** — Ouvrir l'accès public sans regarder la facture. Cloud Run ne coûte presque rien, mais chaque question coûte des appels au modèle. Garde le modèle gratuit, ou fixe une limite de dépense dans OpenRouter (*Settings*, *Credits*) avant de partager le lien. La limite de débit du chapitre 15 aide, elle ne remplace pas un plafond de dépense.

## QCM

**1.** Pourquoi aucune clé ne doit-elle être dans l'image Docker ?

- **a)** Parce qu'une image peut être copiée et inspectée
- **b)** Parce que Docker refuse les clés
- **c)** Parce que les secrets doivent arriver depuis un coffre, en variables d'environnement
- **d)** Parce que l'image serait trop lourde

**2.** Pourquoi copier `requirements.txt` avant le reste du code ?

- **a)** Pour que la couche d'installation reste en cache tant que les dépendances ne changent pas
- **b)** Parce que Docker l'exige
- **c)** Pour reconstruire l'image beaucoup plus vite après un changement de code
- **d)** Pour que les tests passent

**3.** Que se passe-t-il si le conteneur écoute sur le port 8000 alors que Cloud Run envoie `PORT=8080` ?

- **a)** Cloud Run s'adapte tout seul
- **b)** Le service ne démarre pas
- **c)** Il démarre, mais en http
- **d)** Rien, le port n'a pas d'importance

**4.** Pourquoi `--max-instances 1` ?

- **a)** Parce que la base SQLite et la limite de débit vivent dans une seule copie
- **b)** Pour que les conversations ne se perdent pas d'une copie à l'autre
- **c)** Parce que l'offre gratuite l'impose
- **d)** Pour aller plus vite

**5.** Le service redémarre. Que deviennent les conversations ?

- **a)** Elles sont conservées dans l'image
- **b)** Elles sont perdues, car le disque de Cloud Run est éphémère
- **c)** Elles sont dans Secret Manager
- **d)** Une base comme Cloud SQL les garderait

**6.** Que vérifie la CI ?

- **a)** Que les tests passent sur une machine neuve, à chaque push
- **b)** Que la clé OpenRouter est valide
- **c)** Que rien ne dépend d'un fichier qui ne traîne que sur ta machine
- **d)** Que le site est en ligne

**Réponses.** Q1 : a, c · Q2 : a, c · Q3 : b · Q4 : a, b · Q5 : b, d · Q6 : a, c

## Ce qu'il faut retenir

1. Une image Docker emballe le système, Python, les dépendances et le code : elle tourne pareil partout.
2. Les secrets ne sont jamais dans l'image : Secret Manager les donne au conteneur en variables d'environnement.
3. `gcloud run deploy --source .` construit l'image, la range et la met en ligne en une commande, avec une adresse https publique.
4. La CI lance les tests sur une machine neuve à chaque push : ce qui ne marche que chez toi se voit avant le déploiement.
5. Disque éphémère et une seule copie : c'est le prix d'un premier déploiement simple, et le chemin vers une vraie base est tracé.

**Au chapitre suivant :** myTravel est en ligne. Combien coûte une question ? Peut-on en faire autant pour moins cher ? On mesure, on met en cache, on choisit un modèle plus léger pour les spécialistes, et on fait le bilan de la version 1.0.

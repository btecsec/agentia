# Chapitre 19 — Coût, choix du modèle et cache

> **Dossier GitHub associé :** `chapitre-19-cout-modele-cache/`

**À la fin de ce chapitre, tu sauras :**

- compter ce que coûte une question à myTravel, en appels et en tokens ;
- mettre en cache les recherches web pour ne pas payer deux fois la même ;
- donner un modèle plus léger aux spécialistes et garder le meilleur pour Mission et Synthèse ;
- mesurer l'effet d'un changement de modèle avec l'évaluation du chapitre 16 ;
- proposer un modèle payant quand tout est saturé, sans jamais dépenser sans accord.

## La facture de fin de mois

Imagine que tu partages le lien de myTravel dans un groupe de voyageurs. Cent personnes, trois plans complets chacune dans le mois. Un plan complet, c'est six à dix appels au modèle. Fais le calcul : trois mille appels. Sur un modèle gratuit, le quota tombe dès le premier soir. Sur un grand modèle payant, à quelques centimes l'appel, la facture fait plusieurs dizaines d'euros, pour un projet qui ne rapporte rien.

Ce n'est pas une raison pour renoncer. C'est une raison pour savoir **où** part l'argent, et pour ne le dépenser que là où il change la réponse.

## Où part le coût

Un appel au modèle se paie au **token**, un morceau de mot (environ quatre caractères en français). On paie les tokens envoyés (le prompt, la conversation, les descriptions d'outils, les pages lues) et, plus cher, les tokens écrits par le modèle.

Pour un plan complet, le décompte ressemble à ceci :

| Étape | Appels | Ce qui pèse |
|---|---|---|
| Mission | 1 | la conversation entière |
| 5 spécialistes | 2 à 3 chacun | les pages officielles lues (jusqu'à 8 000 caractères) |
| Synthèse | 1 | les cinq rapports, et la réponse écrite |

Trois leçons sortent de ce tableau. Les **spécialistes** font la majorité des appels, mais leur travail est simple : chercher, lire, résumer. Les **pages lues** pèsent plus lourd que les prompts. Et une **même recherche** revient souvent : dix voyageurs qui partent au Japon déclenchent dix fois « visa Japon ».

D'où les deux leviers de ce chapitre, plus une sortie de secours.

**Le cache.** Une recherche est gardée 24 heures dans SQLite. La deuxième fois, on ne demande rien au moteur. Les règles de visa ne changent pas d'heure en heure, et 24 heures reste un délai qu'on peut défendre devant un voyageur. Un résultat vide n'est jamais gardé : ce peut être une panne passagère, on retentera. Les prix, eux, ne passent jamais par ce cache : les offres de vol et d'hôtel sont demandées à chaque question.

**Le routage de modèles.** Le **routage**, c'est choisir le modèle selon la tâche. Les spécialistes reçoivent un modèle rapide et bon marché (variable `MODELE_RAPIDE`), suffisant pour appeler un outil et résumer une page. Mission et Synthèse gardent le modèle principal (`MODELE`) : comprendre une demande floue et écrire une réponse claire, c'est là que la qualité se voit. C'est OpenRouter qui rend ça possible en une ligne : tous les modèles parlent le même dialecte, on ne change que le nom.

**La sortie payante.** Le modèle gratuit et ses deux secours (chapitre 7) peuvent être saturés en même temps. Plutôt que « réessaie dans une minute », myTravel propose un modèle payant (`MODELE_PAYANT`, par défaut `deepseek/deepseek-v4-flash`) : quelques centimes la question. Mais dépenser l'argent du voyageur, c'est une action, comme réserver au chapitre 14 : **on demande avant**. La page affiche le nom du modèle, le voyageur dit oui ou non, et seulement alors la question repart.

> 💡 **À retenir** — On ne réduit pas un coût qu'on n'a pas mesuré. Compte les appels, regarde ce qui pèse, puis agis là : cache sur ce qui se répète, petit modèle sur ce qui est simple.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

| Fichier | Ce qui change |
|---|---|
| `app/cache.py` | NOUVEAU : `get` et `put`, une table SQLite avec la date de chaque entrée |
| `app/web.py` | `search_web` lit le cache avant le moteur, et y range ce qu'il trouve |
| `app/modele.py` | `FAST_MODEL` (lu dans `MODELE_RAPIDE`), `PAID_MODEL` (lu dans `MODELE_PAYANT`), et `paid()` |
| `app/agents.py` | les spécialistes utilisent `FAST_MODEL` |
| `app/graph.py` | le choix payant voyage dans la configuration du graphe |
| `server.py` | tous les gratuits saturés : un événement `error` avec `paid_offer` et un jeton à usage unique |
| `static/index.html` | `payCard` : le prix d'abord, la question repart sur un « oui » ; sur un « non », `retryLater` réessaie gratuitement après une minute |

### Lancer le chapitre

```bash
cd chapitre-19-cout-modele-cache/mytravel
uvicorn server:app --reload
pytest                    # 80 passed
```

Pose deux fois de suite « Visa pour le Japon ? ». Dans le terminal, la première fois tu vois une ligne `"event": "search"` ; la deuxième, aucune : le cache a répondu.

Puis mesure. Ouvre la page *Activity* de ton compte OpenRouter : chaque appel y figure, avec son modèle, ses tokens et son prix. Pose un plan complet, et compte. Puis essaie le routage, dans le `.env` :

```bash
MODELE=deepseek/deepseek-v4-flash
MODELE_RAPIDE=google/gemini-3.1-flash-lite
```

Relance le serveur, refais le même plan, compare la page *Activity*. Enfin, la question qui compte vraiment : est-ce que la qualité a tenu ?

```bash
python evaluate.py        # avant, puis après le changement
```

Si le score tient, tu as économisé sans rien perdre. S'il baisse, tu sais exactement quoi annuler. Pour voir la sortie payante sans attendre une vraie saturation, lance `pytest -k paid` : trois tests jouent la scène, sans réseau.

### À toi d'abord

Ouvre `app/web.py` et trouve la ligne qui fabrique la clé du cache. Pourquoi contient-elle aussi la liste des domaines, et pas seulement la requête ?

## On lit le code ensemble

### `app/cache.py` : vingt lignes de SQL

<!-- code: mytravel/app/cache.py 13-34 -->
```python
DB = os.environ.get("MYTRAVEL_DB", "mytravel.db")
connection = sqlite3.connect(DB, check_same_thread=False)
lock = threading.Lock()  # parallel agents search at the same time
connection.execute("CREATE TABLE IF NOT EXISTS cache "
                   "(key TEXT PRIMARY KEY, saved REAL, value TEXT)")


def get(key, max_age_hours=24):
    with lock:
        row = connection.execute(
            "SELECT saved, value FROM cache WHERE key = ?",
            (key,)).fetchone()
    if row and time.time() - row[0] < max_age_hours * 3600:
        return json.loads(row[1])
    return None


def put(key, value):
    with lock, connection:  # one at a time, committed
        connection.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
            (key, time.time(), json.dumps(value)))
```

Tu reconnais tout : la même base que la mémoire du chapitre 8, une table de plus, des requêtes paramétrées. Et le même verrou : cinq agents qui cherchent en même temps lisent et écrivent le cache en même temps, et `lock` les fait passer un par un. Chaque entrée garde l'heure où elle a été rangée (`saved`), et `get` refuse une entrée trop vieille. On ne supprime jamais rien : `INSERT OR REPLACE` écrase l'ancienne valeur à la recherche suivante.

Ici, `time.time()` et pas `time.monotonic()`, contrairement au chapitre 15. La raison : la date est **rangée sur le disque** et relue plus tard, peut-être par un autre processus. Une horloge monotone n'a de sens que dans le processus qui l'a lue.

### `search_web` : le cache en quatre lignes

<!-- code: mytravel/app/web.py 63-82 -->
```python
def search_web(query, domains, max_results=5):
    """Results from the allowed sites only. Never raises."""
    key = json.dumps([query, domains])
    started = time.perf_counter()
    try:
        saved = cache.get(key)
        if saved:
            return saved
        found = search_engine(query, domains)
        # Ads and random blogs are filtered here, whatever engine.
        results = [r for r in found
                   if is_allowed(r["url"], domains)][:max_results]
        if results:  # an empty answer may be a hiccup: retry later
            cache.put(key, results)
    except Exception as error:  # engine down, quota, network, db
        log("search_failed", query=query, error=str(error))
        return []
    log("search", query=query, results=len(results),
        seconds=round(time.perf_counter() - started, 2))
    return results
```

Réponse à ta question : la même requête sur deux listes de domaines ne donne pas les mêmes résultats. « Japon » sur les sites officiels et « Japon » sur TripAdvisor sont deux recherches différentes. `json.dumps([query, domains])` fait de la paire une clé texte unique.

Le cache est placé **dans** `search_web`, pas dans chaque outil. Tous les outils qui cherchent en profitent sans le savoir, y compris `city_key` du chapitre 10 : le code TripAdvisor de Lisbonne n'est cherché qu'une fois par jour. C'est la récompense d'avoir fait passer toutes les recherches par une seule fonction depuis le chapitre 9.

### Le routage : une variable

Dans `app/modele.py`, une ligne : `FAST_MODEL = os.environ.get("MODELE_RAPIDE", MODEL)`. Sans `MODELE_RAPIDE`, c'est le même modèle partout, et rien ne change pour qui ne s'en sert pas. Dans `app/agents.py`, `run_agent` appelle `get_chat_model(FAST_MODEL)`. Le test `test_agents_use_the_fast_model` garantit que personne ne le défera par mégarde.

### La sortie payante : demander avant de dépenser

Le serveur d'abord. Quand tous les gratuits répondent 429, il ne paie pas : il envoie un événement `error`, avec le nom du modèle payant et un jeton.

<!-- code: mytravel/server.py 102-113 -->
```python
def failure(error, conversation, paid):
    """Too late for an HTTP error: the error is one more event."""
    if isinstance(error, RateLimitError):
        # Free quotas are shared by everyone: it is not your code.
        if paid:  # the paid model failed too: no offer
            return {"type": "error", "detail": "Le modèle est "
                    "saturé : réessaie dans une minute."}
        # Paying is the traveler's call: the page asks first.
        offers[conversation] = secrets.token_urlsafe()
        return {"type": "error", "detail": "Le modèle est saturé.",
                "paid_offer": PAID_MODEL,
                "token": offers[conversation]}
```

Pourquoi un jeton, et pas un simple `paid: true` envoyé par la page ? Parce que n'importe qui peut écrire une requête à la main : avec un `true`, un inconnu dépenserait ton crédit à chaque question. Une revue de sécurité me l'a fait voir. Le serveur garde donc le jeton qu'il a proposé (`offers`) et ne passe au payant que si la page rend exactement celui-là :

<!-- code: mytravel/server.py 66-70 -->
```python
    offer = offers.pop(body.conversation, "")
    paid = bool(offer) and secrets.compare_digest(offer, body.paid)
    claim(body.conversation)  # 409 now, before the stream starts
    events = stream_mytravel(body.message, body.conversation, paid)
    return live(events, body.conversation, paid)
```

`pop` retire le jeton au message suivant, quoi qu'il arrive : un jeton sert une fois. `secrets.compare_digest` compare sans trahir, par sa durée, combien de caractères étaient justes. Et si le modèle payant sature à son tour, plus d'offre : on ne repropose pas une solution qui vient d'échouer.

Reste à faire savoir à `get_chat_model`, tout au fond, que **cette** question a le droit de payer. Ma première idée était une variable globale : deux voyageurs en même temps se seraient mélangés. Ma deuxième, un `ContextVar`, une variable que chaque requête voit à sa façon. Elle a marché, jusqu'au streaming. Le serveur lit le flux morceau par morceau, et chaque morceau est produit dans un contexte neuf : la valeur posée au début était perdue avant Synthèse. La bonne place, c'est la **configuration du graphe**, celle qui porte déjà `thread_id` : `run` y ajoute `"paid": paid`, et LangGraph la transmet à chaque nœud, agents en parallèle compris.

<!-- code: mytravel/app/modele.py 37-51 -->
```python
def paid():
    """True in a graph run the traveler agreed to pay for."""
    try:
        return get_config()["configurable"].get("paid", False)
    except RuntimeError:  # outside a graph: never
        return False


def get_chat_model(model=MODEL):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is missing: copy "
                           ".env.example to .env, paste your key.")
    if paid():
        model = PAID_MODEL
```

`get_config()` rend la configuration du graphe en cours. Hors d'un graphe, il lève `RuntimeError`, et la réponse est non : on ne paie jamais par accident. Aucun nœud ne sait qu'il tourne sur un modèle payant.

La page, ensuite. Quand l'événement `error` porte `paid_offer`, `call` ouvre `payCard` :

<!-- code: mytravel/static/index.html 299-317 -->
```html
// Every free model is busy: say what it costs before paying.
function payCard(model, token) {
  const card = bubble("bot confirm",
    "Les modèles gratuits sont saturés. Je peux répondre avec " +
    "**" + model + "**, un modèle payant : quelques centimes, " +
    "pris sur ton crédit OpenRouter. On y va ?");
  for (const [label, yes] of [["Oui, quelques centimes", true],
                              ["Non, j'attends", false]]) {
    const button = document.createElement("button");
    button.textContent = label;
    button.onclick = () => {
      if (busy) return;
      card.remove();
      if (!yes) return retryLater();
      call("/api/chat", {message: lastQuestion, paid: token});
    };
    card.appendChild(button);
  }
}
```

Même forme que la carte de réservation : le texte, deux boutons, rien ne part sans clic. Le « oui » renvoie la dernière question avec le jeton reçu. Le « non » lance `retryLater` : un compte à rebours d'une minute, puis la même question repart, toujours gratuite. Si le voyageur pose une autre question pendant l'attente, `stopCountdown`, appelé au début de `call`, annule le réessai : l'ancienne question ne repart pas derrière son dos.

> ⚠️ **Piège classique** — Basculer en silence sur le modèle payant « pour rendre service ». Le voyageur découvre la facture plus tard, et ne te fait plus confiance. Un coût, comme une réservation, se valide avant.

> ⚠️ **Piège classique** — Prendre le modèle le moins cher partout parce que « ça a l'air de marcher ». Un modèle trop faible pour Mission choisit les mauvais agents, et toute la suite est fausse. Économise là où l'évaluation montre que la qualité tient, nulle part ailleurs.

## QCM

**1.** Où part la plus grande partie des appels dans un plan complet ?

- **a)** Dans Mission
- **b)** Dans les spécialistes
- **c)** Dans Synthèse
- **d)** Dans la page web

**2.** Pourquoi la clé du cache contient-elle la liste des domaines ?

- **a)** Pour que le cache soit plus gros
- **b)** Parce qu'une même requête sur d'autres sites donne d'autres résultats
- **c)** Parce que SQLite l'exige
- **d)** Pour qu'une recherche d'hôtels ne renvoie pas une page de visa

**3.** Pourquoi un résultat vide n'est-il jamais mis en cache ?

- **a)** Parce que ce peut être une panne passagère
- **b)** Parce que SQLite refuse les listes vides
- **c)** Pour retenter à la question suivante
- **d)** Pour économiser de la place

**4.** Quel modèle reçoivent Mission et Synthèse ?

- **a)** Le modèle rapide, `MODELE_RAPIDE`
- **b)** Le modèle principal, `MODELE`
- **c)** Le modèle payant, toujours
- **d)** Celui que choisit la page

**5.** Pourquoi le serveur exige-t-il un jeton pour passer au modèle payant ?

- **a)** Pour qu'une requête écrite à la main ne puisse pas dépenser ton crédit
- **b)** Pour que le choix ne serve qu'une fois
- **c)** Parce qu'OpenRouter l'exige
- **d)** Pour chiffrer la question

**6.** Pourquoi le choix payant voyage-t-il dans la configuration du graphe plutôt que dans un `ContextVar` ?

- **a)** Parce que chaque morceau du flux est produit dans un contexte neuf
- **b)** Parce que LangGraph transmet sa configuration à chaque nœud, agents parallèles compris
- **c)** Parce que les `ContextVar` sont interdits en Python 3
- **d)** Pour que la page puisse le lire

**7.** Comment sais-tu qu'un modèle moins cher ne dégrade pas myTravel ?

- **a)** Le prix baisse sur la page *Activity*
- **b)** `python evaluate.py` donne le même score avant et après
- **c)** Le modèle le dit
- **d)** On ne peut pas le savoir

**Réponses.** Q1 : b · Q2 : b, d · Q3 : a, c · Q4 : b · Q5 : a, b · Q6 : a, b · Q7 : b

## Ce qu'il faut retenir

1. Un appel se paie au token. Les spécialistes font la majorité des appels, les pages lues pèsent le plus.
2. Le cache, dans `search_web`, sert tous les outils d'un coup ; il ne garde jamais un résultat vide, ni un prix.
3. Le routage donne un petit modèle aux tâches simples, le meilleur à Mission et Synthèse : une variable d'environnement suffit, grâce à OpenRouter.
4. Un changement de modèle se juge à l'évaluation, pas à l'impression.
5. Dépenser l'argent du voyageur se demande avant, avec un jeton à usage unique, et le choix voyage dans la configuration du graphe.

**Au chapitre suivant :** les vols du chapitre 11 et les hôtels du chapitre 10, enfin ensemble : des séjours clé en main, avec un seul prix, aux jours les moins chers. Puis le bilan.

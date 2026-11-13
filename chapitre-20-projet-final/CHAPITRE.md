# Chapitre 20 — Séjours clé en main et bilan

> **Dossier GitHub associé :** `chapitre-20-projet-final/`

**À la fin de ce chapitre, tu sauras :**

- combiner les vols du chapitre 11 et les hôtels du chapitre 10 en **séjours clé en main**, avec un seul total ;
- chercher les jours les moins chers pour un voyageur flexible ;
- classer des séjours au **rapport qualité-prix**, et pas seulement au prix ;
- écrire un nœud de graphe qui ne fait que du code, sans modèle, et qui déplace le voyage avant les agents ;
- dire ce que la version 1.0 sait faire, et par où la faire grandir.

## Le séjour à 499 €

Ouvre Voyage Privé ou lastminute. En haut de la page, il n'y a ni vol ni hôtel : il y a des **séjours**. « Lisbonne, 4 nuits, vol + hôtel 4 étoiles, 499 € par personne. » Un prix, un bouton. Personne n'a envie d'additionner lui-même un vol, quatre nuits et deux chambres.

myTravel sait déjà trouver un vrai vol (chapitre 11) et le vrai prix d'un hôtel (chapitre 10). Il ne sait pas encore les mettre ensemble. Et il ne sait pas profiter d'une phrase que les voyageurs disent tout le temps : « je peux décaler de quelques jours ».

## Le total, pas deux classements

Le vol le moins cher ne fait pas toujours le séjour le moins cher. Un vol à 90 € le samedi peut tomber sur un week-end où l'hôtel double ses prix. C'est tout l'intérêt de calculer le **total**, plutôt que deux classements séparés.

Et le moins cher n'est pas toujours le meilleur : 500 € dans un hôtel noté 4,5 valent mieux que 450 € dans un hôtel noté 3,5. Diviser le total par la note, c'est la règle la plus simple qui le dise : le **prix par point de note**.

Un nœud de code, `best_stays`, s'en charge entre Mission et les agents :

1. avec un vol, il prend les allers-retours réels autour des dates demandées (la fonction `around` du chapitre 11, avec le nombre de jours que le voyageur accepte de décaler, dix au plus) ; sans vol, les dates demandées et quatre décalages, pour le même nombre de nuits ;
2. il garde les quatre paires de jours aux vols les moins chers, et les cinq hôtels de la ville au meilleur rapport qualité-prix selon TripAdvisor (`best_hotels` du chapitre 10) ;
3. il demande le prix de chaque hôtel à chaque paire de jours, et fait le total : vols de tous les voyageurs, plus les nuits de toutes les chambres ;
4. il classe les séjours au prix par point de note, propose les trois meilleurs, un par hôtel, et **déplace le voyage** sur les jours du premier.

À côté, il pose la question aux agences de voyages elles-mêmes. Une recherche limitée à six sites (ovoyages, Carrefour Voyages, Promovacances, Leclerc Voyages, lastminute, Voyage Privé) rapporte des extraits qui donnent déjà l'hôtel, la formule (vol, hôtel, transfert, repas) et le prix. Ce prix-là est celui du **catalogue** (« dès 302 € par personne »), pas celui de tes dates : le rapport le dit, et Synthèse ne l'ajoute jamais à un total.

> 💡 **À retenir** — Tout ce qui se calcule est calculé par du code : un total, un classement, des dates déplacées. Le modèle reçoit le résultat et l'explique. Aucun appel au modèle n'est nécessaire pour additionner des prix.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

| Fichier | Ce qui change |
|---|---|
| `app/stays.py` | NOUVEAU : `stays`, les séjours vol et/ou hôtel avec leur total ; `value` et `choices`, le classement ; `stay_text`, le texte ; `packages`, les séjours des agences |
| `app/graph.py` | le champ `flexible` de la fiche, et le nœud `best_stays` entre Mission et les agents |
| `app/sources.py` | le groupe `"packages"` : six agences de voyages de confiance |

### Lancer le chapitre

```bash
cd chapitre-20-projet-final/mytravel
uvicorn server:app --reload
pytest                    # 81 passed
```

Avec ton `TRAVELPAYOUTS_TOKEN` dans le `.env`, demande : « Un séjour à Lisbonne à deux, vol et hôtel, du 3 au 7 février depuis Paris, je suis flexible de trois jours. » Regarde la bulle d'attente : « Séjours clé en main » apparaît juste après Mission, avant les agents. La réponse s'ouvre sur trois séjours, chacun avec ses dates, son vol, son hôtel, leurs vendeurs, leurs liens et un total. Si les meilleurs jours ne sont pas les tiens, la réponse le dit, avec le total aux dates demandées. En dessous, les séjours des agences, à leur prix catalogue.

Sans jeton, demande seulement un hôtel avec des dates flexibles : les séjours se font sans vol, aux jours où l'hôtel coûte le moins.

### À toi d'abord

Ouvre `app/graph.py`, trouve `after_mission`. Dans quels cas le graphe passe-t-il par `best_stays` ? Une question de visa y passe-t-elle ?

## On lit le code ensemble

### `after_mission` : qui passe par les séjours

<!-- code: mytravel/app/graph.py 176-196 -->
```python
def after_mission(state):
    """The road after Mission: a question, a booking, or agents."""
    trip = state["trip"]
    if trip["question"]:
        return "ask_back"
    if trip["booking"]:
        return "confirm"
    if trip["start"] and ("hotel" in trip["agents"] or (
            "transport" in trip["agents"] and trip["flexible"])):
        return "best_stays"
    return send_agents(state)


def send_agents(state):
    trip = state["trip"]
    request = state["messages"][-1].content
    # Send = "run this node with this input": one per agent, and
    # LangGraph runs them at the same time.
    return [Send("agent", {"name": name, "trip": trip,
                           "request": request})
            for name in trip["agents"]] or "synthesis"
```

Réponse à ta question : `best_stays` n'est pris que si le voyage a des dates **et** que le voyageur veut un hôtel, ou un vol avec des dates flexibles. Une question de visa n'a pas besoin de prix. Un vol à dates fixes reste à l'agent Transports, qui ajoute la voiture. Le reste de l'ancien `after_mission` devient `send_agents`, que `best_stays` réutilise : après les séjours, les agents qui restent partent comme avant.

Le nombre de jours de souplesse vient de la fiche : un champ `flexible` de plus dans `Trip`, que Mission remplit quand il lit « je peux décaler de trois jours ». Zéro si les dates sont fixes.

### `stay` et `stays` : le total d'un séjour

<!-- code: mytravel/app/stays.py 33-48 -->
```python
def stay(out, back, fare, hotel, adults):
    """A flight, a hotel or both on the same days, and the
    total."""
    nights = (date.fromisoformat(back)
              - date.fromisoformat(out)).days
    found = {"out": out, "back": back, "nights": nights, "total": 0}
    if fare:
        found.update(fare=fare, total=fare["price"] * adults)
    if hotel:
        rate = hotels.night(hotel, out, back, adults)
        if rate is None:  # full on these days: out of the ranking
            return None
        found.update(hotel=hotel, rate=rate)
        found["total"] += (rate["rate"] * hotels.rooms(adults)
                           * nights)
    return found
```

`stay` fait l'addition, avec ce que le voyageur a demandé : le vol par adulte fois le nombre d'adultes, plus le prix de la nuit fois les chambres fois les nuits. Sans vol, `fare` vaut `None` ; sans hôtel, `hotel` aussi. Un hôtel complet à ces dates (`None`) disparaît du classement, au lieu de compter pour zéro.

<!-- code: mytravel/app/stays.py 51-73 -->
```python
def stays(trip):
    """Every flight and hotel pair on the cheapest days, the
    cheapest total first."""
    wanted, days = trip["agents"], []
    if "transport" in wanted:  # the days of the cheapest flights
        found = flights.around(trip["origin"], trip["destination"],
                               trip["start"], trip["end"],
                               trip["flexible"])
        days = [(f["departure_at"][:10], f["return_at"][:10], f)
                for f in found[:DAYS_PER_STAY]]
    if not days and "hotel" in wanted:  # no flight: hotels alone
        # Moved only if no flight was asked: else, the days asked.
        shift = 0 if "transport" in wanted else trip["flexible"]
        days = [(*pair, None) for pair in shifted(
            trip["start"], trip["end"], shift)]
    chosen = (hotels.best_hotels(trip["destination"])
              if "hotel" in wanted else [None])
    pairs = [(*day, hotel) for day in days for hotel in chosen]
    # One request per pair: sent together, not one after another.
    with ThreadPoolExecutor() as pool:
        found = pool.map(
            lambda pair: stay(*pair, trip["travelers"]), pairs)
    return sorted(filter(None, found), key=lambda s: s["total"])
```

`stays` fabrique les paires (jours, hôtel). Quatre paires de jours et cinq hôtels, ça fait vingt demandes à Xotelo : le `ThreadPoolExecutor` du chapitre 10 les envoie ensemble. Remarque le cas « vol demandé, aucun vol vu » : on ne déplace pas les dates pour l'hôtel seul (`shift = 0`), sinon le voyageur aurait un hôtel à d'autres dates que le vol qu'il va chercher lui-même.

### `value` et `choices` : trois hôtels, pas trois fois le même

<!-- code: mytravel/app/stays.py 76-91 -->
```python
def value(stay):
    """Price for quality: euros per point of rating. 500 € at 4.5
    beats 450 € at 4: a better hotel is worth a little more."""
    hotel = stay.get("hotel")
    return stay["total"] / (hotel["review_summary"]["rating"]
                            if hotel else 1)


def choices(found):
    """The cheapest stay of each hotel, best value first: hotels
    to choose from, not the same hotel three times."""
    best = {}
    for stay in found:  # cheapest first: the first one stays
        hotel = stay.get("hotel") or {"key": stay["fare"]["link"]}
        best.setdefault(hotel["key"], stay)
    return sorted(best.values(), key=value)
```

`choices` garde le séjour le moins cher **de chaque hôtel** (la liste arrive triée par total, donc `setdefault` garde le premier), puis les classe avec `value`. Sans ce filtre, les trois premiers séjours auraient souvent été le même hôtel à trois dates, à deux euros près. Le voyageur veut choisir un hôtel, pas un jour.

### `best_stays` : déplacer le voyage avant les agents

<!-- code: mytravel/app/graph.py 199-217 -->
```python
def best_stays(state):
    """Flights and hotels priced together, by code, before the
    agents: the trip moves to the days of the best value stay."""
    get_stream_writer()("Séjours clé en main")
    trip = dict(state["trip"])
    try:
        found = stays(trip)
    except Exception as error:  # no token, unknown city: the agents
        log("best_stays_failed", error=str(error))
        found = []
    agencies = packages(trip["destination"])
    sold = []  # the agencies' packages, if any was found
    if agencies:
        sold = [("packages", "## Séjours des agences de voyages\n"
                 "Prix d'appel des catalogues, par personne, à "
                 "vérifier aux dates :\n" + agencies)]
    if not found:  # the agents search flights and hotels apart
        return {"steps": ["Séjours : aucune offre"],
                "reports": sold, "found": links_in(agencies)}
```

C'est un nœud de **code**, pas un agent : aucun modèle n'est appelé. Il s'annonce dans la page comme les agents, avec `get_stream_writer`. Si Travelpayouts ou Xotelo ne répond pas, l'erreur est consignée et la fiche garde ses dates et ses agents : une panne de prix ne doit pas casser le plan. Les séjours des agences, eux, partent dans tous les cas.

<!-- code: mytravel/app/graph.py 218-240 -->
```python
    asked = (trip["start"], trip["end"])
    before = next((s["total"] for s in found
                   if (s["out"], s["back"]) == asked), None)
    best = choices(found)[:3]
    trip["start"], trip["end"] = best[0]["out"], best[0]["back"]
    # The stays hold the hotels, and the flights if any was seen.
    done = ["hotel"] + ["transport"] * ("fare" in best[0])
    trip["agents"] = [name for name in trip["agents"]
                      if name not in done]
    report = "\n".join(
        ["## Séjours clé en main", "Prix réels vus, total pour "
         f"{trip['travelers']}, du meilleur rapport qualité-prix "
         "(prix par point de note) au moins bon :"]
        + [stay_text(s, trip["travelers"]) for s in best])
    if (trip["start"], trip["end"]) != asked:
        report += (f"\nDates déplacées au {trip['start']} -> "
                   f"{trip['end']}, {nights(trip)} nuits au lieu "
                   f"de {nights(state['trip'])}. Aux dates "
                   "demandées : " +
                   (f"{before} €." if before else "aucune offre."))
    return {"trip": trip, "steps": ["Séjours clé en main"],
            "reports": [("stays", report), *sold],
            "found": links_in(report + agencies)}
```

`best[0]` donne les jours du premier séjour : la fiche part à ces dates, et la météo sera cherchée aux bonnes. `before` retrouve le meilleur total aux dates demandées, pour que le voyageur voie ce qu'il gagne à bouger. Puis les agents Transports et Hôtel sortent de la liste : leur travail est fait (Transports reste si aucun vol n'a été vu, pour le dire et donner le lien de recherche). Chaque agent en moins, ce sont deux ou trois appels au modèle économisés, et pas de deuxième prix pour le même hôtel.

Enfin, `links_in(report + agencies)` ajoute les liens des séjours aux adresses de confiance du chapitre 14 : ils passeront le filtre de `check_output`.

> ⚠️ **Piège classique** — Additionner un prix catalogue et un prix réel. « Dès 302 € par personne » chez une agence, c'est le prix d'appel d'une semaine creuse, pas le tien. Le rapport des agences le dit en toutes lettres, et le prompt de Synthèse interdit de l'ajouter à un total.

## Le bilan : myTravel 1.0

Fais le compte de ce que tu as construit depuis le chapitre 7.

- Une **page web** que n'importe qui ouvre avec un lien, qui répond **en direct** : chaque agent au moment où il démarre, la réponse mot à mot.
- Une **API** qui valide tout ce qu'elle reçoit, et une **mémoire** par conversation : ce que le voyageur dit de lui n'est jamais redemandé.
- Des **sources officielles** lues le jour même, filtrées par le code, citées dans chaque réponse. Aucune donnée en dur.
- De **vrais prix** : la nuit d'hôtel du jour chez son vendeur, des offres de vol réelles avec leur date, jamais une estimation.
- **Sept agents** : Mission qui comprend et répartit, cinq spécialistes en parallèle, Synthèse qui assemble.
- Des **garde-fous** à l'entrée et à la sortie, et ton accord avant toute action.
- Une **sécurité** pensée contre un adversaire : injection de prompt, redirections, déluge de messages.
- Une **évaluation** qu'on rejoue, des **logs** qu'on lit, un **déploiement** en une commande, un **coût** mesuré.
- Des **séjours clé en main** : vol et hôtel réels, avec vendeurs, liens et un total, classés au rapport qualité-prix, aux meilleurs jours pour qui est flexible.

Ce n'est pas une démo. C'est un vrai assistant, avec les limites qu'on a dites honnêtement en route : des offres de vol vues par d'autres voyageurs, des prix d'hôtels lus chez un intermédiaire, un disque éphémère, une seule copie.

### Par où le faire grandir

Quelques pistes, de la plus simple à la plus ambitieuse :

- **Une vraie base** : Cloud SQL et le checkpointer PostgreSQL de LangGraph. Les conversations survivent aux redémarrages, et Cloud Run peut lancer plusieurs copies.
- **Des prix fermes** : brancher l'API d'un partenaire de réservation, le jour où tu en as un. `best_stays` garde la même place dans le graphe, seules `fares` et `night` changent.
- **D'autres langues** : les prompts demandent déjà de répondre dans la langue du voyageur. Il reste les listes de sites officiels, à compléter pays par pays.
- **Des comptes** : un profil retrouvé sur tous tes appareils, au lieu d'une conversation par navigateur. C'est un chantier de sécurité à part entière : mots de passe, données personnelles, droit à l'oubli.

## QCM

**1.** Pourquoi calculer le total d'un séjour plutôt que classer vols et hôtels séparément ?

- **a)** Parce que le vol le moins cher peut tomber les jours où l'hôtel est le plus cher
- **b)** Pour appeler moins souvent Xotelo
- **c)** Parce que le voyageur paie le total
- **d)** Parce que Travelpayouts l'exige

**2.** Que mesure `value` ?

- **a)** Le prix par point de note de l'hôtel
- **b)** Le nombre d'avis
- **c)** La distance au centre
- **d)** Une façon de préférer 500 € à 4,5 sur 450 € à 3,5

**3.** Pourquoi `best_stays` est-il un nœud de code et pas un agent ?

- **a)** Parce qu'additionner et classer des prix ne demande pas de modèle
- **b)** Parce que LangGraph interdit deux agents de suite
- **c)** Pour ne payer aucun appel au modèle à cette étape
- **d)** Parce que le code ne se trompe pas dans une addition

**4.** Quand le graphe passe-t-il par `best_stays` ?

- **a)** À chaque question
- **b)** Quand le voyage a des dates et que le voyageur veut un hôtel
- **c)** Quand il veut un vol avec des dates flexibles
- **d)** Pour une question de visa

**5.** Après `best_stays`, pourquoi l'agent Hôtel sort-il de la liste ?

- **a)** Son travail est fait : les séjours portent déjà les hôtels et leurs prix
- **b)** Pour économiser des appels au modèle
- **c)** Pour éviter deux prix différents pour le même hôtel
- **d)** Parce qu'il est en panne

**6.** Une agence affiche « dès 302 € par personne ». Que fait myTravel ?

- **a)** Il l'ajoute au total du séjour
- **b)** Il le donne comme prix catalogue, avec l'agence et son lien
- **c)** Il le présente comme le prix de tes dates
- **d)** Il ne l'ajoute jamais à un total

**Réponses.** Q1 : a, c · Q2 : a, d · Q3 : a, c, d · Q4 : b, c · Q5 : a, b, c · Q6 : b, d

## Ce qu'il faut retenir

1. Un séjour se juge sur son total, vol et hôtel ensemble, rapporté à la note de l'hôtel.
2. Un voyageur flexible gagne à décaler : le code cherche les meilleurs jours et le dit, avec le total aux dates demandées.
3. Un nœud de code a sa place dans un graphe d'agents : il calcule, il déplace le voyage, et les agents qui restent travaillent sur le résultat.
4. Un prix catalogue reste un prix catalogue : jamais ajouté à un total.
5. myTravel 1.0 est un vrai assistant : réponses en direct, sources officielles, vrais prix, agents en parallèle, garde-fous, sécurité, évaluation, logs, déploiement. Ses limites sont connues, et le chemin pour les lever est tracé.

Tu as maintenant tout ce qu'il faut pour construire ton propre agent : la boucle comprise à la main, les frameworks, et un projet complet à adapter. Ouvre `chapitre-20-projet-final/mytravel/`, change une liste de sites, un prompt, un outil, et fais-en le tien.

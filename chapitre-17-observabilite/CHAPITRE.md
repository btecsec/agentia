# Chapitre 17 — Observabilité : voir ce que font les agents

> **Dossier GitHub associé :** `chapitre-17-observabilite/`

**À la fin de ce chapitre, tu sauras :**

- dire ce qu'il faut tracer dans un système d'agents, et pourquoi ;
- écrire des logs structurés, une ligne JSON par événement ;
- mesurer la durée d'une recherche et la consigner ;
- montrer au voyageur quels agents ont travaillé sur sa réponse ;
- brancher LangSmith pour voir chaque appel au modèle, sans changer une ligne de code.

## « Hier, ça marchait »

Mardi matin, un voyageur écrit : « Votre assistant m'a dit qu'il n'y avait aucune information officielle sur le Maroc. » Tu essaies : chez toi, ça marche. Que s'est-il passé chez lui ?

Peut-être que DuckDuckGo n'a rien renvoyé à ce moment-là. Peut-être que Mission n'a pas appelé Administration. Peut-être que la page du ministère a mis vingt secondes à répondre. Sans trace, tu ne le sauras jamais. Tu vas deviner, corriger au hasard, et le problème reviendra.

Un agent est un programme qui prend des décisions. Ces décisions ne sont pas dans ton code, elles sont dans les réponses du modèle, différentes à chaque fois. L'**observabilité**, c'est la capacité de reconstituer après coup ce qui s'est passé : qui a décidé quoi, quel outil a été appelé, avec quel résultat, en combien de temps.

## Trois niveaux de traces

**Les logs structurés.** Un *log*, c'est une ligne écrite à chaque événement important. *Structuré* veut dire qu'elle est en JSON, avec des champs nommés, plutôt qu'en phrase libre. « Recherche OK » ne se filtre pas ; `{"event": "search", "query": "visa Maroc", "results": 0, "seconds": 1.8}` se filtre, se compte, se trie. myTravel en écrit quatre sortes : `mission` (la destination comprise et les agents choisis), `search` (chaque recherche, son nombre de résultats et sa durée), `search_failed` (le moteur en panne) et `model_error`.

Ces lignes partent sur la **sortie standard**, avec `print`. Ça paraît primitif, et c'est voulu : en local, tu les lis dans le terminal ; sur Google Cloud Run, chaque ligne JSON de la sortie standard devient automatiquement une entrée de *Cloud Logging*, filtrable par champ. Le champ `severity` est celui que Google lit pour classer les lignes (INFO, ERROR).

**Les étapes, dans la page.** Le chapitre 16 a ajouté `steps` à chaque réponse. Ce chapitre les affiche : sous chaque réponse, des pastilles bleues, « Mission · Administration · Synthèse ». Le voyageur voit qui a travaillé, et ton voyageur de mardi aurait pu te dire : « Il n'y avait que Mission et Synthèse. » Diagnostic en une phrase : Mission n'a pas appelé Administration.

**Les traces complètes, avec LangSmith.** **LangSmith** est le service d'observabilité de l'équipe qui fait LangChain et LangGraph. Il enregistre chaque appel au modèle (le prompt exact, la réponse, les tokens, la durée), chaque outil, chaque nœud du graphe, et les affiche en arbre. Il a une offre gratuite. Et il ne demande **aucun code** : LangChain l'active tout seul quand il voit deux variables d'environnement.

> 💡 **À retenir** — Trace les décisions (qui a choisi quoi), les appels externes (combien de temps, combien de résultats) et les erreurs. Pas les données personnelles : ni la fiche du voyage, ni le texte complet des messages dans tes logs.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

| Fichier | Ce qui change |
|---|---|
| `app/logs.py` | NOUVEAU : `log(event, **fields)`, une ligne JSON |
| `app/web.py` | `search_web` mesure et consigne chaque recherche |
| `app/graph.py` | `mission` consigne la destination et les agents choisis |
| `server.py` | `model_error` part dans les logs au lieu d'un `print` |
| `static/index.html` | les pastilles bleues des agents sous chaque réponse |

### Lancer le chapitre

```bash
cd chapitre-17-observabilite/mytravel
uvicorn server:app --reload
pytest                    # 72 passed
```

Pose « Il me faut un visa pour le Maroc ? » et regarde le terminal :

```text
{"time": "...", "severity": "INFO", "event": "mission",
 "destination": "Maroc", "agents": ["admin"]}
{"time": "...", "severity": "INFO", "event": "search",
 "query": "visa Maroc passeport français", "results": 4,
 "seconds": 1.42}
```

(Chaque événement tient sur une seule ligne ; on l'a coupé ici pour la page.) Dans la page, sous la réponse : « Mission · Administration · Synthèse ».

Pour LangSmith, crée un compte gratuit sur smith.langchain.com, une clé dans *Settings*, puis ajoute au `.env` :

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
```

Relance le serveur, pose une question, ouvre LangSmith : tu vois l'arbre complet. Le graphe, Mission et sa sortie structurée, chaque agent, chaque outil avec ses arguments, et la Synthèse.

> ⚠️ **Piège classique** — Activer LangSmith en production sans y penser. Il enregistre tout, y compris les messages des voyageurs et ce qu'ils disent d'eux, chez un service tiers. Pour un vrai produit, c'est une décision à prendre avec ta politique de confidentialité, pas une option à laisser allumée par défaut.

### À toi d'abord

Ouvre `app/web.py` et trouve les deux appels à `log`. Puis cherche : où est mesurée la durée, et pourquoi avec `time.perf_counter()` et pas `time.time()` ?

## On lit le code ensemble

### `app/logs.py` : toute l'infrastructure en cinq lignes

<!-- code: mytravel/app/logs.py 12-16 -->
```python
def log(event, **fields):
    line = {"time": datetime.now(timezone.utc).isoformat(),
            "severity": "INFO", "event": event, **fields}
    print(json.dumps(line, ensure_ascii=False, default=str),
          flush=True)
```

`**fields` accepte n'importe quels champs nommés : `log("search", query=..., results=...)`. Pas de format à déclarer d'avance, chaque événement porte ce qui lui est utile.

Trois paramètres, trois raisons. `datetime.now(timezone.utc)` : l'heure en UTC, toujours, parce qu'un serveur en Belgique et un autre aux États-Unis doivent pouvoir comparer leurs logs. `ensure_ascii=False` : « Pérou » reste lisible au lieu de `Pérou`. `default=str` : si un champ n'est pas sérialisable en JSON (une date, un objet), on écrit sa version texte au lieu de planter. Et `flush=True` force l'écriture tout de suite : sans lui, Python garde parfois les lignes en mémoire, et quand le serveur plante, les dernières, celles qui expliquent le plantage, sont perdues.

Pourquoi pas le module `logging` de Python ? Il est plus riche (niveaux, filtres, destinations multiples), et un projet plus gros l'utiliserait. Ici, il ajouterait une configuration à comprendre pour un résultat identique : une ligne JSON sur la sortie standard. Je garde l'outil le plus simple qui fait le travail.

### `search_web` : mesurer un appel externe

<!-- code: mytravel/app/web.py 61-74 -->
```python
def search_web(query, domains, max_results=5):
    """Results from the allowed sites only. Never raises."""
    started = time.perf_counter()
    try:
        found = search_engine(query, domains)
        # Ads and random blogs are filtered here, whatever engine.
        results = [r for r in found
                   if is_allowed(r["url"], domains)][:max_results]
    except Exception as error:  # engine down, quota, no network
        log("search_failed", query=query, error=str(error))
        return []
    log("search", query=query, results=len(results),
        seconds=round(time.perf_counter() - started, 2))
    return results
```

Réponse à ta question : `time.perf_counter()` est une horloge faite pour mesurer des durées, précise et qui ne recule jamais. `time.time()` donne l'heure du système, qui peut sauter d'une seconde quand l'ordinateur se resynchronise. Pour un chronomètre, `perf_counter`.

Regarde ce que le log `search` contient : `results` compte les résultats **après** le filtre. C'est le chiffre qui compte. Un `results: 0` répété sur la même requête te dit que le moteur ne trouve rien sur les sites de confiance : il faut reformuler la requête dans l'outil, ou ajouter un domaine. Le voyageur de mardi, c'était ça.

Et `search_failed` garde l'erreur, ce que le chapitre 9 jetait avec `except Exception: return []`. L'agent continue de ne pas planter, mais tu sais désormais pourquoi il n'a rien trouvé.

### `mission` : consigner la décision

<!-- code: mytravel/app/graph.py 129-146 -->
```python
def mission(state):
    get_stream_writer()("Mission")  # shown now, in the page
    model = get_chat_model().with_structured_output(
        Trip, method="function_calling")
    prompt = MISSION.format(today=date.today())
    for _ in range(2):  # a free model may answer nothing
        try:
            trip = model.invoke([SystemMessage(prompt),
                                 *state["messages"]])
        except ValueError:  # the fiche does not match Trip
            trip = None
        if trip is not None:
            break
    if trip is None:  # twice nothing, or prose
        trip = Trip(question=UNREAD)
    trip.start, trip.end = not_past(trip.start), not_past(trip.end)
    log("mission", destination=trip.destination,
        agents=trip.agents)
```

Si je ne devais garder qu'un log, ce serait celui-là. La décision la plus importante d'une question, c'est le choix des agents, et c'est la plus fragile : elle dépend entièrement du modèle. Remarque ce qui n'est **pas** consigné : la fiche complète, les messages. Ils contiennent la nationalité, parfois des détails personnels. Les logs sont lus par des humains, gardés des semaines, parfois copiés dans un ticket. On y met ce qui sert au diagnostic, rien de plus.

### La page : les pastilles

<!-- code: mytravel/static/index.html 178-197 -->
```html
// The agents that worked on the answer, in order, and in
// parentheses the tools each one called.
function stepPills(div, steps) {
  if (!steps.length) return;
  const row = pills(div);
  row.append("Agent appelé :");
  for (const step of steps) {
    const [name, tools] = step.split(" (");
    const pill = document.createElement("span");
    pill.className = "chip step";
    pill.textContent = name;
    if (tools) {
      const used = document.createElement("span");
      used.className = "tools";
      used.textContent = ` (${tools}`;
      pill.appendChild(used);
    }
    row.appendChild(pill);
  }
}
```

La rangée commence par « Agent appelé : ». Chaque étape arrive sous la forme `"Hôtel (hotel_offers, hotel_links)"` : `split(" (")` sépare l'agent de ses outils, et les outils vont dans un `span` de classe `tools`, d'une autre couleur. `textContent` et pas `innerHTML` : un nom d'étape est du texte, il le reste. La fonction partage `pills` avec les sources : une rangée de pastilles, deux contenus. Pendant l'attente, les pastilles du chapitre 13 annonçaient chaque agent au départ, puis disparaissaient avec la bulle d'attente. Celles-ci restent sous la réponse, avec les outils : c'est la trace qu'on relit après coup.

## QCM

**1.** Pourquoi des logs en JSON plutôt qu'en phrases ?

- **a)** Parce qu'on peut filtrer, compter et trier par champ
- **b)** Parce que Python ne sait pas écrire de phrases
- **c)** Parce que Cloud Logging lit chaque ligne JSON comme une entrée structurée
- **d)** Pour qu'ils soient plus courts

**2.** Que ne faut-il pas mettre dans les logs de myTravel ?

- **a)** La durée d'une recherche
- **b)** La nationalité du voyageur
- **c)** Les agents choisis par Mission
- **d)** Le texte complet des messages

**3.** Le log montre `"event": "search", "results": 0` dix fois de suite pour la même requête. Que soupçonner ?

- **a)** Le modèle est saturé
- **b)** Aucun résultat ne vient des sites de confiance : la requête ou la liste de domaines est à revoir
- **c)** La page web est cassée
- **d)** Le checkpointer est plein

**4.** Pourquoi `flush=True` dans `log` ?

- **a)** Pour écrire la ligne tout de suite
- **b)** Pour ne pas perdre les dernières lignes si le serveur plante
- **c)** Pour chiffrer les logs
- **d)** Pour aller plus vite

**5.** Que faut-il pour activer LangSmith ?

- **a)** Réécrire les nœuds du graphe
- **b)** Deux variables d'environnement
- **c)** Un compte et une clé
- **d)** Installer un serveur

**6.** Un voyageur dit « il n'y avait que Mission et Synthèse ». Qu'en déduis-tu ?

- **a)** Mission n'a choisi aucun spécialiste
- **b)** La recherche web est en panne
- **c)** Il faut regarder le log `mission` de ce moment-là
- **d)** Synthèse a répondu sans rapport

**Réponses.** Q1 : a, c · Q2 : b, d · Q3 : b · Q4 : a, b · Q5 : b, c · Q6 : a, c, d

## Ce qu'il faut retenir

1. Un agent décide à chaque question : sans trace, impossible de savoir après coup ce qui s'est passé.
2. Un log structuré est une ligne JSON par événement, avec des champs nommés. Sur la sortie standard, il devient une entrée de Cloud Logging sans aucun réglage.
3. On trace les décisions, les appels externes (durée, résultats) et les erreurs ; jamais les données personnelles.
4. Les étapes affichées dans la page font du voyageur un témoin utile.
5. LangSmith donne l'arbre complet des appels sans changer le code, et sa mise en production se décide avec la politique de confidentialité.

**Au chapitre suivant :** myTravel tourne sur ta machine, observé, évalué, protégé. Il est temps qu'il tourne ailleurs : une image Docker, des tests à chaque `git push`, et Google Cloud Run.

# Chapitre 9 — Recherche web officielle : visas, passeport, bagages, santé

> **Dossier GitHub associé :** `chapitre-09-recherche-web/`

**À la fin de ce chapitre, tu sauras :**

- expliquer pourquoi un modèle ne doit jamais répondre de mémoire sur un visa ;
- brancher une recherche web en direct, avec Tavily ou DuckDuckGo ;
- limiter cette recherche à une liste de sites de confiance, et vérifier chaque lien ;
- lire le texte d'une page avant de la citer ;
- donner des outils à un agent LangChain et le laisser choisir quand s'en servir ;
- montrer dans la page chaque outil au moment où l'agent l'appelle.

## Le formulaire qui n'existait plus

Tu demandes à un assistant ce qu'il faut pour entrer en Thaïlande. Réponse sûre : passeport valide, rien d'autre. On arrive à l'aéroport de Bangkok sans le formulaire d'arrivée en ligne devenu obligatoire quelques mois plus tôt. Une heure de file pour le remplir sur son téléphone, au guichet, en pleine nuit.

L'assistant n'avait pas menti. Il avait répondu avec ce qu'il avait lu pendant son entraînement, deux ans avant. Pour un modèle, le monde s'arrête à la date de ses données. Pour un voyageur, une règle d'il y a deux ans est une règle fausse.

La solution n'est pas de recopier les règles dans un fichier : il faudrait le mettre à jour chaque semaine, pour deux cents pays. La solution, c'est d'aller lire **la page officielle, le jour de la question**. C'est ce que fait myTravel à partir de ce chapitre.

## Chercher, filtrer, lire, citer

Un **moteur de recherche** renvoie des titres, des adresses et des extraits (*snippets*). Trois problèmes, dans l'ordre.

**Les résultats ne sont pas tous fiables.** Sur « visa Japon », le premier résultat est souvent une publicité pour un service payant, puis un blog de 2019. myTravel garde donc une **liste de domaines de confiance** par sujet : diplomatie.gouv.fr et france-visas.gouv.fr pour l'entrée dans un pays, pasteur.fr et who.int pour la santé, la DGAC et la compagnie aérienne pour les bagages, plus les sites gouvernementaux des destinations (`go.jp` pour le Japon, `gov.uk` pour le Royaume-Uni). Tout résultat hors liste est jeté, par le code, quoi que pense le modèle.

**Un extrait n'est pas une source.** Il fait deux lignes, coupées au milieu d'une phrase. L'agent doit donc pouvoir **lire la page** : on télécharge le HTML, on garde le texte visible, sans menus ni scripts.

**Le moteur peut tomber en panne.** Quota atteint, réseau coupé. Dans ce cas, l'outil le dit (« aucune source officielle trouvée »), et le prompt de l'agent lui interdit de deviner.

Pour le moteur, deux choix. **Tavily** est un moteur de recherche conçu pour les agents : il accepte une liste de domaines (`include_domains`) et renvoie des extraits propres. Il demande une clé, gratuite pour mille recherches par mois. Sans clé, myTravel se rabat sur **DuckDuckGo**, via la bibliothèque `ddgs`, qui ne demande rien mais varie un peu plus d'un essai à l'autre. Le reste du code ne voit pas la différence.

Enfin, ce chapitre donne ses premiers **outils** à l'agent. Avec `create_agent`, c'est la boucle du chapitre 1 : le modèle lit la description des outils, décide d'en appeler un, lit le résultat, recommence ou répond.

> 💡 **À retenir** — Le modèle choisit *quoi* chercher. Le code décide *où* il a le droit de chercher. La liste des sites de confiance ne se négocie pas avec un prompt.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

```text
chapitre-09-recherche-web/mytravel/
├── server.py
├── static/index.html
├── app/
│   ├── assistant.py   ← + la liste TOOLS, un prompt plus strict
│   ├── tools.py       ← NOUVEAU : 2 outils officiels
│   ├── web.py         ← NOUVEAU : chercher, filtrer, lire une page
│   ├── sources.py     ← NOUVEAU : les sites de confiance
│   ├── memory.py
│   └── modele.py
└── tests/             ← 17 tests
```

| Fichier | Rôle |
|---|---|
| `app/sources.py` | la politique de confiance : quels domaines, pour quel sujet |
| `app/web.py` | parle au moteur, filtre les résultats, lit le texte d'une page |
| `app/tools.py` | ce que l'agent voit : deux outils et leur description |
| `app/assistant.py` | donne les outils à l'agent, lui interdit de répondre de mémoire |

### Lancer le chapitre

```bash
cd chapitre-09-recherche-web/mytravel
uvicorn server:app --reload
pytest                    # 17 passed
```

Dis « Je suis française » et demande : « Il me faut un visa pour le Japon, 10 jours en mars ? ». La réponse arrive plus lentement qu'avant : l'agent cherche, lit, puis répond. Elle contient des liens. Clique : ce sont de vraies pages de france-visas.gouv.fr ou de diplomatie.gouv.fr.

Essaie aussi « Je peux prendre un flacon de 200 ml en cabine ? » : cette fois, l'agent choisit le sujet `baggage`, et la source est la DGAC ou Air France.

Pour Tavily, ajoute `TAVILY_API_KEY=tvly-...` dans le `.env` de la racine et relance le serveur. Rien d'autre ne change.

### À toi d'abord

Ouvre `app/web.py` et réponds à une question précise : si DuckDuckGo renvoie une publicité en premier, à quelle ligne est-elle jetée ? Puis ouvre `app/tools.py` et lis seulement les docstrings des deux fonctions. Tu lis exactement ce que le modèle lit.

## On lit le code ensemble

### Je pars de ce que voit le modèle : `app/tools.py`

Cette fois, je ne commence pas par `server.py` : rien n'y a changé. Je commence par ce qui est nouveau du point de vue de l'agent, ses outils.

<!-- code: mytravel/app/tools.py 44-55 -->
```python
@tool
def search_official(topic: str, query: str) -> str:
    """Search official government and health websites.

    topic is one of: entry (visa, passport, entry rules), health
    (vaccines, health risks), baggage (luggage, customs).
    """
    domains = OFFICIAL.get(topic, OFFICIAL["entry"])
    results = search_web(query, domains)
    if not results:
        return "No official source found. Say so; do not guess."
    return show(results)
```

Le décorateur `@tool` fait ce que tu faisais à la main au chapitre 1 : il lit le nom de la fonction, ses paramètres typés et sa docstring, et en fabrique la description JSON que le modèle reçoit. La docstring est donc un **mode d'emploi pour le modèle**. Elle dit quoi mettre dans `topic`, et le modèle s'y conforme.

Je regarde ce qui se passe si le modèle invente un sujet, disons `"visa"` : `OFFICIAL.get(topic, OFFICIAL["entry"])` retombe sur la liste « entrée ». Pas d'exception, pas de plantage. Et quand rien n'est trouvé, l'outil renvoie une **phrase d'ordre** au modèle : dis-le, ne devine pas. Un outil peut guider le modèle par ce qu'il renvoie, pas seulement par ce qu'il fait.

<!-- code: mytravel/app/tools.py 58-64 -->
```python
@tool
def read_official_page(url: str) -> str:
    """Read an official page found by search_official."""
    try:
        return f"{url}\n{read_page(url, ALL_OFFICIAL)}"
    except (ValueError, httpx.HTTPError) as error:
        return f"Could not read {url}: {error}"
```

Le second outil lit une page. Il renvoie l'adresse en première ligne : c'est elle que le modèle citera. Et les erreurs deviennent du texte, comme au chapitre 1. En vrai, ça arrive souvent : le site de l'ambassade du Japon répond 403 aux robots. L'agent lit alors « Could not read… » et se rabat sur une autre page.

### `app/sources.py` : la politique, en clair

<!-- code: mytravel/app/sources.py 10-28 -->
```python
# Government sites of the main destinations: a visa rule is
# written by the country that issues the visa.
GOVERNMENTS = ["gouv.fr", "gov", "gov.uk", "europa.eu", "go.jp",
               "go.th", "go.kr", "gov.au", "govt.nz", "gc.ca",
               "admin.ch", "belgium.be", "gob.mx", "gov.br",
               "gov.in", "gov.sg", "gov.ma", "gouv.qc.ca"]

OFFICIAL = {
    # Visa, passport, entry rules.
    "entry": ["diplomatie.gouv.fr", "france-visas.gouv.fr",
              "service-public.fr", *GOVERNMENTS],
    # Vaccines, health risks, insurance abroad.
    "health": ["pasteur.fr", "who.int", "ameli.fr",
               "santepubliquefrance.fr", *GOVERNMENTS],
    # What goes in the suitcase (aviation security), what customs
    # allow, what an airline accepts.
    "baggage": ["ecologie.gouv.fr", "douane.gouv.fr",
                "airfrance.fr", "easa.europa.eu", *GOVERNMENTS],
}
```

Tu vas me dire : « C'est une donnée en dur, ça ! » Bonne remarque, et j'y ai réfléchi. Une donnée en dur, c'est un fait qui vieillit : un prix, une règle de visa. Ici, ce sont des **noms de sites**, et diplomatie.gouv.fr ne change pas d'adresse tous les mois. C'est une politique de confiance, comme la liste des personnes qui ont la clé de ta maison. Les règles elles-mêmes sont lues en direct.

Un détail : `"gov"` couvre `travel.state.gov`, et `"go.jp"` couvre `www.mofa.go.jp`. Un domaine couvre ses sous-domaines. On va voir comment.

### `app/web.py` : trois fonctions, une règle

Je lis les noms des fonctions d'abord : `is_allowed`, `search_engine`, `search_web`, `read_page`. Le reste est un analyseur HTML.

<!-- code: mytravel/app/web.py 27-35 -->
```python
def is_allowed(url, domains):
    """https, and the host is one of the domains or a subdomain."""
    try:
        parts = urlparse(url)
        host = parts.hostname or ""
    except ValueError:  # a broken URL is never trusted
        return False
    return parts.scheme == "https" and any(
        host == d or host.endswith("." + d) for d in domains)
```

Six lignes, et c'est la plus importante du chapitre. Je teste mentalement les cas tordus, c'est ce que ferait un attaquant :

- `https://www.diplomatie.gouv.fr/...` : l'hôte finit par `.diplomatie.gouv.fr`, accepté ;
- `https://diplomatie.gouv.fr.evil.com/...` : l'hôte finit par `.evil.com`, refusé. C'est pour ça qu'on compare la **fin** du nom d'hôte, et pas `"diplomatie.gouv.fr" in url` ;
- `http://www.diplomatie.gouv.fr/` : pas de https, refusé ;
- `https://www.bing.com/aclick?...` : une publicité, refusée.

Et une adresse cassée, que Python ne sait même pas découper (`https://[x`), lève une erreur dans `urlparse` : le `try` la transforme en refus. Un contrôle de sécurité qui plante est un contrôle qui ne contrôle plus ; celui-ci échoue **fermé**. Les tests du chapitre vérifient exactement ces cas. Je te conseille de les lire : `tests/test_ch09_web.py` est la meilleure documentation de `is_allowed`.

<!-- code: mytravel/app/web.py 59-67 -->
```python
def search_web(query, domains, max_results=5):
    """Results from the allowed sites only. Never raises."""
    try:
        found = search_engine(query, domains)
    except Exception:  # engine down, quota, no network
        return []
    # Ads and random blogs are filtered here, whatever the engine.
    return [r for r in found
            if is_allowed(r["url"], domains)][:max_results]
```

Voilà la réponse à la question de tout à l'heure : la publicité est jetée dans la compréhension de liste, à la fin de la fonction. Et `except Exception` n'est pas une paresse : c'est un choix. Une recherche ratée ne doit jamais faire tomber la conversation. On renvoie une liste vide, et l'outil dira « aucune source ». C'est le seul `except Exception` de ce fichier, et le commentaire dit pourquoi.

`search_engine`, plus haut dans le fichier, cache la différence entre Tavily et DuckDuckGo. Avec DuckDuckGo, il essaie d'abord la requête avec `site:diplomatie.gouv.fr OR site:...` pour viser les bons sites, puis sans, si rien ne sort. Je l'ai découvert en testant : selon le moteur que `ddgs` choisit au hasard, l'opérateur `site:` marche ou ne marche pas.

<!-- code: mytravel/app/web.py 90-99 -->
```python
def read_page(url, domains):
    """The text of an allowed page."""
    if not is_allowed(url, domains):
        raise ValueError(f"not a trusted site: {url}")
    response = httpx.get(url, timeout=20, follow_redirects=True,
                         headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    parser = PageText()
    parser.feed(response.text)
    return " ".join(parser.parts)[:MAX_CHARS]
```

On vérifie l'adresse **avant** de la télécharger : le modèle ne peut pas faire lire à myTravel une page hors liste, même s'il la réclame. `PageText` garde le texte visible et saute `script`, `style`, `nav`, `footer` : le menu d'un site ministériel fait parfois plus de texte que l'article. Enfin, on coupe à `MAX_CHARS` (8 000 caractères) : une page officielle complète peut dépasser la fenêtre de contexte d'un modèle gratuit.

> ⚠️ **Piège classique** — `follow_redirects=True` suit les redirections sans revérifier l'adresse d'arrivée. Une page autorisée pourrait rediriger ailleurs. Pour ce chapitre, c'est acceptable : on ne lit que des sites gouvernementaux. Le chapitre 15 ferme cette porte en vérifiant chaque saut.

En haut du fichier, une ligne intrigue toujours : `truststore.inject_into_ssl()`. Sur beaucoup de PC d'entreprise, un antivirus ou un proxy inspecte le trafic https avec son propre certificat. Python, par défaut, ne le connaît pas et refuse toutes les connexions. `truststore` lui fait utiliser les certificats du système, comme ton navigateur.

### `app/assistant.py` : deux lignes changent

Le prompt gagne trois phrases : utilise tes outils, ne réponds jamais de mémoire, chaque fait avec l'URL où tu l'as lu. `create_agent` reçoit la liste `TOOLS` au lieu d'une liste vide, et un **middleware** : une fonction qui entoure chaque appel d'outil. C'est `tool_errors`, en haut de `app/tools.py` :

<!-- code: mytravel/app/tools.py 26-39 -->
```python
@wrap_tool_call
def tool_errors(request, handler):
    """Around every tool call: a failure becomes a message.

    A bad date, a site down, a city not found: the model reads
    what went wrong and tries again, instead of the whole answer
    crashing. It is the chapter 1 rule: an error is a text.
    """
    try:
        return handler(request)
    except Exception as error:
        return ToolMessage(f"Tool error: {error}. Fix the call, "
                           "or say you could not find it.",
                           tool_call_id=request.tool_call["id"])
```

Sans elle, une date mal écrite par le modèle (« mars » au lieu de `2027-03-10`) ferait planter `date.fromisoformat`, et toute la réponse avec. Avec elle, l'exception devient un message d'outil : le modèle lit « Tool error : … », corrige son appel ou dit qu'il n'a pas trouvé. On retrouve la règle du chapitre 1 (une erreur est un texte), appliquée une fois pour tous les outils. La mémoire du chapitre 8 continue de marcher : demande « et pour la Corée ? » après la question sur le Japon, l'agent comprend.

### Les outils, en direct dans la page

Chercher et lire une page prend du temps : parfois dix secondes avant le premier mot. C'est le moment de servir l'événement `step` réservé au chapitre 7. Je regarde la boucle de `stream_mytravel` :

<!-- code: mytravel/app/assistant.py 38-50 -->
```python
    for token, _ in agent.stream(
            {"messages": [("user", message)]}, config,
            stream_mode="messages"):
        if token.type == "tool":  # its result: not for the page
            continue
        # The model calls a tool: say it now, it may take a while.
        for call in getattr(token, "tool_call_chunks", []):
            if call["name"]:
                yield {"type": "step", "text": call["name"]}
        if token.content:
            yield {"type": "token", "text": token.content}
    answer = agent.get_state(config).values["messages"][-1]
    yield {"type": "done", "answer": answer.content}
```

En mode `"messages"`, LangGraph fait passer trois sortes de messages : les tokens du modèle, ses appels d'outils, et les résultats des outils. Le résultat (`token.type == "tool"`) est une page entière, pas pour le voyageur : on le saute. L'appel, lui, arrive en morceaux (`tool_call_chunks`) : le premier morceau porte le nom de l'outil, les suivants ses arguments. Dès que le nom arrive, un `step` part, et la page affiche une pastille `search_official` dans la bulle d'attente. Le voyageur voit que ça travaille, et sur quoi.

Une dernière chose : le modèle écrit parfois une phrase avant d'appeler un outil (« Je vais vérifier sur le site officiel »). Elle s'affiche en brouillon, puis `done` la remplace par la réponse finale. C'est pour ça que la page garde un brouillon et ne colle jamais les tokens à la réponse définitive.

## QCM

**1.** Pourquoi ne pas recopier les règles de visa dans un fichier du projet ?

- **a)** Parce qu'elles changent, et qu'un fichier vieillit
- **b)** Parce que le modèle ne sait pas lire un fichier
- **c)** Parce qu'il faudrait le tenir à jour pour des centaines de pays
- **d)** Parce que Python ne sait pas ouvrir de JSON

**2.** `is_allowed("https://diplomatie.gouv.fr.evil.com/x", ["diplomatie.gouv.fr"])` renvoie :

- **a)** `True`, le texte contient `diplomatie.gouv.fr`
- **b)** `False`, l'hôte ne finit pas par `.diplomatie.gouv.fr`
- **c)** `True`, c'est en https
- **d)** une exception

**3.** Où une publicité renvoyée par le moteur est-elle écartée ?

- **a)** Dans le prompt de l'agent
- **b)** Dans `search_web`, par le filtre `is_allowed`
- **c)** Dans la page web
- **d)** Par le code, quel que soit le moteur

**4.** Le moteur de recherche est en panne. Que se passe-t-il ?

- **a)** Le serveur renvoie une erreur 500
- **b)** `search_web` renvoie une liste vide
- **c)** L'outil répond « No official source found. Say so; do not guess. »
- **d)** L'agent invente une règle plausible

**5.** Que lit le modèle pour savoir comment appeler `search_official` ?

- **a)** Le code de la fonction
- **b)** Sa docstring
- **c)** Ses paramètres et leurs types
- **d)** Le fichier `sources.py`

**6.** Pourquoi `read_page` vérifie-t-elle l'adresse avant de télécharger ?

- **a)** Pour aller plus vite
- **b)** Pour que le modèle ne puisse pas faire lire une page hors liste
- **c)** Parce que httpx l'exige
- **d)** Pour éviter de télécharger une page inutile

**Réponses.** Q1 : a, c · Q2 : b · Q3 : b, d · Q4 : b, c · Q5 : b, c · Q6 : b, d

## Ce qu'il faut retenir

1. Un modèle répond avec le monde de ses données d'entraînement. Pour une règle qui change, on lit la page officielle le jour de la question.
2. Le modèle choisit quoi chercher ; le code décide où. La liste des sites de confiance est vérifiée sur chaque résultat et avant chaque lecture.
3. On compare la fin du nom d'hôte, jamais une sous-chaîne de l'URL.
4. Une recherche ratée renvoie une liste vide, et l'outil dit au modèle de ne pas deviner.
5. Avec `@tool`, la docstring devient le mode d'emploi de l'outil pour le modèle.

**Au chapitre suivant :** myTravel sait s'il te faut un visa. Il est temps qu'il te trouve où dormir. Même méthode, d'autres sites de confiance, et une nouveauté : un lien de recherche Booking déjà rempli avec tes dates.

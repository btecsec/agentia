# Chapitre 13 — Le graphe myTravel : des agents qui travaillent ensemble

> **Dossier GitHub associé :** `chapitre-13-graphe/`

**À la fin de ce chapitre, tu sauras :**

- découper un agent surchargé en un agent Mission, des spécialistes et un agent Synthèse ;
- obtenir du modèle une sortie structurée (un objet Pydantic) plutôt que du texte ;
- lancer plusieurs agents en même temps avec `Send`, et réunir leurs rapports ;
- montrer chaque agent au moment où il démarre, puis la synthèse mot à mot, avec `graph.stream` ;
- lire et dessiner l'architecture complète de myTravel ;
- justifier le choix de LangGraph pour ce projet.

## La caisse à outils

Au chapitre 12, tu as donné dix outils à un seul agent, et tu l'as vu hésiter. Ce n'est pas une question d'intelligence. Demande à quelqu'un de très compétent de vérifier un visa, chercher un hôtel, comparer des vols, lire la météo et le bulletin de sécurité, en même temps, en gardant tout en tête : il oubliera quelque chose. Personne ne travaille comme ça.

Une agence de voyage, si. Quelqu'un à l'accueil écoute le client et note sa demande. Il la passe à ceux qui savent : la personne des visas, celle des hôtels, celle des billets. Chacun fait sa partie, en même temps que les autres. Puis quelqu'un remet tout en forme, vérifie le total, et rend le dossier.

C'est exactement le graphe de ce chapitre : un agent **Mission** à l'accueil, cinq **spécialistes**, un agent **Synthèse**. Les mêmes dix outils qu'au chapitre 12, mais personne n'en porte plus de trois.

## Le découpage

Trois idées font tout le chapitre.

**Mission ne répond pas : il comprend.** Il lit la conversation et remplit une fiche structurée, la classe `Trip` : destination, pays, dates, ville de départ, nationalité, voyageurs, budget, et la liste des agents utiles. Ce que tu as dit de toi trois messages plus tôt (« je suis belge ») atterrit dans la fiche : Mission relit toute la conversation. Pour obtenir un objet plutôt qu'un texte, on utilise la **sortie structurée** : on donne au modèle le schéma de la classe Pydantic, il renvoie des valeurs qui le respectent, et LangChain les transforme en objet Python. Si l'essentiel manque (« je veux partir », sans destination ; « entre le 22 janvier et le 8 mars », sans dire combien de temps), Mission remplit le champ `question` au lieu des agents, et le graphe renvoie la question au voyageur.

**Les spécialistes travaillent en même temps.** La fiche du chapitre 6 le disait : aucun spécialiste n'attend un autre. LangGraph le permet avec `Send`, vu au chapitre 3 : une instruction « lance ce nœud avec cette entrée », envoyée une fois par agent choisi. Les cinq tournent en parallèle, et le nœud suivant attend qu'ils aient tous fini. Le temps d'un plan complet devient celui du plus lent, pas la somme des cinq.

**Synthèse n'a pas d'outil.** Il lit les rapports et la conversation, et écrit la réponse. Sans outil, il ne peut rien aller chercher de nouveau : il ne peut assembler que ce que les spécialistes ont trouvé, avec leurs sources.

Pourquoi **LangGraph** ? Ce découpage est un graphe : des étapes, des flèches, un embranchement après Mission, une étape qui attend plusieurs autres. LangGraph dessine exactement ça, garde l'état entre les étapes, et fournit déjà le checkpointer du chapitre 8. Au chapitre 14, il nous donnera aussi de quoi **mettre le graphe en pause** pour attendre ton accord. CrewAI, que tu as vu au chapitre 4, pense en rôles et en tâches plutôt qu'en étapes : parfait pour un prototype ou un traitement par lots, moins pour une application web qui doit montrer chaque étape en direct, se mettre en pause et reprendre.

> 💡 **À retenir** — Un agent par mission courte, deux ou trois outils chacun. Un agent qui comprend et répartit, un agent qui assemble. Le graphe rend ce découpage visible et testable.

## L'architecture complète

Voici myTravel en entier, tel qu'il est à la fin du livre. Les pièces ajoutées aux chapitres 14 à 20 sont marquées.

![L'architecture complète de myTravel : navigateur, API et graphe des agents](chapitre-13-graphe/images/architecture-mytravel.png){width=14cm}

Et en dessous de chaque agent :

```text
AGENTS  app/agents.py   un prompt + des outils, modèle rapide (19)
  admin     search_official, read_official_page
  hotel     hotel_offers, hotel_links, exchange_rate
  transport flight_offers, flight_links, car_links
  weather   weather
  risk      travel_advice, search_official
OUTILS  app/tools.py ──► app/web.py ──► Tavily | DuckDuckGo
                     │   (sites de app/sources.py, cache (19))
                     ├─► Open-Meteo (géocodage, prévision, archive)
                     └─► Frankfurter (taux BCE)
        app/hotels.py ──► Xotelo (prix du jour, par vendeur)
        app/flights.py ─► Travelpayouts (offres de vol réelles)
DONNÉES app/memory.py  mytravel.db : checkpoints, cache
```

Lis le premier schéma en suivant une question complète. `mission` produit une `Trip`. Selon ce qu'elle contient, le graphe prend une de trois routes : poser une question (`ask_back`), préparer une réservation (`confirm`, chapitre 14), ou lancer les agents. Chaque `agent` est le même nœud, lancé cinq fois avec un nom différent. Quand tous ont rendu leur rapport, `synthesis` écrit la réponse.

![Le graphe myTravel complet : flèches simples en trait plein, flèches conditionnelles en pointillé](chapitre-13-graphe/images/graphe-mytravel.png){width=14cm}

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

```text
chapitre-13-graphe/mytravel/
├── server.py          ← importe stream_mytravel depuis app.graph
└── app/
    ├── graph.py       ← NOUVEAU : Trip, état, nœuds, graphe
    ├── agents.py      ← NOUVEAU : les 5 spécialistes
    ├── tools.py       ← inchangé : les 10 outils
    └── (assistant.py a disparu)
```

| Fichier | Rôle |
|---|---|
| `app/graph.py` | la fiche `Trip`, l'état du graphe, les quatre nœuds, le flux `stream_mytravel` |
| `app/agents.py` | pour chaque spécialiste : un nom affiché, des outils, une consigne ; `run_agent` |
| `server.py` | une seule ligne change : `from app.graph import stream_mytravel` |

### Lancer le chapitre

```bash
cd chapitre-13-graphe/mytravel
uvicorn server:app --reload
pytest                    # 38 passed
```

Rejoue la question qui posait problème : « Plan complet pour Rome, 4 jours en mai, 800 €, départ de Lyon, passeport français. » Dans la bulle d'attente, cinq pastilles apparaissent presque ensemble : les agents partent à la fois. Puis la synthèse s'écrit mot à mot. La réponse arrive en sections (vols, hôtel, formalités, météo, sécurité), chacune avec ses sources. Puis « Visa pour le Japon ? » : un seul agent travaille, la réponse arrive vite. Et « Je veux partir » : myTravel te demande où.

### À toi d'abord

Ouvre `app/graph.py` et va tout en bas, à `build_graph`. Dessine le graphe sur une feuille. Puis remonte à `after_mission` et réponds : que renvoie cette fonction quand Mission n'a choisi aucun agent ?

## On lit le code ensemble

### `build_graph` d'abord, le sommaire du fichier

<!-- code: mytravel/app/graph.py 188-201 -->
```python
def build_graph():
    graph = StateGraph(State)
    graph.add_node("mission", mission)
    graph.add_node("agent", agent)
    graph.add_node("synthesis", synthesis)
    graph.add_node("ask_back", ask_back)
    graph.add_edge(START, "mission")
    graph.add_conditional_edges(
        "mission", after_mission,
        ["agent", "synthesis", "ask_back"])
    graph.add_edge("agent", "synthesis")  # waits for all agents
    graph.add_edge("synthesis", END)
    graph.add_edge("ask_back", END)
    return graph.compile(checkpointer=checkpointer())
```

Quatre nœuds, et une seule flèche qui hésite : `add_conditional_edges`. Après `mission`, c'est la fonction `after_mission` qui choisit la suite, parmi trois noms. La liste en troisième argument sert à LangGraph pour dessiner le graphe et vérifier qu'on ne va nulle part d'inattendu.

La ligne `graph.add_edge("agent", "synthesis")` porte un commentaire que j'ai pesé : *waits for all agents*. Quand cinq copies du nœud `agent` tournent en même temps, LangGraph attend qu'elles aient toutes fini avant de lancer `synthesis`, une seule fois. C'est le comportement par défaut, rien à écrire.

### `Trip` et l'état : ce qui circule

<!-- code: mytravel/app/graph.py 37-55 -->
```python
    agents: list[Literal["admin", "hotel", "transport", "weather",
                         "risk"]] = Field(
        default_factory=list,
        description="Agents needed for the last message")
    question: str = Field(
        "", description="Question to ask back if something "
                        "essential is missing, else empty")


def fresh(old, new):
    """Parallel agents add to the list; [] starts it over."""
    return old + new if new else []


class State(TypedDict):
    messages: Annotated[list, add_messages]  # the conversation
    trip: dict
    reports: Annotated[list, fresh]  # (agent, report) pairs
    answer: str
```

Dans `Trip`, le champ `agents` est une liste de `Literal` : le modèle ne peut choisir que parmi ces cinq noms. Un nom inventé (`"visa_agent"`) est refusé par Pydantic avant d'atteindre le graphe. Les `description` ne sont pas des commentaires : elles partent au modèle avec le schéma, et lui disent quoi mettre dans chaque champ.

L'état, `State`, est ce que les nœuds se passent. Deux champs ont un **réducteur**, la fonction écrite dans `Annotated`, qui dit comment fusionner une mise à jour avec la valeur existante. Pour `messages`, `add_messages` ajoute à la suite : c'est la conversation. Pour `reports`, j'ai écrit `fresh`, et je t'explique pourquoi, parce que c'est le bug que j'ai fait en premier.

Cinq agents renvoient chacun `{"reports": [(leur nom, leur rapport)]}`, en même temps. Sans réducteur, le dernier écraserait les quatre autres. Avec un simple ajout (`old + new`), ça marche… une fois. Au message suivant, le checkpointer recharge l'état, et les rapports de la question précédente sont encore là : Synthèse mélange Rome et Tokyo. D'où `fresh` : une liste vide **remet à zéro**, et `stream_mytravel` envoie `"reports": []` au début de chaque question.

### `mission` et `after_mission` : comprendre, puis aiguiller

<!-- code: mytravel/app/graph.py 111-127 -->
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
    return {"trip": trip.model_dump()}
```

<!-- code: mytravel/app/graph.py 141-151 -->
```python
def after_mission(state):
    """The road after Mission: a question back, or the agents."""
    trip = state["trip"]
    if trip["question"]:
        return "ask_back"
    request = state["messages"][-1].content
    # Send = "run this node with this input": one per agent, and
    # LangGraph runs them at the same time.
    return [Send("agent", {"name": name, "trip": trip,
                           "request": request})
            for name in trip["agents"]] or "synthesis"
```

`with_structured_output(Trip, method="function_calling")` mérite un mot. Il existe plusieurs façons d'obtenir une sortie structurée ; `function_calling` passe par l'appel d'outil, que tous nos modèles savent faire (c'était la condition du choix du modèle gratuit). Le modèle « appelle » un faux outil nommé `Trip`, et ses arguments deviennent l'objet.

Et si le modèle n'y arrive pas ? Un modèle gratuit rend parfois une réponse vide, ou des phrases au lieu de la fiche : `invoke` renvoie alors `None`, ou une fiche invalide qui lève une `ValueError`. Souvent, c'est un raté passager : le même message, renvoyé tout de suite, passe. D'où la boucle `for` : deux essais. Si les deux échouent, Mission répond `UNREAD` au voyageur : ce qu'une demande doit contenir (destination, dates ou durée, ville de départ, voyageurs), plutôt qu'un vague « reformule » ou un serveur à terre. Le test `test_unreadable_mission_asks_back` le vérifie.

Dernière ligne avant le `return` : `not_past`. En novembre, demande « du 22 janvier au 8 mars » : le modèle écrit souvent le janvier qui vient de passer, malgré la date du jour dans le prompt. `not_past` repousse d'un an toute date déjà passée. Même règle que pour les nuits, un peu plus bas : ce que Python sait vérifier, Python le vérifie.

Mission reçoit **toute la conversation** (`*state["messages"]`). C'est ce qui lui permet de comprendre « et en juin ? » après une question sur Rome : il remplit `destination="Rome"` tout seul.

Dans `after_mission`, je lis la dernière ligne deux fois, parce qu'elle répond à ta question. Une compréhension de liste fabrique un `Send` par agent choisi. Si Mission n'en a choisi aucun (« merci ! »), la liste est vide, donc fausse, et le `or` renvoie `"synthesis"` : Synthèse répond seul, poliment.

Chaque `Send` porte **sa propre entrée** : le nom de l'agent, la fiche (nationalité comprise), la question. Le nœud `agent` ne reçoit donc pas tout l'état, seulement sa mission.

### `app/agents.py` : un spécialiste, c'est trois lignes de config

<!-- code: mytravel/app/agents.py 22-30 -->
```python
AGENTS = {
    "admin": {
        "label": "Administration",
        "tools": [tools.search_official, tools.read_official_page],
        "prompt": "Visa, passport validity, entry rules, health, "
                  "baggage and customs, for the traveler's "
                  "nationality. Read the official page before "
                  "citing it.",
    },
```

Un dictionnaire, pas une classe par agent. Ajouter un spécialiste, c'est ajouter une entrée ici et un nom dans le `Literal` de `Trip`. Le prompt commun (`COMMON`, en haut du fichier) donne les règles que tous partagent : outils obligatoires, une URL par fait, rien n'est inventé, rapport court en français.

<!-- code: mytravel/app/agents.py 66-76 -->
```python
def run_agent(name, trip, request):
    """One agent, one task: returns its report."""
    spec = AGENTS[name]
    agent = create_agent(
        get_chat_model(), spec["tools"],
        system_prompt=COMMON.format(label=spec["label"])
        + spec["prompt"],
        middleware=[tools.tool_errors])
    task = f"Traveler's message: {request}\nTrip: {trip}"
    result = agent.invoke({"messages": [("user", task)]})
    return f"## {spec['label']}\n{result['messages'][-1].content}"
```

Tu reconnais l'agent des chapitres 9 à 12 : `create_agent`, un modèle, des outils. Deux différences. Il n'a **pas de checkpointer** : un spécialiste n'a pas besoin de mémoire, il reçoit tout ce qu'il faut dans sa tâche. Et son rapport commence par un titre (`## Administration`) : Synthèse sait ainsi d'où vient chaque morceau.

Un graphe qui contient des agents, qui sont eux-mêmes de petits graphes : c'est le schéma le plus courant des systèmes multi-agents, et il n'a rien de magique.

> ⚠️ **Piège classique** — Donner la mémoire de la conversation à chaque spécialiste. Cinq agents relisent alors toute la discussion à chaque appel : cinq fois plus de tokens, et des rapports qui répondent aux anciennes questions. Mission résume la conversation dans la fiche `Trip` ; les spécialistes lisent la fiche.

### `synthesis` : assembler sans inventer

<!-- code: mytravel/app/graph.py 160-171 -->
```python
def synthesis(state):
    get_stream_writer()("Synthèse")
    ranked = sorted(state["reports"],
                    key=lambda pair: ORDER.index(pair[0]))
    reports = "\n\n".join(report for _, report in ranked)
    prompt = SYNTHESIS.format(trip=state["trip"],
                              nights=nights(state["trip"]),
                              reports=reports or "No report.")
    answer = get_chat_model().invoke(
        [SystemMessage(prompt), *state["messages"]])
    # The model's own message: already streamed, not sent twice.
    return {"answer": answer.content, "messages": [answer]}
```

Les cinq agents finissent dans l'ordre qu'ils veulent : la météo répond en une seconde, l'hôtel en dix. Si Synthèse lisait les rapports dans l'ordre d'arrivée, ta réponse commencerait un jour par la météo, le lendemain par les formalités. Le voyageur, lui, cherche d'abord combien coûte le vol et où il dort. Chaque rapport arrive donc avec le nom de son agent, et `sorted` les range selon `ORDER` (défini sous le prompt) : vols, hôtel, puis le reste. Le prompt demande de garder cet ordre dans les sections. Le tri, lui, ne dépend pas de la bonne volonté du modèle.

Le prompt `SYNTHESIS` dit : réponds à partir des rapports « et de rien d'autre », garde chaque URL à côté du fait qu'elle prouve, vérifie le total par rapport au budget, termine par une liste de sources. C'est une consigne, pas une garantie : un modèle peut encore glisser un lien de sa mémoire. Le chapitre 14 ajoute le contrôle qui ne dépend pas de sa bonne volonté.

Une ligne du prompt mérite un détour : « The stay lasts {nights} nights ». Le nombre de nuits n'est pas demandé au modèle, il lui est donné :

<!-- code: mytravel/app/graph.py 174-180 -->
```python
def nights(trip):
    """Counted here: a model that counts days writes 47 for 16."""
    try:
        return (date.fromisoformat(trip["end"])
                - date.fromisoformat(trip["start"])).days
    except ValueError:  # no dates: a visa question, say
        return "an unknown number of"
```

Pourquoi ce zèle ? Parce qu'un modèle compte mal. Pour un séjour du 22 novembre au 8 décembre, j'ai vu Synthèse écrire « 47 jours », en déduire qu'il fallait un visa, puis recopier son erreur au message suivant. Les rapports, eux, disaient tous 16. Règle simple : tout ce que Python sait calculer (une durée, un total, une conversion), Python le calcule, et le modèle le recopie.

### `stream_mytravel` : le graphe en direct

Un plan complet prend une minute. Sans rien à l'écran, c'est long. Avec le graphe, on peut montrer mieux que des outils : les **agents**, au moment où ils démarrent. Chaque nœud l'annonce lui-même, en première ligne : `get_stream_writer()("Mission")`, `get_stream_writer()(AGENTS[...]["label"])`, `get_stream_writer()("Synthèse")`. Le *stream writer* est un canal que LangGraph ouvre pour chaque nœud : ce qu'on y écrit ressort tout de suite du flux, en mode `"custom"`.

<!-- code: mytravel/app/graph.py 207-223 -->
```python
def stream_mytravel(message, conversation):
    """One message in; events out, as they happen. "custom"
    carries what the nodes say with get_stream_writer,
    "messages" the model's tokens."""
    config = {"configurable": {"thread_id": conversation}}
    start = {"messages": [HumanMessage(message)], "reports": [],
             "answer": ""}
    for mode, chunk in graph.stream(start, config,
                                    stream_mode=["custom",
                                                 "messages"]):
        if mode == "custom":
            yield {"type": "step", "text": chunk}
        elif (chunk[1]["langgraph_node"] == "synthesis"
              and chunk[0].content):  # not the specialists' drafts
            yield {"type": "token", "text": chunk[0].content}
    state = graph.get_state(config).values
    yield {"type": "done", "answer": state["answer"]}
```

On demande deux modes à la fois : `"custom"` pour ce que les nœuds annoncent, `"messages"` pour les tokens des modèles. Le flux rend alors des paires `(mode, morceau)`. Je m'arrête sur le filtre, parce qu'il m'a eu. Le mode `"messages"` rend les tokens de **tous** les modèles du graphe : Mission qui remplit sa fiche, les cinq spécialistes qui écrivent leurs rapports en même temps, et Synthèse. Sans filtre, la page affichait cinq brouillons mélangés, mot à mot, avant la réponse. Les métadonnées de chaque token disent quel nœud l'a produit (`langgraph_node`) : on ne garde que `synthesis`.

Un dernier détail, dans `synthesis` : le nœud ajoute à la conversation le message du modèle lui-même (`"messages": [answer]`), pas un `AIMessage(answer)` tout neuf. En mode `"messages"`, LangGraph rend aussi les messages qu'un nœud ajoute à l'état, sauf ceux qu'il a déjà diffusés, reconnus à leur identifiant. Un message neuf a un nouvel identifiant : la réponse arrivait deux fois. Le test `test_steps_come_first_then_the_answer_word_by_word` vérifie l'ordre : les étapes, puis les mots, une seule fois.

> 💡 **Et ailleurs ?** — D'autres outils savent orchestrer des agents. L'**OpenAI Agents SDK** propose des « handoffs » (un agent passe la main à un autre) ; le **Claude Agent SDK** donne à un agent un terminal et des fichiers, idéal pour du code ; **MCP**, vu au chapitre 12, sert à partager des outils entre programmes, pas à orchestrer des agents. Pour myTravel, LangGraph l'emporte sur un point précis : le chemin est un graphe qu'on lit, qu'on teste nœud par nœud, qu'on met en pause et qu'on reprend.

## QCM

**1.** Que produit l'agent Mission ?

- **a)** La réponse finale au voyageur
- **b)** Un objet `Trip` : la demande structurée et les agents utiles
- **c)** Une question en retour, si l'essentiel manque
- **d)** Les liens de réservation

**2.** Que fait `Send("agent", {...})` ?

- **a)** Envoie un e-mail au voyageur
- **b)** Lance le nœud `agent` avec cette entrée précise
- **c)** Permet, renvoyé plusieurs fois, de lancer plusieurs agents en même temps
- **d)** Enregistre la conversation

**3.** Sans le réducteur `fresh`, que se passerait-il avec un simple ajout `old + new` ?

- **a)** Les rapports de la question précédente resteraient dans l'état
- **b)** Synthèse mélangerait deux voyages
- **c)** Les agents ne pourraient plus tourner en parallèle
- **d)** Rien

**4.** Mission n'a choisi aucun agent. Où va le graphe ?

- **a)** Nulle part, il plante
- **b)** Vers `synthesis`, grâce au `or` de `after_mission`
- **c)** Vers `ask_back`
- **d)** Vers les cinq agents

**5.** Pourquoi les spécialistes n'ont-ils pas de checkpointer ?

- **a)** Ils reçoivent tout ce qu'il faut dans leur tâche
- **b)** Leur donner la conversation multiplierait les tokens par cinq
- **c)** LangGraph l'interdit
- **d)** La fiche `Trip` résume déjà la conversation pour eux

**6.** Pourquoi le champ `agents` de `Trip` est-il une liste de `Literal` ?

- **a)** Pour que le modèle ne puisse choisir que des agents qui existent
- **b)** Pour aller plus vite
- **c)** Pour que Pydantic refuse un nom inventé
- **d)** Parce que LangGraph l'exige

**7.** Dans `stream_mytravel`, pourquoi ne garder que les tokens du nœud `synthesis` ?

- **a)** Parce que les spécialistes écrivent leurs rapports en même temps, et la page les mélangerait
- **b)** Parce que les autres nœuds n'ont pas de modèle
- **c)** Parce que seule la synthèse s'adresse au voyageur
- **d)** Pour économiser des tokens

**Réponses.** Q1 : b, c · Q2 : b, c · Q3 : a, b · Q4 : b · Q5 : a, b, d · Q6 : a, c · Q7 : a, c

## Ce qu'il faut retenir

1. Un agent surchargé se découpe : Mission comprend et répartit, des spécialistes à deux ou trois outils travaillent, Synthèse assemble.
2. La sortie structurée transforme la compréhension de Mission en objet Pydantic, dont les champs et les valeurs possibles sont contrôlés.
3. `Send` lance plusieurs agents en parallèle ; le nœud suivant attend qu'ils aient tous fini.
4. Un réducteur dit comment fusionner l'état ; une liste partagée par des agents parallèles doit aussi savoir repartir de zéro.
5. `graph.stream` en modes `"custom"` et `"messages"` montre chaque agent qui démarre, puis la seule synthèse, mot à mot.
6. LangGraph rend le chemin visible, testable nœud par nœud, et sait faire une pause : c'est ce qui en fait le bon choix pour myTravel en production.

**Au chapitre suivant :** myTravel répond bien, mais il fait confiance à tout le monde : à toi, qui pourrais lui coller ton numéro de carte, et au modèle, qui pourrait glisser un lien douteux. On pose les garde-fous, et on lui apprend à attendre ton « oui » avant de préparer une réservation.

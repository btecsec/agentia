# Chapitre 3 — LangGraph : dessiner le chemin de ton agent

> **Dossier GitHub associé :** `chapitre-03-langgraph/`

**À la fin de ce chapitre, tu sauras :**

- expliquer ce qu'est un graphe d'état (état, nœuds, arêtes) et pourquoi il remplace une suite de `if` ;
- construire un workflow « rédiger, critiquer, réécrire » avec une boucle et une sortie conditionnelle ;
- choisir la bonne flèche (simple, conditionnelle, parallèle, rendez-vous) et lancer plusieurs copies d'un nœud avec `Send` ;
- visualiser le graphe, et suivre son exécution nœud par nœud ;
- sauvegarder l'état sur disque, mettre le graphe en pause et le reprendre ;
- choisir entre LangChain seul et LangGraph.

## Le texte parfait qu'on a quand même réécrit

Inès veut un paragraphe sur la météo à Tokyo pour le carnet de voyage de ses amis. Le premier jet de l'agent est excellent. Mais ton pipeline a trois étapes fixes : écrire, critiquer, réécrire. Alors il critique un texte sans défaut, le critique cherche et trouve quand même *quelque chose*, parce qu'on le paie pour ça, et la réécriture abîme ce qui marchait.

Le cas inverse est pire. Le premier jet est mauvais, la réécriture à peine meilleure, et personne ne vérifie. Le pipeline s'arrête parce que sa troisième étape est la dernière, pas parce que le texte est bon.

Dans les deux cas, la **forme** du programme ne dépend pas du **contenu**. Trois étapes, quoi qu'il arrive, comme une chaîne de montage qui visserait la même vis sur tous les produits. Ce qu'il te faudrait : « réécris tant que ce n'est pas bon, mais pas plus de deux fois ». Une boucle, une décision, un garde-fou.

Tu peux l'écrire avec un `while` et des `if`. Ça marche, jusqu'au jour où s'ajoutent une validation humaine, puis une branche pour les erreurs, puis une reprise après plantage. LangGraph existe pour ce jour-là.

## Pourquoi LangGraph ?

**LangGraph** est une bibliothèque, de la même équipe que LangChain, qui te fait décrire ton agent comme un **graphe** : des étapes reliées par des flèches. Tu ne programmes plus « fais ceci, puis cela » ; tu dessines les chemins possibles, et le programme choisit le sien à l'exécution.

Pourquoi s'embêter à dessiner ? Parce que les **boucles** et les **décisions** s’écrivent directement, sans acrobaties. Parce que le chemin est **visible** : on peut en tirer un dessin et suivre l'exécution pas à pas. Parce que l'état est **sauvegardé** à chaque étape, donc une panne à 3 heures du matin ne coûte pas tout le travail. Et parce qu'on peut **mettre le graphe en pause** pour qu'un humain valide avant de continuer.

Tu as déjà utilisé LangGraph sans le savoir. Au chapitre 2, `create_agent` construit un graphe de deux nœuds (« modèle », « outils ») avec une flèche qui revient. Ici, on dessine nous-mêmes un graphe, avec les nôtres.

Ce que LangGraph ne fait pas : il ne conçoit pas ton flux à ta place. Choisir ce qu'il y a dans l'état, découper en nœuds, décider des sorties, tout cela reste ton travail, et un mauvais découpage donne un mauvais graphe. Il demande aussi un peu plus de code qu'un agent LangChain pour un cas simple. L'investissement se paie quand le flux se complique.

> 💡 **À retenir** — LangChain assemble un agent prêt à l'emploi. LangGraph te laisse tracer le chemin. Dès que ton flux a une boucle, une branche ou une pause, c'est lui qu'il te faut.

## Les trois ingrédients d'un graphe

![Un agent piloté par l'état : nœuds, outils, décisions et état partagé](chapitre-03-langgraph/images/graph-ingredients.jpeg){width=13.1cm}

Un graphe LangGraph se compose de trois choses.

L'**état** (*state*) est le sac que tout le monde se passe. C'est un simple dictionnaire typé. Chaque étape y lit ce dont elle a besoin et y écrit son résultat.

Les **nœuds** (*nodes*) sont des fonctions Python. Un nœud reçoit l'état, fait son travail, et renvoie **seulement ce qu'il change**. Il n'a pas à renvoyer tout l'état.

Les **arêtes** (*edges*) sont les flèches : « après `write`, va dans `critique` ». Une arête **conditionnelle** choisit sa destination en regardant l'état : « si le texte est approuvé, fin ; sinon, retour à la réécriture ».

Voici le haut de `graph.py`, avec l'état de notre atelier :

<!-- code: graph.py 1-29 -->
```python
"""A write -> critique -> rewrite workflow as a LangGraph graph.

Chapter 2 gave a straight line: model, tools, model. Here the path
has a loop and a decision. A graph has three ingredients:

- a STATE: the bag every node passes around;
- NODES: Python functions that read the state and return what they
  want to change in it;
- EDGES: arrows saying which node runs after which. A CONDITIONAL
  edge picks its destination by looking at the state.

The graph:
  write -> critique -> approved? end : rewrite -> critique
"""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from modele import get_chat_model


class State(TypedDict):
    topic: str
    draft: str
    feedback: str
    revisions: int
    approved: bool
```

Cinq cases : le sujet, le brouillon courant, le conseil du critique, le nombre de réécritures déjà faites, et le verdict. Un `TypedDict` n'impose rien à l'exécution, mais il documente ce que contient le sac, et ton éditeur te prévient si tu te trompes de clé.

Une subtilité à connaître dès maintenant : que se passe-t-il quand un nœud écrit dans une case qui contient déjà quelque chose ? Par défaut, la nouvelle valeur **remplace** l'ancienne. C'est ce qu'on veut pour `draft`. Pour une liste de messages, on veut l'inverse : **ajouter** à la fin. On le déclare avec un *réducteur*, une petite fonction qui dit comment fusionner. Au chapitre 2, `create_agent` en utilisait un (`add_messages`) pour que l'historique grossisse au lieu d'être écrasé. Notre atelier n'en a pas besoin, car chaque case n'a qu'un auteur à la fois.

> ⚠️ **Piège classique** — Un nœud qui renvoie tout l'état au lieu de ses seuls changements. Ça marche sur un graphe linéaire, puis ça écrase le travail d'un autre nœud le jour où deux étapes tournent en parallèle. Renvoie le strict nécessaire.

### Les nœuds : trois fonctions, un modèle

Notre atelier est indépendant de myTravel : trois nœuds, qui parlent à un modèle. Ils sont définis à l'intérieur de `build_graph`, pour partager le même `model`. Le vrai modèle vient de `get_chat_model`, la fonction que `modele.py` a gagnée au chapitre 2 ; un test passe un faux modèle à la place :

<!-- code: modele.py 57-66 -->
```python
def get_chat_model():
    """The same OpenRouter model, seen through LangChain.

    LangChain's ChatOpenAI speaks the same dialect: it only needs
    the OpenRouter URL. Same key, same MODELE as chapter 1.
    """
    # Imported here: `python modele.py` must work without LangChain.
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=MODEL, base_url=BASE_URL, max_retries=6,
                      api_key=get_client().api_key)
```

Voici le premier nœud, `write`, et le deuxième, `critique` :

<!-- code: graph.py 56-79 -->
```python
def build_graph(model=None, max_revisions=2, checkpointer=None,
                review=False):
    """Assemble and compile the graph. Tests inject a `model`."""
    model = model or get_chat_model()

    def write(state: State):
        prompt = (
            "Write a paragraph of three sentences about: "
            f"{state['topic']}"
        )
        draft = model.invoke(prompt).content
        return {"draft": draft, "revisions": 0}

    def critique(state: State):
        prompt = (
            "You are a strict editor. Read this paragraph.\n"
            "Answer 'APPROVED' only if it contains at least one "
            "concrete figure (a number, a date or a percentage). "
            "Otherwise answer 'REVISE: ' followed by one sentence "
            f"of advice.\n\nParagraph:\n{state['draft']}"
        )
        verdict = model.invoke(prompt).content
        approved, feedback = parse_verdict(verdict)
        return {"approved": approved, "feedback": feedback}
```

Chaque nœud lit l'état (`state['topic']`, `state['draft']`) et renvoie un dictionnaire de changements. Le critique est volontairement pointilleux : il exige un chiffre. Sans ce critère un peu artificiel, un modèle poli approuve tout au premier coup et tu ne verrais jamais la boucle. Sa réponse passe par `parse_verdict`, plus haut dans le fichier :

<!-- code: graph.py 32-44 -->
```python
def parse_verdict(text):
    """Turn the critic's answer into (approved, feedback).

    We ask the model for 'APPROVED' or 'REVISE: <advice>'. Free text
    is easier for small models than JSON, and a plain parser is
    enough. Anything unclear counts as 'revise': safer than a false
    approval.
    """
    cleaned = text.strip()
    if cleaned.upper().startswith("APPROVED"):
        return True, ""
    feedback = cleaned.split(":", 1)[-1].strip()
    return False, feedback or "Improve clarity."
```

Toute réponse floue vaut « à réviser ». Mieux vaut une relecture de trop qu'une fausse approbation.


### Les arêtes : le routage

Les flèches simples s'écrivent en une ligne : `write` vers `critique`. La flèche intéressante part de `critique`. Elle appelle une fonction de routage :

<!-- code: graph.py 47-53 -->
```python
def route_after_critique(state, max_revisions=2):
    """The conditional edge: where do we go after the critic?"""
    if state["approved"]:
        return END
    if state["revisions"] >= max_revisions:
        return END  # the safety net, visible on the drawing
    return "rewrite"
```

C'est la fonction la plus importante du chapitre. Elle ne parle pas au modèle : elle lit l'état et renvoie le nom du prochain nœud, ou `END`. Trois cas, trois lignes. Le second `END` est le garde-fou : même si le critique ne se satisfait jamais, le graphe s'arrête après deux réécritures.

Reste le troisième nœud, `rewrite`, qui reçoit le brouillon et le conseil et incrémente `revisions`, puis l'assemblage :

<!-- code: graph.py 81-113 -->
```python
    def rewrite(state: State):
        prompt = (
            "Rewrite this paragraph, applying the advice.\n"
            f"Advice: {state['feedback']}\n\n"
            f"Paragraph:\n{state['draft']}"
        )
        return {
            "draft": model.invoke(prompt).content,
            "revisions": state["revisions"] + 1,
        }

    graph = StateGraph(State)
    graph.add_node("write", write)
    graph.add_node("critique", critique)
    graph.add_node("rewrite", rewrite)
    graph.add_edge(START, "write")
    graph.add_edge("write", "critique")
    graph.add_conditional_edges(
        "critique",
        lambda state: route_after_critique(state, max_revisions),
        ["rewrite", END],
    )
    graph.add_edge("rewrite", "critique")
    return graph.compile(
        checkpointer=checkpointer or InMemorySaver(),
        # Pause before each rewrite so a human can read the advice.
        interrupt_before=["rewrite"] if review else None,
    )


def drawing(graph):
    """The graph as Mermaid text, for any Mermaid viewer."""
    return graph.get_graph().draw_mermaid()
```

`compile()` vérifie que le graphe est cohérent (pas de nœud orphelin, pas de flèche vers un nœud inconnu) et renvoie l'objet qu'on lance. Le paramètre `review` servira plus bas, pour la pause. Et `drawing` renvoie le schéma du graphe.

## Pratique : qui fait quoi, et comment le lancer

Ici, le dossier ne contient plus d'agent à outils : un graphe « rédiger, critiquer, réécrire ». Repère les fichiers avant de lire le code des nœuds.

### Les fichiers et leur rôle

```text
chapitre-03-langgraph/
├── main.py    ← point d'entrée : lance le graphe, suit les nœuds
├── graph.py   ← l'état, les trois nœuds, le routage, build_graph
├── modele.py  ← la prise : client OpenRouter pour LangChain
└── tests/     ← modèle scripté, sans clé d'API
```

### Lancer le programme

Une seule installation, à la racine du dépôt, déjà faite si tu as suivi le chapitre 1 :

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
cp .env.example .env       # puis colle ta clé OpenRouter
```

Ensuite, dans le dossier du chapitre :

```bash
cd chapitre-03-langgraph
python modele.py   # 1. modèles gratuits capables d'outils
python main.py     # 2. le graphe, nœud par nœud
pytest             # 3. 14 tests, sans clé ni réseau
```

`main.py` crée un fichier `checkpoints.sqlite` : c'est l'état sauvegardé. Supprime-le pour repartir de zéro. La sortie typique est montrée plus bas, avec ses petits accidents de modèle gratuit.

### Les cinq détails à comprendre avant de lire le code

1. **Un nœud renvoie seulement ce qu'il change.** Pas tout l'état : LangGraph fusionne le résultat dans l'état commun.
2. **L'arête conditionnelle est une fonction ordinaire.** `route_after_critique` lit l'état et renvoie le nom de la suite.
3. **La limite de réécritures est le garde-fou.** Sans `max_revisions`, un critique jamais satisfait fait boucler le graphe.
4. **Le critique répond en texte libre.** `APPROVED` ou `REVISE: conseil`, lu par `parse_verdict`. Dans le doute, on réécrit.
5. **Le checkpointer sauvegarde chaque étape.** C'est lui qui permet de reprendre, et de mettre en pause avant `rewrite`.

## Voir le graphe, suivre l'exécution

Un graphe se dessine. `graph.get_graph().draw_mermaid()` renvoie du texte **Mermaid**, un langage de schémas que lisent GitHub, la plupart des éditeurs et le site mermaid.live :

![Le graphe du chapitre 3 : écrire, critiquer, réécrire jusqu'à l'approbation](chapitre-03-langgraph/images/graphe-critique.jpeg){width=9.1cm}

Une fois mis en forme, le texte Mermaid donne ce schéma, celui que tu tracerais sur un tableau blanc. La différence : il sort du code, donc il ne peut pas s'écarter du programme.

Pour suivre l'exécution, `main.py` remplace `invoke` par `stream` :

<!-- code: main.py -->
```python
"""Run chapter 3:  python main.py

Needs OPENROUTER_API_KEY in the .env file at the repository root.
The state is saved in checkpoints.sqlite: the file stays on disk
after the script ends, so a later run can read the state back.
"""

import sys

from langgraph.checkpoint.sqlite import SqliteSaver
from openai import RateLimitError

from graph import build_graph, drawing

TOPIC = "why a travel assistant should check the weather"
DB_FILE = "checkpoints.sqlite"


def main():
    # The drawing needs no model: any placeholder will do.
    print(drawing(build_graph(model=object())))

    # SqliteSaver writes every step to disk: the state survives the
    # end of the program.
    with SqliteSaver.from_conn_string(DB_FILE) as saver:
        graph = build_graph(checkpointer=saver)
        config = {"configurable": {"thread_id": "essay-1"}}

        # stream() yields one update per node: we SEE the path.
        updates = graph.stream(
            {"topic": TOPIC}, config, stream_mode="updates"
        )
        for update in updates:
            for node, change in update.items():
                print(f"\n[{node}] {change}")

        final = graph.get_state(config).values
        count = final["revisions"]
        print(f"\nFinal draft after {count} revision(s):")
        print(final["draft"])


if __name__ == "__main__":
    try:
        main()
    except RateLimitError:
        # Free quotas are shared by everyone: it is not your code.
        sys.exit("The model is saturated (429). Wait a minute, or "
                 "change MODELE in .env (python modele.py).")
```

Le dessin d'abord : il n'a pas besoin de modèle, n'importe quel objet fait l'affaire. Puis chaque nœud qui se termine produit une ligne. (Le mode `updates` renvoie les changements de chaque nœud ; le mode `values` renvoie l'état complet après chaque étape. Le premier est plus lisible pour suivre un chemin.) Voici une vraie exécution, lancée avec le modèle gratuit par défaut (textes tronqués) :

```text
[write] {'draft': 'Checking weather forecasts helps ...'}
[critique] {'approved': False, 'feedback': 'Include a number ...'}
[rewrite] {'draft': 'User Safety: safe', 'revisions': 1}
[critique] {'approved': False, 'feedback': 'Add figures ...'}
[rewrite] {'draft': 'User Safety: safe', 'revisions': 2}
[critique] {'approved': False, 'feedback': 'Include metrics ...'}
```

Regarde le deuxième `rewrite`. Le modèle a répondu « User Safety: safe », un texte qui n'a plus rien à voir avec le sujet. Ce n'est pas un bug de ton code : un modèle gratuit peut dérailler à la réécriture. Deux choses sauvent l'exécution. La limite de deux réécritures arrête la boucle au lieu de la laisser tourner. Et le `stream` te montre exactement quelle étape a déraillé, ce qu'un `invoke` aurait caché.

> ⚠️ **Piège classique** — Un graphe avec une boucle et sans limite. Si le critique n'approuve jamais, l'agent tourne jusqu'à épuiser ton quota ou ton budget. Ajoute toujours une sortie par compteur, comme `max_revisions`, et teste-la.

## Toutes les sortes de flèches

Notre atelier n'utilise que deux flèches : la simple et la conditionnelle. LangGraph en connaît d'autres, et tu les retrouveras dans myTravel. Pour les voir sans bruit, oublie le modèle : chaque nœud se contente d'écrire son nom dans une liste, `log`.

```python
import operator
from typing import Annotated, TypedDict

class State(TypedDict):
    log: Annotated[list, operator.add]  # each node appends

def step(name):
    """A fake node: it only writes its name in the log."""
    return lambda state: {"log": [name]}
```

`Annotated[list, operator.add]` déclare un **réducteur** : la règle qui fusionne la mise à jour d'un nœud avec la valeur déjà dans l'état. Ici, ajouter au bout. Tu vas voir dans un instant pourquoi il devient obligatoire.

**1. La flèche simple.** Toujours la même suite. `START` et `END` ne sont pas des nœuds : ce sont l'entrée et la sortie du graphe.

```python
graph.add_edge(START, "a")
graph.add_edge("a", "b")
graph.add_edge("b", END)
# log: ['a', 'b']
```

**2. La flèche conditionnelle.** Une fonction lit l'état et renvoie le nom de la suite. C'est notre `route_after_critique`, en miniature :

```python
def route(state):
    return "hostel" if state["budget"] < 500 else "hotel"

graph.add_conditional_edges(START, route, ["hostel", "hotel"])
# budget 300 -> log: ['hostel']
```

La liste en troisième argument annonce les destinations possibles. LangGraph s'en sert pour dessiner le graphe.

**3. L'éventail (*fan-out*).** Deux flèches partent du même nœud. Il n'y a pas de choix : les deux nœuds tournent, et **en même temps**.

```python
graph.add_edge(START, "plan")
graph.add_edge("plan", "weather")
graph.add_edge("plan", "visa")
```

**4. Le rendez-vous (*fan-in*).** Une liste de nœuds au départ de la flèche : `summary` attend que `weather` **et** `visa` aient fini, puis tourne une seule fois.

```python
graph.add_edge(["weather", "visa"], "summary")
# log: ['plan', 'visa', 'weather', 'summary']
```

`visa` avant `weather` ? Ce n'est pas une erreur. Deux nœuds parallèles finissent dans l'ordre qui leur plaît : ne compte jamais dessus.

> ⚠️ **Piège classique** — Deux nœuds parallèles qui écrivent la même clé sans réducteur. LangGraph ne sait pas laquelle des deux valeurs garder, alors il refuse : `InvalidUpdateError: At key 'log': Can receive only one value per step`. Le réducteur tranche : `operator.add` garde les deux.

**5. `Send` : autant de copies que nécessaire.** L'éventail a une limite : ses branches sont écrites dans le code. Trois villes à vérifier aujourd'hui, sept demain ? `Send("weather", {"city": "Rome"})` veut dire « lance le nœud `weather` avec cette entrée-là ». La fonction de routage renvoie une **liste** de `Send`, un par ville, et toutes les copies tournent en parallèle. L'état a maintenant une clé `cities` en plus de `log` :

```python
def one_per_city(state):
    return [Send("weather", {"city": city})
            for city in state["cities"]]

def weather(task):  # gets its Send input, not the state
    return {"log": [f"weather in {task['city']}"]}

graph.add_conditional_edges(START, one_per_city, ["weather"])
graph.add_edge("weather", END)
# cities ['Rome', 'Tokyo', 'Lima'] -> log: ['weather in Rome',
#   'weather in Tokyo', 'weather in Lima']
```

Deux différences avec l'éventail. Le nombre de branches se décide **à l'exécution**, d'après l'état. Et chaque copie reçoit **sa propre entrée** (ici `{"city": ...}`), pas l'état entier. Les résultats remontent par le réducteur. Ce motif a un nom, *map-reduce* : distribuer le travail, puis rassembler les morceaux. Au chapitre 13, myTravel lance ses agents spécialistes exactement comme ça, un `Send` par agent utile.

**6. `Command` : le nœud choisit lui-même.** Au lieu d'une fonction de routage à part, un nœud peut renvoyer d'un coup sa mise à jour et sa destination :

```python
def critique(state):
    ...
    return Command(update={"approved": False}, goto="rewrite")
```

C'est pratique quand le travail et la décision vont ensemble. Le prix : la flèche disparaît de `build_graph`, et il faut lire le corps du nœud pour connaître le chemin. On garde donc la flèche conditionnelle dans ce livre, plus lisible.

| Flèche | Comment on l'écrit | Quand |
|---|---|---|
| simple | `add_edge("a", "b")` | toujours la même suite |
| conditionnelle | `add_conditional_edges("a", f, [...])` | une suite parmi plusieurs |
| éventail | deux `add_edge` depuis `"a"` | des branches parallèles connues d'avance |
| rendez-vous | `add_edge(["b", "c"], "d")` | attendre plusieurs branches |
| `Send` | `f` renvoie `[Send(...), ...]` | un nombre de branches décidé à l'exécution |
| `Command` | le nœud renvoie `Command(goto=...)` | le nœud décide seul |

> 💡 **À retenir** — Une flèche conditionnelle choisit **une** suite. `Send` en lance **plusieurs**, autant que l'état le demande, chacune avec son entrée. Dès que deux nœuds tournent en parallèle, la clé qu'ils partagent doit avoir un réducteur.

## Checkpointing : sauvegarder, reprendre, mettre en pause

Dans `build_graph`, on a passé un `checkpointer`. Il enregistre l'état **après chaque nœud**, sous un `thread_id` (la même idée qu'au chapitre 2). Cela offre trois pouvoirs.

**Lire l'état à tout moment.** `graph.get_state(config).values` renvoie le dictionnaire courant, `.next` renvoie les nœuds qui restent à exécuter. Quand le graphe est terminé, `.next` est vide.

**Survivre à un redémarrage.** `InMemorySaver` vit dans la mémoire du programme. `SqliteSaver`, dans `main.py`, écrit dans un fichier :

```python
with SqliteSaver.from_conn_string(DB_FILE) as saver:
    graph = build_graph(checkpointer=saver)
```

Arrête le programme, relance-le avec le même `thread_id` : l'état est là. Un des tests le prouve avec deux graphes distincts qui lisent le même fichier.

**Mettre en pause.** `compile(interrupt_before=["rewrite"])` arrête le graphe juste avant le nœud `rewrite`. L'appel rend la main, l'état est sauvegardé, `get_state(config).next` vaut `("rewrite",)`. Un humain lit le conseil du critique, puis on reprend avec `graph.invoke(None, config)`, c'est-à-dire « continue où tu t'es arrêté ».

```python
graph = build_graph(model=model, review=True)
graph.invoke({"topic": "Lisbon"}, config)   # runs until the pause
print(graph.get_state(config).next)         # ('rewrite',)
graph.invoke(None, config)                  # the human said go
```

C'est la base de l'humain dans la boucle, qui reviendra pour valider une réservation avant de la lancer.

> 💡 **À retenir** — Checkpointer + `thread_id` = un état lisible, sauvegardé, reprenable. Avec `interrupt_before`, le même mécanisme sert de point d'arrêt pour un humain.

## QCM

**1.** Que peut faire un nœud LangGraph ?

- **a)** Renvoyer seulement ce qu'il change
- **b)** Renvoyer le nom du prochain nœud
- **c)** Renvoyer l'état complet recopié
- **d)** Laisser les autres clés de l'état intactes

**2.** Que fait une arête conditionnelle ?

- **a)** Elle appelle le modèle
- **b)** Elle lit l'état
- **c)** Elle peut renvoyer `END`
- **d)** Elle renvoie le nom du prochain nœud

**3.** Ton graphe tourne depuis dix minutes sans s'arrêter. Quelles causes sont plausibles ?

- **a)** Une boucle sans sortie par compteur
- **b)** Le fichier `.env` est absent
- **c)** Un compteur jamais incrémenté
- **d)** Le prompt est trop long

**4.** Comment reprendre un graphe mis en pause avec `interrupt_before` ?

- **a)** Relancer avec un nouveau `thread_id`
- **b)** Supprimer le checkpointer
- **c)** Appeler `compile()` à nouveau
- **d)** `graph.invoke(None, config)`

**5.** Après un plantage, l'état est vide. Quelles causes sont probables ?

- **a)** Le graphe n'a pas de nœud `END`
- **b)** Le checkpointer est un `InMemorySaver`
- **c)** Le `thread_id` n'est pas celui de la première exécution
- **d)** Le routage est trop long

**6.** Quand préférer LangGraph à LangChain ?

- **a)** Un modèle, des outils et une réponse
- **b)** Plusieurs agents qui se passent la main
- **c)** Une boucle avec condition d'arrêt
- **d)** Une pause pour un humain

**7.** Tu dois vérifier la météo d'une liste de villes dont la longueur change à chaque demande. Que fait `Send` ici ?

- **a)** Il lance le nœud `weather` une fois par ville, en parallèle
- **b)** Il envoie toutes les villes au même appel du nœud
- **c)** Il donne à chaque copie sa propre entrée, comme `{"city": "Rome"}`
- **d)** Il remplace le réducteur de la clé `log`

**Réponses.** Q1 : a, d · Q2 : b, c, d · Q3 : a, c · Q4 : d · Q5 : b, c · Q6 : b, c, d · Q7 : a, c

## Ce qu'il faut retenir
1. LangGraph décrit un agent comme un graphe : un état, des nœuds (fonctions) et des arêtes (flèches). Les boucles et les décisions deviennent des éléments normaux au lieu d'acrobaties.
2. Un nœud renvoie seulement ce qu'il change. Une arête conditionnelle est une fonction qui lit l'état et renvoie le nom du prochain nœud, ou `END`.
3. Plusieurs flèches qui partent d'un nœud font tourner leurs branches en parallèle ; `add_edge([...], "d")` les attend toutes. `Send` lance autant de copies d'un nœud que l'état le demande, chacune avec son entrée. Une clé écrite en parallèle a besoin d'un réducteur.
4. Toute boucle a besoin d'une sortie de secours par compteur (`max_revisions`). Sans elle, un critique trop exigeant épuise ton quota.
5. Le checkpointer sauvegarde l'état à chaque nœud : lecture avec `get_state`, survie à l'arrêt avec `SqliteSaver`, pause avec `interrupt_before` puis reprise avec `invoke(None, config)`.
6. LangChain pour un agent simple, LangGraph dès qu'il y a une boucle, une branche, une pause ou plusieurs agents.

**Au chapitre suivant :** un graphe organise des étapes, mais chaque étape reste un appel de modèle générique. Et si chaque étape était tenue par un spécialiste, avec son métier, ses objectifs et sa façon de parler ? CrewAI décrit des agents par rôles. Tu compareras ses forces à celles de LangGraph sur le même exercice.

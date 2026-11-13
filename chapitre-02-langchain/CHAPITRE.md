# Chapitre 2 — LangChain : le même agent en vingt lignes

> **Dossier GitHub associé :** `chapitre-02-langchain/`

**À la fin de ce chapitre, tu sauras :**

- expliquer ce que LangChain apporte, et ce qu'il ne fait pas à ta place ;
- transformer une fonction Python en outil sans écrire de schéma JSON ;
- construire un agent avec `create_agent` et un `PromptTemplate` ;
- donner une mémoire à l'agent avec un `checkpointer` et un `thread_id` ;
- brancher des outils réels (Wikipedia, météo, taux de change) et les tester hors ligne.

## Le jour où j'ai ajouté un outil à trois endroits

Retour chez Inès. Son agent du chapitre 1 connaît trois outils, et elle veut un quatrième : convertir des euros en yens. Simple, non ? Il faut toucher trois endroits.

La fonction Python, dans `tools.py`. Son schéma JSON, écrit à la main, dans `TOOL_SCHEMAS`. L'entrée du catalogue `TOOLS`. Oublie de resynchroniser un seul des trois et le modèle appelle `convert_currency` avec un argument `montant`, alors que ta fonction attend `amount`. L'erreur tombe en pleine conversation, et son message ne dit pas où chercher.

Rien de difficile là-dedans. C'est de la plomberie, répétée pour chaque outil, et la plomberie se désynchronise toujours un vendredi soir.

Ce chapitre la supprime. Tu gardes la fonction, tu jettes le reste, et l'agent complet tient en une vingtaine de lignes.

## Pourquoi LangChain ?

**LangChain** est une bibliothèque Python qui range derrière quelques objets prêts à l'emploi tout ce que tu as écrit à la main : l'appel au modèle, la description des outils, la boucle, la mémoire. Pourquoi la choisir ici ?

D'abord parce que tu manipules un « modèle de chat » au lieu d'un client HTTP : changer de modèle ne touche pas une ligne de ton agent. Ensuite parce que c'est la bibliothèque que citent la plupart des tutoriels et des offres d'emploi, avec des centaines d'intégrations (bases vectorielles, moteurs de recherche, outils de suivi). Enfin parce qu'elle sert de passerelle : le chapitre suivant reprend exactement les mêmes briques.

Elle a un prix, et il vaut mieux le connaître : une couche de plus entre toi et le modèle. Quand quelque chose casse, il faut parfois descendre lire le code de la bibliothèque. C'est là que le chapitre 1 te sauve : tu sais ce que la boucle fait, donc tu sais où chercher.

Pour mesurer le gain, compare les deux chapitres sur le même agent :

| | Chapitre 1 (à la main) | Chapitre 2 (LangChain) |
|---|---|---|
| Ajouter un outil | 3 endroits à modifier | 1 fonction + 1 entrée de liste |
| Schéma JSON | écrit à la main | lu dans la docstring |
| Boucle ReAct | une vingtaine de lignes à toi | `create_agent` |
| Mémoire | liste `messages` gérée par toi | checkpointer + `thread_id` |
| Limite de tours | `max_turns` | limite de récursion intégrée |

Verdict : pour un agent simple avec quelques outils, LangChain est le chemin le plus court. Dès que le flux se complique (boucles, validation humaine), rendez-vous au chapitre 3.

> 💡 **À retenir** — LangChain ne rend pas l'agent plus intelligent. Il écrit à ta place la plomberie que tu as écrite au chapitre 1 : schémas, boucle, historique de messages.

## Les quatre briques à connaître

Quatre notions suffisent pour lire n'importe quel agent LangChain.

**Le modèle de chat** (*ChatModel*). Un objet qui sait recevoir des messages et en renvoyer un. Pour nous, c'est `ChatOpenAI`, pointé sur OpenRouter. La règle du livre reste valable : un seul fichier, `modele.py`, nomme un fournisseur.

C'est ici que la promesse du chapitre 1 se vérifie. Ajoute une ligne `MODELE=qwen/qwen3.8-27b:free` dans ton `.env`, relance `main.py` : le même agent tourne sur un autre modèle, sans toucher au code. Les modèles gratuits se valent rarement pour l'appel d'outils. Si l'un ignore tes outils ou se trompe d'argument, change de slug avant de changer de code. `python modele.py` liste ce qui est disponible aujourd'hui.

**Le PromptTemplate.** Un texte à trous, rempli au dernier moment. Les consignes de l'agent contiennent la date du jour et la langue de réponse : on ne veut pas les écrire en dur.

**L'outil** (*tool*). Une fonction Python décorée par `@tool`. LangChain lit son nom, ses types et sa docstring, et fabrique le schéma que tu écrivais à la main.

**L'agent.** Un objet qui contient le modèle, les outils et les consignes, et qui connaît la boucle du chapitre 1. On lui envoie des messages, il renvoie la conversation complète.

## Pratique : qui fait quoi, et comment le lancer

Le tour du propriétaire avant le code. Tu vas voir que le dossier est plus court, et c'est justement le but de LangChain.

### Les fichiers et leur rôle

```text
chapitre-02-langchain/
├── main.py    ← point d'entrée : trois questions de suite
├── agent.py   ← l'agent : prompt, create_agent, mémoire
├── tools.py   ← quatre outils @tool, sans schéma écrit à la main
├── modele.py  ← la prise : client OpenRouter pour LangChain
└── tests/     ← faux modèle, sans clé d'API
```

Le fichier du chapitre 1 qui gérait la mémoire a disparu, et la boucle de `agent.py` tient en une dizaine de lignes. Ce que tu avais écrit à la main, LangChain le fait à ta place.

### Les cinq détails à comprendre avant de lire le code

1. **`@tool` lit ta fonction.** Le nom, les types et la docstring deviennent le schéma que tu écrivais à la main. La docstring est le mode d'emploi du modèle.
2. **`create_agent` contient la boucle.** Plus de `tool_calls` à lire, plus de compteur de tours : tu donnes modèle, outils et consignes.
3. **La mémoire, c'est un `thread_id`.** Même identifiant, même conversation. Un autre identifiant, page blanche.
4. **Le `PromptTemplate` est un texte à trous.** La date du jour et la langue y sont injectées au moment de construire l'agent.
5. **Tout se teste avec un faux modèle.** `tools.py` passe par une seule porte réseau, `_get_json`, que les tests remplacent.

## L'outil et le prompt : deux briques sans plomberie

### Un outil, sans schéma écrit à la main

Voici `tools.py`, en entier. Le haut du fichier pose les opérateurs autorisés pour `calculate` (le même garde-fou qu'au chapitre 1) et la seule porte vers le réseau :

<!-- code: tools.py 1-38 -->
```python
"""myTravel's tools, written for LangChain.

Compare with chapter 1: no JSON schema written by hand. The `@tool`
decorator reads the function name, its type hints and its docstring
and builds the description the model needs. The docstring IS the
manual, so write it for the model, not for yourself.

Three tools call real, free APIs that need no key:
Wikipedia (facts), Open-Meteo (weather), Frankfurter (rates).
"""

import ast
import json
import operator
import urllib.parse
import urllib.request

from langchain.tools import tool

OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub,
             ast.Mult: operator.mul, ast.Div: operator.truediv,
             ast.Pow: operator.pow, ast.USub: operator.neg}


def _get_json(url, params=None):
    """The single network door. Tests replace this function.

    Plain `urllib`, from the standard library: nothing to install,
    and it trusts the system certificate store (corporate proxies).
    """
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    # Wikipedia refuses requests without an identifiable User-Agent.
    agent_name = "agentia-book/1.0 (github.com/btecsec)"
    request = urllib.request.Request(
        url, headers={"User-Agent": agent_name})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)
```

Les trois outils « réels » interrogent des API gratuites, sans clé : Wikipedia, Open-Meteo, Frankfurter. Ils passent tous par `_get_json`, une petite fonction basée sur `urllib`. C'est la seule porte vers le réseau : les tests la remplacent, et tout le reste fonctionne hors ligne. Wikipedia et plusieurs API refusent les requêtes anonymes, d'où le `User-Agent`, une règle de politesse autant qu'une nécessité.

Compare maintenant avec le chapitre 1. Voici la recherche et le calcul, version LangChain :

<!-- code: tools.py 41-86 -->
```python
@tool(parse_docstring=True)
def web_search(query: str) -> str:
    """Look up a place, a person or a concept on Wikipedia.

    Use it before answering any factual question about a destination
    (history, size, country, main sights).

    Args:
        query: The page title to look up, for example 'Lisbon'.
    """
    title = query.strip().replace(" ", "_")
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        page = _get_json(url + title)
    except OSError as error:
        # A sentence, not an exception: the model adapts to it.
        return f"No result for {query!r} ({error})."
    return page.get("extract") or f"No summary for {query!r}."


@tool(parse_docstring=True)
def calculate(expression: str) -> str:
    """Evaluate arithmetic. Never calculate in your head.

    Args:
        expression: A formula such as '3 * 120 * 1.085'.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_evaluate(tree.body))
    except (ValueError, SyntaxError, ZeroDivisionError) as error:
        return f"Cannot calculate {expression!r}: {error}"


def _evaluate(node):
    """Accept numbers and + - * / ** only: never eval model text."""
    if isinstance(node, ast.Constant) and isinstance(
        node.value, (int, float)
    ):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = _evaluate(node.left), _evaluate(node.right)
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("only numbers and + - * / ** are allowed")
```

Il n'y a plus de dictionnaire de schéma. Le nom de l'outil, c'est le nom de la fonction. Sa description, c'est le début de la docstring. La description de chaque paramètre vient de la section `Args:`, lue grâce à `parse_docstring=True`. Les types viennent des annotations (`query: str`). Tu peux vérifier ce que le modèle va lire :

```python
print(convert_currency.args)
# {'amount': {'description': 'The amount to convert...',
#             'type': 'number', ...},
#  'source': {'description': 'The ISO code of the...', ...}}
```

> ⚠️ **Piège classique** — La docstring n'est plus un commentaire pour toi, c'est le manuel du modèle. Une docstring vague (« Utilitaire de météo ») donne un modèle qui n'appelle pas l'outil au bon moment. Écris-la comme une consigne : quand l'utiliser, ce que chaque argument doit contenir.

Les deux derniers outils suivent le même modèle :

<!-- code: tools.py 89-144 -->
```python
@tool(parse_docstring=True)
def get_weather(city: str) -> str:
    """Get the current temperature in a city (Open-Meteo data).

    Args:
        city: The city name, for example 'Tokyo'.
    """
    try:
        found = _get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": city, "count": 1},
        ).get("results")
        if not found:
            return f"Unknown city {city!r}."
        place = found[0]
        current = _get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m",
            },
        )["current"]
    except (OSError, ValueError, KeyError) as error:
        return f"Weather service unavailable ({error})."
    degrees = current["temperature_2m"]
    where = f"{place['name']}, {place['country']}"
    return f"{where}: {degrees} degrees C."


@tool(parse_docstring=True)
def convert_currency(
    amount: float, source: str, target: str
) -> str:
    """Convert an amount between two currencies (real rates).

    Args:
        amount: The amount to convert, for example 250.
        source: The ISO code of the starting currency, e.g. 'EUR'.
        target: The ISO code of the target currency, e.g. 'JPY'.
    """
    try:
        data = _get_json(
            "https://api.frankfurter.dev/v1/latest",
            {"base": source.upper(), "symbols": target.upper()},
        )
        rate = data["rates"][target.upper()]
    except (OSError, ValueError, KeyError) as error:
        return f"Cannot convert {source} to {target} ({error})."
    converted = amount * rate
    code = target.upper()
    return f"{amount} {source.upper()} = {converted:.2f} {code}"


# A "toolkit" is a list of tools handed to the agent together.
TOOLKIT = [web_search, calculate, get_weather, convert_currency]
```

`get_weather` fait deux appels : le géocodage transforme « Tokyo » en coordonnées, puis la prévision donne la température à ces coordonnées. Chaque erreur réseau devient une phrase, jamais une exception.

Un **toolkit** (« boîte à outils ») n'a rien de mystérieux : c'est une liste d'outils qu'on donne ensemble à l'agent. Les bibliothèques d'intégration livrent des toolkits tout faits (SQL, GitHub, e-mail). Le principe est le même.

### Le prompt : un texte à trous

Les consignes de l'agent changent avec le contexte : la date, la langue, plus tard le profil du voyageur. Un `PromptTemplate` garde le texte fixe d'un côté, les valeurs variables de l'autre. Il ouvre `agent.py` :

<!-- code: agent.py 1-29 -->
```python
"""myTravel with LangChain: the chapter 1 agent in about 20 lines.

In chapter 1 we wrote the loop "the model asks for a tool, we
run it, we hand back the result".
LangChain ships that loop ready-made.

What disappears: hand-written JSON schemas, reading `tool_calls`,
`tool` messages, the turn counter, the message list.
What stays: your tools. That is the whole point.
"""

from datetime import date

from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import InMemorySaver

from modele import get_chat_model
from tools import TOOLKIT

# A PromptTemplate is a text with holes ({today}, {language}) filled
# at the last moment. Same template, different values per user.
SYSTEM_TEMPLATE = PromptTemplate.from_template(
    "You are myTravel, a travel assistant. Today is {today}.\n"
    "Use a tool whenever the answer depends on real-world data "
    "(weather, exchange rates, facts). Never calculate in your "
    "head: use `calculate`. Answer in {language}, in three "
    "sentences max."
)
```

Les accolades `{today}` et `{language}` sont les trous. On les remplit avec `.format(today=..., language=...)`. La date du jour est une information que le modèle ne peut pas deviner : sans elle, « le 3 mai » n'a pas d'année.

> 💡 **À retenir** — Mets dans le prompt système ce qui est stable (le rôle, les règles) et dans les variables ce qui change (date, langue, profil). Tu auras un seul texte à relire, et un seul endroit où le corriger.

## L'agent en vingt lignes

Voici le morceau qui remplace toute la classe `Agent` du chapitre 1 :

<!-- code: agent.py 32-43 -->
```python
def build_agent(model=None, language="English", checkpointer=None):
    """Assemble the agent. Tests inject a fake `model`."""
    system_prompt = SYSTEM_TEMPLATE.format(
        today=date.today().isoformat(), language=language
    )
    return create_agent(
        model=model or get_chat_model(),
        tools=TOOLKIT,
        system_prompt=system_prompt,
        # The memory: conversations are saved per `thread_id`.
        checkpointer=checkpointer or InMemorySaver(),
    )
```

Douze lignes. Cherche ce qui a disparu : plus de `while`, plus de `max_turns`, plus de lecture de `tool_calls`, plus de message `tool` à construire. `create_agent` fait tout ça. Il choisit aussi une limite de récursion par défaut, qui joue le rôle de notre `max_turns`.

**Sous le capot.** `create_agent` ne cache pas une boucle `while`. Il construit un graphe : un nœud « modèle », un nœud « outils », et une flèche qui revient du second au premier tant que le modèle demande des outils. C'est exactement la boucle du chapitre 1, dessinée au lieu d'être écrite. Le checkpointer vient d'ailleurs de LangGraph, la bibliothèque du chapitre suivant.

Le paramètre `model` accepte un faux modèle, comme le `client` du chapitre 1 : c'est ce qui permet de tester sans clé. Le vrai vient de `get_chat_model`, la seule fonction que `modele.py` gagne par rapport au chapitre 1 :

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

`ChatOpenAI` est la classe de LangChain qui parle le dialecte d'OpenAI ; on lui donne l'adresse d'OpenRouter, et le reste ne change pas. La clé est lue par `get_client`, pour garder un seul endroit qui la cherche et un seul message d'erreur si elle manque.

Pour poser une question, on envoie une liste de messages, et on lit la conversation complète au retour :

<!-- code: agent.py 46-62 -->
```python
def ask(agent, question, thread_id="trip-1"):
    """Ask a question. Returns (answer, tools called)."""
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [("user", question)]}
    result = agent.invoke(inputs, config)
    messages = result["messages"]
    # The thread keeps the whole conversation: only look at this
    # turn, i.e. what follows the last human message.
    humans = [i for i, m in enumerate(messages)
              if m.type == "human"]
    last_human = humans[-1]
    tools_called = [
        call["name"]
        for message in messages[last_human:]
        for call in getattr(message, "tool_calls", [])
    ]
    return messages[-1].content, tools_called
```

La dernière réponse est `messages[-1]`. Le reste de la liste, ce sont les appels d'outils et leurs résultats, ce que ton `self.messages` contenait au chapitre 1. Comme le checkpointer garde toute la conversation, `ask` ne regarde que ce qui suit la dernière question pour lister les outils appelés à ce tour.

## La mémoire : un `thread_id`

Au chapitre 1, la mémoire était une liste que tu gérais toi-même. Ici, tu donnes un **checkpointer** à l'agent : un objet qui sauvegarde la conversation après chaque étape, comme un carnet qu'on referme et qu'on rouvre à la bonne page. `InMemorySaver` la garde dans la mémoire du programme.

Ce qui distingue deux conversations, c'est le `thread_id` (le « fil »). Même `thread_id`, même conversation. Autre `thread_id`, page blanche. Regarde `main.py`, le dernier fichier :

<!-- code: main.py -->
```python
"""Run chapter 2:  python main.py

Needs OPENROUTER_API_KEY in the .env file at the repository root.
"""

import sys

from openai import RateLimitError

from agent import ask, build_agent

# The agent is built ONCE and keeps the conversation under one
# thread_id: the second question relies on the first.
QUESTIONS = [
    "Give me two facts about Lisbon.",
    "What is the weather there right now?",
    "What do 250 euros make in Japanese yen?",
]


def main():
    agent = build_agent()
    for question in QUESTIONS:
        answer, tools_called = ask(agent, question)
        print(f"\n> {question}")
        print(f"  tools: {tools_called or 'none'}")
        print(f"< {answer}")


if __name__ == "__main__":
    try:
        main()
    except RateLimitError:
        # Free quotas are shared by everyone: it is not your code.
        sys.exit("The model is saturated (429). Wait a minute, or "
                 "change MODELE in .env (python modele.py).")
```

L'agent est construit une seule fois, et `ask` utilise toujours le fil `trip-1`. Lance `python main.py` :

```text
> Give me two facts about Lisbon.
  tools: ['web_search']
< Lisbon is the capital and most populous city of Portugal ...

> What is the weather there right now?
  tools: ['get_weather']
< It is 21.5 degrees C in Lisbon right now.

> What do 250 euros make in Japanese yen?
  tools: ['convert_currency']
< 250 euros convert to approximately 44,212.50 Japanese yen ...
```

Le « there » de la deuxième question se résout tout seul. Pas une ligne de gestion de l'historique dans `main.py`.

Tu peux aussi inspecter la mémoire à tout moment. `agent.get_state(config)` renvoie l'état d'un fil, avec la liste de ses messages. C'est ce que fait le test `test_memory_is_kept_per_thread` : deux questions sur le fil A donnent quatre messages (deux questions, deux réponses), une question sur le fil B en donne deux. Le prompt système n'y figure pas : il est ajouté à chaque appel, sans grossir l'historique.

Le remplaçant de `ConversationBufferMemory`, c'est donc ceci : un checkpointer plus un `thread_id`. Il fait mieux que l'ancien, puisqu'il garde aussi les appels d'outils. Il a la même limite que ta liste du chapitre 1 : `InMemorySaver` s'efface quand le programme s'arrête, et la conversation grossit jusqu'à saturer la fenêtre de contexte. Le chapitre 3 branche une sauvegarde sur disque.

> 💡 **À retenir** — Mémoire LangChain moderne : un checkpointer (où l'on sauvegarde) et un `thread_id` (quelle conversation). Deux conversations, deux identifiants.

> ⚠️ **Piège classique** — Oublier le `thread_id`. Sans lui, un agent avec checkpointer lève une erreur. Avec un `thread_id` fixe pour tous les utilisateurs d'un site web, c'est pire : tout le monde partage la même conversation. Un identifiant par utilisateur, toujours.

## Bonnes pratiques et pièges courants

**Une erreur d'outil est une phrase.** Comme au chapitre 1, tes outils attrapent les erreurs réseau et renvoient un texte. Une exception non rattrapée remonte à travers l'agent et interrompt la conversation. Pendant l'écriture de ce chapitre, Wikipedia a répondu `403 Forbidden` à un client HTTP pourtant correct : sans la phrase d'erreur, l'agent aurait planté, avec elle il a répondu qu'il ne trouvait rien.

**Un `User-Agent` honnête.** Wikipedia et plusieurs API refusent les requêtes anonymes. `_get_json` envoie un nom d'application, et c'est une règle de politesse autant qu'une nécessité.

**Pas d'`eval()` sur du texte de modèle.** `calculate` lit l'expression avec le module `ast` et refuse tout sauf des nombres et des opérateurs. Le modèle écrit ce qu'on lui demande d'écrire, ou ce qu'une page web piégée lui a soufflé.

**Un prompt qui dit quand utiliser chaque outil.** Les modèles gratuits hésitent plus que les gros. La phrase « Never calculate in your head: use `calculate` » a plus d'effet que dix lignes de théorie.

**Peu d'outils, bien décrits.** Chaque outil ajoute sa description à chaque requête, donc des tokens et du bruit. Au-delà d'une dizaine d'outils, les petits modèles se trompent plus souvent d'outil : c'est mon observation sur des modèles gratuits, pas une loi. Mieux vaut cinq outils nets que vingt outils flous. Quand la liste grossit vraiment, on répartit les outils entre plusieurs agents (chapitres 4 et suivants).

**Regarder la conversation complète.** Quand l'agent se comporte mal, affiche `result["messages"]` en entier. Tu y vois la décision du modèle, l'argument envoyé à l'outil et le texte rendu. C'est le journal `ACT`/`OBSERVE` du chapitre 1, version LangChain.

## QCM

**1.** Que lit `@tool(parse_docstring=True)` pour fabriquer le schéma d'un outil ?

- **a)** Le nom de la fonction
- **b)** La clé d'API
- **c)** La docstring
- **d)** Les types des paramètres

**2.** À quoi sert un `PromptTemplate` ?

- **a)** À isoler ce qui varie (date, langue, profil)
- **b)** À appeler le modèle plus vite
- **c)** À garder un prompt système stable
- **d)** À remplacer les outils

**3.** Deux utilisateurs voient les messages l'un de l'autre malgré `InMemorySaver`. Où cherches-tu d'abord ?

- **a)** Dans le `thread_id`, probablement identique pour tous
- **b)** Dans la docstring des outils
- **c)** Dans la version de LangChain
- **d)** Dans le choix du modèle

**4.** Tu relances le programme demain et l'agent a oublié hier. Quelles affirmations sont vraies ?

- **a)** `InMemorySaver` vit dans la mémoire du programme
- **b)** C'est un bug de LangChain
- **c)** Le modèle gratuit efface l'historique
- **d)** Il faut un checkpointer persistant pour survivre à l'arrêt

**5.** Pourquoi `calculate` lit-il l'expression avec `ast` plutôt qu'avec `eval()` ?

- **a)** `ast` refuse tout sauf nombres et opérateurs
- **b)** `ast` est plus rapide
- **c)** Une page web piégée peut lui souffler du code
- **d)** Le texte vient du modèle

**Réponses.** Q1 : a, c, d · Q2 : a, c · Q3 : a · Q4 : a, d · Q5 : a, c, d

## Ce qu'il faut retenir
1. LangChain range derrière quelques objets (modèle, outils, agent) la plomberie du chapitre 1 : schémas, boucle, historique. Il n'ajoute pas d'intelligence.
2. `@tool(parse_docstring=True)` fabrique le schéma d'un outil depuis son nom, ses types et sa docstring. La docstring est le manuel du modèle.
3. Un `PromptTemplate` est un texte à trous. Il garde le prompt système stable et sépare ce qui varie : date, langue, profil.
4. `create_agent` assemble modèle, outils, consignes et mémoire. La mémoire est un `checkpointer` plus un `thread_id`, qui remplace `ConversationBufferMemory`.

**Au chapitre suivant :** ton agent suit une ligne droite : le modèle, les outils, le modèle. Le jour où tu veux « rédige, fais critiquer, puis réécris », ou « demande confirmation avant d'agir », cette ligne droite ne suffit plus. LangGraph te laisse dessiner le chemin au lieu de le deviner.

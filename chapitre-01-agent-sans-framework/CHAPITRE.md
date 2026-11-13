# Chapitre 1 — Qu'est-ce qu'un agent IA ? Écris le tien, sans framework

> **Dossier GitHub associé :** `chapitre-01-agent-sans-framework/`

**À la fin de ce chapitre, tu sauras :**

- définir un agent IA en une phrase et le distinguer d'un simple chatbot ;
- écrire une boucle ReAct complète en Python pur, en une quarantaine de lignes ;
- donner à un modèle des outils qu'il peut appeler, et lui rendre leurs résultats ;
- garder une conversation dans la fenêtre de contexte du modèle ;
- tester ta boucle sans clé d'API et sans dépenser un centime.

## Le jour où le modèle a fait une erreur de calcul

Inès part à Tokyo avec deux amis. Trois nuits à 120 € la nuit, plus 8,5 % de taxe de séjour. Elle demande le total à un modèle d'IA, qui répond avec un aplomb de notaire : « 390,60 € ».

C'est juste. Alors elle repose la question, par pur plaisir de le voir recommencer. « 396 € ». Troisième essai : « 391,20 € ». Même modèle, même question, trois budgets, et chaque fois le même ton calme.

Le modèle ne calcule pas. Il écrit le chiffre qui *ressemble* à une réponse, comme quelqu'un qui finirait ta phrase sans avoir écouté le début. Même histoire pour l'heure, la météo, le prix d'un vol : un modèle de langage lit du texte et en écrit, point. Pas d'horloge, pas de calculatrice, pas d'accès au web. Un cerveau dans un bocal : brillant, mais incapable de tendre le bras.

Un **agent** casse le bocal. Dans ce chapitre, tu écris celui d'Inès : un agent de voyage qui sort la calculatrice, consulte la météo et fouille une base de connaissances avant d'ouvrir la bouche (factices au départ, on branchera du réel au chapitre 2). Une quarantaine de lignes de Python, aucun framework, et à la fin plus personne ne devine un total.

## Ce qu'est un agent, et ce que tu vas construire

Un **agent IA** se résume à trois ingrédients :

1. un **LLM** (*Large Language Model*, grand modèle de langage) : le cerveau, qui lit du texte et en produit ;
2. des **outils** : des fonctions Python que le modèle peut demander d'exécuter ;
3. une **boucle de décision** : ton code relance le modèle tant qu'il demande des outils, et s'arrête quand il répond.

Enlève les outils, tu as un chatbot. Enlève la boucle, tu as un appel d'API. C'est la combinaison qui fait l'agent.

La différence se voit sur une question concrète. Un chatbot répond à « Quel temps fait-il à Lisbonne ? » avec ce qu'il a lu pendant son entraînement, c'est-à-dire des moyennes de saison. Un agent comprend qu'il lui manque une donnée du moment, appelle un outil météo, lit le résultat et seulement ensuite répond. Dans les deux cas le modèle est le même. Seul l'entourage change.

![La boucle de l'agent : le modèle reçoit la question, demande un outil ou répond](chapitre-01-agent-sans-framework/images/agent-boucle.png){width=13.3cm}

> 💡 **À retenir** — Agent = LLM + outils + boucle. Le modèle *décide*, ton code *exécute*. Le modèle n'exécute jamais rien lui-même.

Tout le livre construit **myTravel**, un assistant de voyage. Il cherche et compare, il ne réserve jamais à ta place. Dans ce chapitre, il sait trois choses : chercher un fait sur une ville, calculer, donner la météo.

Un mot sur la plomberie, que tu peux survoler. Les modèles passent tous par **OpenRouter**, un guichet unique qui donne accès à des dizaines de modèles avec une seule clé et un seul format. Pourquoi ce détour ? Parce que changer de modèle devient une ligne dans `.env` au lieu d'une réécriture. Tu compares sans ouvrir dix comptes, et le routage du dernier chapitre n'existerait pas sans lui.

Le modèle par défaut est gratuit (le slug, c'est-à-dire le nom `fournisseur/modele`, se termine par `:free`). OpenRouter demande une carte à l'inscription pour vérifier que tu es humain, mais rien n'est prélevé tant que tu restes sur un modèle gratuit.

## Pratique : qui fait quoi, et comment le lancer

Avant d'entrer dans le code, prends dix minutes pour faire le tour du propriétaire. Quand tu sais quel fichier fait quoi, le reste du chapitre se lit presque tout seul.

### Les fichiers et leur rôle

Le dossier `chapitre-01-agent-sans-framework/` contient cinq fichiers de code, plus les tests :

```text
chapitre-01-agent-sans-framework/
├── main.py    ← point d'entrée : c'est lui que tu lances
├── agent.py   ← le cerveau : classe Agent, boucle ReAct
├── tools.py   ← les mains : 3 outils + leurs descriptions
├── memory.py  ← la mémoire : compter, couper l'historique
├── modele.py  ← la prise : client OpenRouter
└── tests/     ← filets de sécurité, sans clé d'API
```

Le chapitre vit dans les trois fichiers du milieu : `agent.py`, `tools.py`, `memory.py`. `modele.py` est la prise vers le modèle : tu le liras une fois, ici ; chaque chapitre en garde une copie.

### Lancer le programme

Une seule installation, à la racine du dépôt, pour tout le livre :

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
cp .env.example .env       # puis colle ta clé OpenRouter
```

Ensuite, dans le dossier du chapitre :

```bash
cd chapitre-01-agent-sans-framework
python modele.py   # 1. modèles gratuits capables d'outils
python main.py     # 2. l'agent, tour par tour
pytest             # 3. les tests, sans clé ni réseau
```

L'ordre compte. `python modele.py` d'abord : il vérifie que ta clé fonctionne et te montre quels modèles gratuits sont disponibles aujourd'hui (les noms changent tous les quelques mois). Si `main.py` affiche « Missing key », ton `.env` n'est pas au bon endroit ou la clé est vide. Si les accents s'affichent de travers sous Windows, tape `set PYTHONUTF8=1` avant de relancer.

Voici ce que tu verras en lançant `python main.py` :

```text
> What is the weather there, and what do 3 nights at 120 euros cost?
  [turn 1] ACT     get_weather({"city": "Tokyo"})
  [turn 1] OBSERVE Weather in Tokyo: 18 degrees C, light rain.
  [turn 2] ACT     calculate({"expression": "3 * 120"})
  [turn 2] OBSERVE 360
< The weather in Tokyo is 18 degrees C with light rain. 3 nights at
  120 euros per night cost 360 euros total.
```

Deux outils, deux tours, une réponse. Et le « there » de la question n'a jamais été expliqué : l'agent se souvient que la question précédente parlait de Tokyo. C'est sa mémoire, et elle tient dans une liste Python.

> 💡 **À retenir** — Trois commandes à connaître pour tout le livre : `python modele.py` (quel modèle ?), `python main.py` (l'agent tourne-t-il ?), `pytest` (le code est-il correct ?). Chaque chapitre suivant garde la même mécanique.

### Les cinq détails à comprendre avant de lire le code

Si tu ne devais retenir que cinq choses du code qui suit, ce seraient celles-là. Chacune est détaillée plus bas :

1. **`self.messages` est toute la mémoire.** Une simple liste Python. Le modèle ne sait que ce qu'elle contient.
2. **Chaque tour renvoie toute la liste au modèle.** Ce n'est pas lui qui se souvient : c'est ton code qui lui relit la conversation depuis le début, à chaque fois.
3. **Le modèle demande, ton code exécute.** Le modèle renvoie un `tool_calls`, jamais un résultat. C'est `_run_tool` qui lance la vraie fonction.
4. **Une erreur est un texte, pas une exception.** Outil inconnu, JSON cassé, ville introuvable : on rend une phrase au modèle, qui se corrige tout seul.
5. **`max_turns` est le garde-fou.** Sans lui, un agent perdu boucle indéfiniment et la facture grimpe.

Garde cette liste sous les yeux en lisant la suite. Quand tu rencontreras une fonction, demande-toi : « laquelle de ces cinq idées elle met en œuvre ? »

## Les outils : une fonction pour toi, une description pour le modèle

Un outil a deux faces. La première est une fonction Python que **ton** code exécute. La seconde est une description que **le modèle** lit. Il ne voit jamais ta fonction, seulement sa description : c'est son unique mode d'emploi.

Ce mécanisme porte un nom : le *function calling* (appel de fonction). Tu envoies au modèle ta question **et** la liste des outils disponibles. Au lieu de répondre, il peut renvoyer : « appelle `calculate` avec `3 * 120` ». Ton code lance la fonction, puis rend le résultat.

Voici `tools.py`, en entier. D'abord les données factices et la liste des opérateurs autorisés :

<!-- code: tools.py 1-31 -->
```python
"""The agent's tools: fake, on purpose.

A tool is two things:
1. a Python function that YOUR code runs;
2. a description that THE MODEL reads.

The model never sees your function, only its description. Write it
carefully: it is the model's only manual. The tools are fake (three
facts, simulated weather) so every run gives the same answers and
the tests need no network.
"""

import ast
import operator

# The "web" of this chapter: three facts, enough to see search work.
KNOWLEDGE_BASE = {
    "tokyo": "Tokyo: 14 million people, capital of Japan, UTC+9.",
    "lisbon": "Lisbon: 550,000 people, capital of Portugal, UTC+0.",
    "kyoto": "Kyoto: 1.4 million people, imperial capital to 1868.",
}
WEATHER = {
    "tokyo": "18 degrees C, light rain",
    "lisbon": "24 degrees C, sunny",
    "kyoto": "16 degrees C, cloudy",
}
# Only these operators are allowed in `calculate`. Never eval() text
# written by a model: it could run anything.
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub,
             ast.Mult: operator.mul, ast.Div: operator.truediv,
             ast.Pow: operator.pow, ast.USub: operator.neg}
```

Ces outils sont **factices** à dessein : une mini base de trois villes, une météo figée. Tes tests donneront toujours la même réponse, sans réseau. Au chapitre 2, on branchera de vraies sources.

Puis les trois fonctions, la première face des outils :

<!-- code: tools.py 34-72 -->
```python
def search(query):
    """Look up a city in the fake knowledge base."""
    for city, fact in KNOWLEDGE_BASE.items():
        if city in query.lower():
            return fact
    # A sentence, not an exception: the model reads it and adapts.
    known = ", ".join(KNOWLEDGE_BASE)
    return f"Nothing found for {query!r}. Known: {known}."


def calculate(expression):
    """Evaluate basic arithmetic, safely."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(evaluate(tree.body))
    except (ValueError, SyntaxError, ZeroDivisionError) as error:
        return f"Cannot calculate {expression!r}: {error}"


def evaluate(node):
    """Walk the syntax tree: numbers and operators, nothing else."""
    if isinstance(node, ast.Constant) and type(node.value) in (
            int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = evaluate(node.left), evaluate(node.right)
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate(node.operand))
    raise ValueError("only numbers and + - * / ** are allowed")


def get_weather(city):
    """Return the (simulated) weather in a city."""
    forecast = WEATHER.get(city.strip().lower())
    if forecast is None:
        known = ", ".join(WEATHER)
        return f"No weather for {city!r}. Known: {known}."
    return f"Weather in {city}: {forecast}."
```

Remarque la fin de `search` et de `get_weather`. Quand la ville est inconnue, elles ne lèvent pas d'exception : elles **renvoient une phrase** qui liste les villes connues. Le modèle la lit et réessaie. Une exception, elle, arrêterait tout.

> ⚠️ **Piège classique** — Ne passe jamais le texte d'un modèle à `eval()`. Le modèle peut écrire `__import__('os').system(...)`. Ici, `calculate` lit l'expression avec le module `ast`, qui la découpe en arbre sans l'exécuter, et `evaluate` parcourt cet arbre en n'acceptant que des nombres et les opérateurs de la liste. Tout le reste lève une erreur, transformée en phrase pour le modèle.

Enfin la seconde face, les descriptions, au format qu'OpenRouter attend (celui d'OpenAI) :

<!-- code: tools.py 75-105 -->
```python
# Catalogue: the name the model says -> the Python function to run.
TOOLS = {"search": search, "calculate": calculate,
         "get_weather": get_weather}


def schema(name, description, parameter, parameter_description):
    """One tool description, in the dialect OpenRouter speaks."""
    return {"type": "function", "function": {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {parameter: {
                "type": "string",
                "description": parameter_description}},
            "required": [parameter],
        },
    }}


TOOL_SCHEMAS = [
    schema("search", "Find facts about a city: population, "
           "country, time zone. Use it before answering about a "
           "place.",
           "query", "The city to look up, for example 'Tokyo'."),
    schema("calculate", "Evaluate an arithmetic expression. Never "
           "calculate in your head: use this tool.",
           "expression", "A formula such as '14 * 3 + 2'."),
    schema("get_weather", "Get the current weather in a city.",
           "city", "The city name, for example 'Lisbon'."),
]
```

`TOOLS` relie le nom que le modèle prononce à la fonction que ton code lance. `schema` évite de réécrire trois fois les mêmes accolades. Et dans `TOOL_SCHEMAS`, le champ `description` est celui qui compte. Un modèle choisit un outil comme tu choisis un tiroir : à l'étiquette. Retiens une règle d'écriture : une description dit **quand** utiliser l'outil, pas seulement ce qu'il fait. « Calculatrice » ne dit rien. « Ne calcule jamais de tête : utilise cet outil » donne au modèle un déclencheur. C'est de la rédaction, pas du code, et c'est là que se gagnent la moitié des bugs d'agent.

Les arguments, eux, arrivent en **chaîne de JSON**, pas en dictionnaire. Ton code doit appeler `json.loads()`, et se méfier : c'est un modèle qui l'a écrit, le JSON peut être cassé.

## La boucle ReAct : raisonner, agir, observer

Voici le cœur du chapitre. Pense à un enquêteur dans un film : il observe la scène, formule une hypothèse, va interroger un témoin, revient avec une nouvelle pièce, et recommence jusqu'à pouvoir nommer le coupable. Il ne devine pas depuis son fauteuil. **ReAct** (de *Reason* et *Act*) donne ce même rythme à ton agent, en trois temps :

- **Reason** — le modèle lit la conversation et décide : répondre, ou utiliser un outil ;
- **Act** — ton code exécute l'outil demandé ;
- **Observe** — le résultat est ajouté à la conversation, et le cycle repart.

Le cycle s'arrête quand le modèle répond sans demander d'outil.

Une précision, parce que le schéma d'origine de ReAct l'écrit autrement. Dans l'article de recherche, le modèle *écrit* sa réflexion en toutes lettres (« Thought : je dois connaître la météo... »). Avec le function calling, ce raisonnement reste le plus souvent interne : tu ne vois que la décision, c'est-à-dire l'outil choisi. Le Reason existe toujours, il est simplement moins bavard. Les lignes `ACT` et `OBSERVE` du mode `verbose` te montrent le reste du cycle.

Voici `agent.py`. Le début du fichier pose les règles et construit l'agent :

<!-- code: agent.py 1-33 -->
```python
"""myTravel v1: a model, tools, a loop. No framework.

Everything is written by hand so you can see the loop that
frameworks hide in the next chapters.
"""

import json

from modele import MODEL, get_client
from tools import TOOL_SCHEMAS, TOOLS

SYSTEM_PROMPT = """You are myTravel, a travel assistant.
You have tools. Rules:
- Never guess a fact a tool can give you.
- Never calculate in your head: call `calculate`.
- When you have what you need, answer in one or two sentences."""


class Agent:
    """A model + tools + a loop + a turn limit + a memory."""

    def __init__(self, client=None, model=MODEL, max_turns=6,
                 verbose=False):
        # A fake client can be injected: tests run without a key.
        self.client = client or get_client()
        self.model = model
        # Without a limit, a lost agent loops (and bills) forever.
        self.max_turns = max_turns
        self.verbose = verbose
        # The memory IS this list: the model only knows its content.
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
```

Le message `system` est le **prompt système** : les règles de l'agent, placées en tête de la conversation. Deux détails dans `__init__`. Le `client` peut être remplacé par une doublure : c'est ce qui permet de tester sans clé. Et `max_turns` coupe la boucle : sans cette limite, un agent perdu tourne toute la nuit et te présente la facture au matin.

Voici maintenant la boucle elle-même :

<!-- code: agent.py 35-66 -->
```python
    def chat(self, question):
        """Ask a question; the conversation is kept for the next."""
        self.messages.append({"role": "user", "content": question})

        for turn in range(1, self.max_turns + 1):
            # REASON: the model reads it all and decides.
            reply = self.client.chat.completions.create(
                model=self.model,
                tools=TOOL_SCHEMAS,
                messages=self.messages,
            ).choices[0].message
            message = reply.model_dump(exclude_none=True)
            self.messages.append(message)

            # No tool requested: this is the final answer. We stop.
            if not reply.tool_calls:
                return reply.content or ""

            for call in reply.tool_calls:
                name = call.function.name
                args = call.function.arguments
                # ACT: our code runs the tool, not the model.
                result = self._run_tool(name, args)
                self._log(turn, name, args, result)
                # OBSERVE: the result goes back in the conversation.
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })

        return f"Stopped after {self.max_turns} turns, no answer."
```

Chaque tour envoie **toute** la conversation au modèle, avec la liste des outils. Sa réponse est ajoutée à la liste : sans cela, il oublierait qu'il vient de demander un outil. S'il n'y a pas de `tool_calls`, c'est fini. Sinon, chaque outil demandé est exécuté, et son résultat repart dans un message de rôle `tool`. Ce message porte un `tool_call_id` : il dit à quelle demande il répond. Un modèle peut demander deux outils d'un coup, et il doit savoir quel résultat va avec quelle demande.

Reste `_run_tool`, qui exécute l'outil sans jamais planter, et `_log`, qui affiche les étapes en mode `verbose` :

<!-- code: agent.py 68-84 -->
```python
    def _run_tool(self, name, arguments_json):
        """Run a tool. Always returns text, even on error."""
        if name not in TOOLS:
            return f"Error: tool {name!r} does not exist."
        try:
            # Arguments arrive as JSON text written by a model:
            # it may be broken.
            arguments = json.loads(arguments_json or "{}")
            return str(TOOLS[name](**arguments))
        except Exception as error:  # noqa: BLE001
            # The error goes back to the model, which can adapt.
            return f"Error while running {name}: {error}"

    def _log(self, turn, name, arguments, result):
        if self.verbose:
            print(f"  [turn {turn}] ACT     {name}({arguments})")
            print(f"  [turn {turn}] OBSERVE {result}")
```

Même principe que pour `search` : une erreur est un **texte** rendu au modèle. Il a inventé un outil qui n'existe pas ? Il l'apprend et se corrige au tour suivant. Une `except Exception` si large choque d'habitude. Ici c'est voulu : tout ce qui sort de l'outil doit devenir une observation, quel que soit le plantage.

> 💡 **À retenir** — La boucle ReAct tient en trois gestes : envoyer la conversation, exécuter les outils demandés, renvoyer leurs résultats. Tout framework de ce livre n'est qu'une manière plus confortable d'écrire ces trois gestes.

> ⚠️ **Piège classique** — Oublier d'ajouter la réponse du modèle à `self.messages` avant de renvoyer le résultat de l'outil. L'API refuse alors le message `tool` : il répond à une demande qu'elle ne retrouve pas dans la conversation.

## La prise : `modele.py`

`agent.py` importe deux choses de `modele.py` : le nom du modèle et `get_client`. C'est la seule porte vers un modèle dans tout le livre, et la voici une fois pour toutes. Les chapitres suivants en gardent une copie dans leur dossier.

<!-- code: modele.py -->
```python
"""The only door to a model in this book: OpenRouter.

OpenRouter speaks the OpenAI dialect: the `openai` SDK works as is,
only the base URL changes. The model is a slug read from MODELE.

    python modele.py    # free models that can call tools today
"""

import json
import os
import urllib.request

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # climbs up to the .env at the repository root

BASE_URL = "https://openrouter.ai/api/v1"
# Free (":free" costs nothing) and able to call tools.
DEFAULT_MODEL = "google/gemma-4-31b-it:free"
MODEL = os.environ.get("MODELE", DEFAULT_MODEL)
# When free quotas run out: a few cents for the whole book.
CHEAP_MODELS = ["deepseek/deepseek-v4-flash",
                "google/gemini-3.1-flash-lite"]


def get_client():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing: copy "
                         ".env.example to .env and paste your key.")
    # Free models often answer 429 "busy": retry, waiting longer.
    return OpenAI(base_url=BASE_URL, api_key=key, max_retries=6)


def make_ask(client, model=MODEL):
    """A function messages -> text: the model, without the SDK."""
    def ask(messages):
        response = client.chat.completions.create(
            model=model, messages=messages)
        return response.choices[0].message.content or ""
    return ask


def free_models_with_tools():
    """Read the public catalogue: no key needed."""
    request = urllib.request.Request(
        f"{BASE_URL}/models", headers={"User-Agent": "mytravel"})
    with urllib.request.urlopen(request, timeout=15) as response:
        catalogue = json.load(response)["data"]
    return sorted(
        m["id"] for m in catalogue
        if m["id"].endswith(":free")
        and "tools" in (m.get("supported_parameters") or []))


if __name__ == "__main__":
    print(f"Model in use: {MODEL}")
    print("Free models that can call tools today:")
    for slug in free_models_with_tools():
        print(" ", slug)
    print("Cheap fallback:", ", ".join(CHEAP_MODELS))
```

Tout appel de modèle passe par **OpenRouter**, un service qui donne accès à des centaines de modèles avec une seule clé. Il parle le même dialecte que l'API d'OpenAI : on utilise donc le SDK `openai`, en changeant seulement l'adresse (`BASE_URL`). Changer de modèle devient une ligne du `.env`.

Le modèle par défaut finit par `:free` : il ne coûte rien. OpenRouter demande une carte à l'inscription, pour écarter les robots, mais ne prélève rien tant que tu restes sur un slug `:free`. En échange, les quotas gratuits sont bas : quelques dizaines de requêtes par jour, et un agent en consomme plusieurs par question. `CHEAP_MODELS` donne la sortie de secours, quelques centimes pour tout le livre. `max_retries=6` demande au SDK de réessayer quand un modèle gratuit répond « occupé » (code 429). `make_ask` servira à partir du chapitre 7. Et `python modele.py` interroge le catalogue public pour lister les modèles gratuits **capables d'appeler des outils** : sans cette capacité, aucun agent ne tourne.

## La fenêtre de contexte : ce que le modèle voit

Voici un fait qui surprend tout le monde : le modèle n'a aucune mémoire entre deux appels. À chaque tour, il relit **toute** la liste `messages` depuis le début, comme un poisson rouge à qui on réciterait l'histoire depuis la première ligne avant de lui poser la question suivante. Ce qu'il « sait », c'est ce qui s'y trouve. Rien d'autre.

Cette liste a une taille maximale, la **fenêtre de contexte**. Elle se mesure en **tokens** : des fragments de mots, environ quatre caractères en anglais. Un mot courant vaut un token, un mot rare en vaut trois ou quatre. Au-delà de la limite, la requête échoue, ou les plus vieux messages disparaissent sans prévenir. Dans les deux cas, ton agent oublie.

Les modèles gratuits de ce livre ont des fenêtres de plusieurs centaines de milliers de tokens : tu n'atteindras pas la limite avec trois questions. Mais chaque token coûte du temps et, sur un modèle payant, de l'argent : on te facture toute la liste à chaque tour, pas seulement le dernier message. Et une longue conversation noie les informations utiles. Apprends à couper proprement dès maintenant, avec `memory.py` :

<!-- code: memory.py -->
```python
"""Keeping the conversation inside the context window.

The model reads the WHOLE message list at every turn, and that
list has a size limit (the context window). Past it, the request
fails or old messages are silently dropped. Here we cut on
purpose, cleanly.
"""


def estimate_tokens(messages):
    """Rough size of the conversation, in tokens.

    A token is a chunk of a word: about four characters in
    English. An estimate is enough to decide when to trim.
    """
    chars = sum(len(str(m.get("content") or "")) for m in messages)
    return chars // 4


def trim_messages(messages, max_messages):
    """Keep the system prompt and the most recent messages.

    The cut always lands on a `user` message. Cutting between a
    tool request and its result leaves an orphan `tool` message,
    and the API rejects it.
    """
    if len(messages) <= max_messages:
        return messages

    system, rest = messages[0], messages[1:]
    start = len(rest) - (max_messages - 1)
    # Move the cut forward to the next user message.
    while start < len(rest) and rest[start]["role"] != "user":
        start += 1
    return [system, *rest[start:]]
```

`estimate_tokens` donne une estimation grossière, qui suffit pour décider quand couper. `trim_messages` garde toujours le prompt système, puis les messages les plus récents. Le `while` est la ligne qui évite un bug vicieux : si la coupe tombe entre une demande d'outil et son résultat, le message `tool` reste orphelin et l'API le rejette. On avance donc la coupe jusqu'au prochain message `user`.

> ⚠️ **Piège classique** — Couper « les 20 derniers messages » sans regarder leur rôle. Si la coupe tombe en plein milieu d'un échange d'outil, l'erreur de l'API ne dit pas pourquoi. Coupe sur une frontière de question.

## La mémoire conversationnelle : une liste, rien de plus

Il n'y a pas de base de données, pas de magie. La mémoire d'un agent simple, c'est la liste `self.messages`, qui grossit à chaque question et à chaque outil.

Regarde `main.py`, le dernier fichier : un seul `Agent` pour toute la conversation.

<!-- code: main.py -->
```python
"""Run chapter 1:  python main.py

Needs OPENROUTER_API_KEY in the .env file at the repository root.
"""

import sys

from openai import RateLimitError

from agent import Agent
from memory import estimate_tokens, trim_messages

# One conversation, three questions. The second only makes sense
# thanks to the memory: "there" is the city of the first question.
QUESTIONS = [
    "How many people live in Tokyo?",
    "What is the weather there, and what do 3 nights at 120 euros "
    "cost?",
    "And the weather in Lisbon?",
]


def main():
    # One agent for the whole conversation: it keeps its memory.
    agent = Agent(verbose=True)
    for question in QUESTIONS:
        print(f"\n> {question}")
        print(f"< {agent.chat(question)}")
        # Keep the context window under control between questions.
        agent.messages = trim_messages(agent.messages, 20)
        tokens = estimate_tokens(agent.messages)
        print(f"  (about {tokens} tokens in context)")


if __name__ == "__main__":
    try:
        main()
    except RateLimitError:
        # Free quotas are shared by everyone: it is not your code.
        sys.exit("The model is saturated (429). Wait a minute, or "
                 "change MODELE in .env (python modele.py).")
```

Crée un `Agent` neuf à chaque question, et tu perds tout : la seconde question (« la météo *là-bas* ? ») n'aurait plus de sens. Garde le même, et le « there » se résout tout seul. Entre deux questions, `trim_messages` garde la liste dans des limites raisonnables. Et si le modèle gratuit est saturé, le message du `except` dit quoi faire au lieu d'afficher trente lignes de trace.

Un détail utile pour la suite : le prompt système n'est pas un message comme les autres. Il reste en tête de liste à chaque tour, et `trim_messages` le protège. Si tu le laisses partir avec les vieux messages, l'agent perd ses règles en pleine conversation et se met à calculer de tête.

Cette mémoire a deux limites que tu connais déjà. Elle disparaît quand le programme s'arrête. Et elle grossit jusqu'à la fenêtre de contexte. Les chapitres suivants s'occupent des deux.

## Ce que cette approche ne sait pas faire

Ton agent tourne, Inès a son budget, tout le monde est content. Profites-en une minute, parce que la suite du livre existe à cause de ce qui va mal ensuite.

**Les outils s'écrivent deux fois.** La fonction Python, puis son schéma JSON, à la main. Oublie de resynchroniser l'un des deux, et le modèle appelle une fonction avec un argument qui n'existe plus. Au chapitre 2, LangChain lit la signature et fabrique le schéma pour toi.

**La mémoire est fragile.** Elle vit dans une variable. Ferme le terminal, et Inès doit tout réexpliquer demain.

**La boucle est une ligne droite.** Le modèle, les outils, le modèle : un cercle, rien d'autre. Le jour où tu veux « rédige, fais critiquer, puis réécris », ou « demande confirmation avant d'agir », tu empiles des `if` dans le `for`, et ton code ressemble vite à un plat de spaghettis. Le chapitre 3 (LangGraph) dessine ces chemins au lieu de les enfouir.

**Un seul agent.** Pour plusieurs agents spécialisés qui se passent le travail, il faut une orchestration. Rendez-vous au chapitre 4 (CrewAI).

Un dernier détail, appris à mes dépens sous Windows : le « 18 °C » de la météo s'affichait « 18�C » dans mon terminal. Les outils renvoyaient du texte correct, c'est la console qui n'était pas en UTF-8. `set PYTHONUTF8=1` règle le problème. Moralité : quand un agent se comporte bizarrement, le coupable est souvent très loin du modèle.

## QCM

**1.** Quels éléments composent un agent IA ?

- **a)** Un modèle de langage
- **b)** Une boucle de décision
- **c)** Une base de données vectorielle
- **d)** Des outils

**2.** Dans la boucle de l'agent, qui exécute réellement l'outil ?

- **a)** Ton code Python
- **b)** Le prompt système
- **c)** OpenRouter, côté serveur
- **d)** Le modèle, directement

**3.** Que lit le modèle pour savoir se servir d'un outil ?

- **a)** Le code source de la fonction
- **b)** Son nom
- **c)** Sa description en texte
- **d)** Ses paramètres

**4.** Dans la boucle ReAct, que fait ton code (et non le modèle) ?

- **a)** Il choisit l'outil à appeler
- **b)** Il renvoie le résultat dans la conversation
- **c)** Il rédige la réponse finale
- **d)** Il lance la fonction demandée

**5.** L'agent répond « Stopped after 6 turns, no answer. » Quelles pistes sont pertinentes ?

- **a)** Lire les messages `tool`
- **b)** Changer la version de Python
- **c)** Relancer avec `verbose=True`
- **d)** Chercher un outil inconnu ou des arguments faux

**6.** Un outil lève une exception. Que faut-il faire ?

- **a)** L'ignorer en silence
- **b)** Rendre ce texte au modèle pour qu'il corrige son appel
- **c)** La transformer en texte
- **d)** La laisser planter le programme

**7.** Tu crées un `Agent` neuf à chaque question. Qu'observes-tu ?

- **a)** Le quota gratuit est épuisé
- **b)** « La météo là-bas ? » devient incompréhensible
- **c)** Le modèle ne se souvient de rien
- **d)** La liste de messages repart de zéro

**Réponses.** Q1 : a, b, d · Q2 : a · Q3 : b, c, d · Q4 : b, d · Q5 : a, c, d · Q6 : b, c · Q7 : b, c, d

## Ce qu'il faut retenir
1. Un agent IA, c'est un LLM, des outils et une boucle de décision. Le modèle décide, ton code exécute.
2. Un outil a deux faces : une fonction Python que ton code lance, et une description JSON que le modèle lit. La description est son seul mode d'emploi.
3. La boucle ReAct enchaîne Reason (le modèle choisit), Act (ton code lance l'outil) et Observe (le résultat revient dans la conversation), jusqu'à une réponse sans outil.
4. Le modèle ne se souvient de rien : il relit toute la liste de messages à chaque tour. La mémoire simple est cette liste, bornée par la fenêtre de contexte.
5. Une limite de tours et des erreurs rendues en texte rendent l'agent robuste.

**Au chapitre suivant :** ton agent marche, mais chaque outil existe en double : une fonction, puis un schéma écrit à la main. Et la boucle, c'est toi qui la maintiens. LangChain fait les deux : il lit ta fonction pour fabriquer le schéma, et fournit la boucle toute faite. Même agent, une vingtaine de lignes.

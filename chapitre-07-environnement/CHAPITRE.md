# Chapitre 7 — L'environnement : une API, une page, une réponse en direct

> **Dossier GitHub associé :** `chapitre-07-environnement/`

**À la fin de ce chapitre, tu sauras :**

- expliquer ce que sont un serveur, une API, une requête HTTP et du JSON ;
- écrire une API avec FastAPI, qui valide toute seule ce qu'elle reçoit ;
- envoyer la réponse du modèle **mot à mot**, au moment où il l'écrit, avec les *Server-Sent Events* ;
- lire ce flux dans la page avec `fetch` ;
- brancher LangChain sur OpenRouter en une fonction ;
- transformer une panne du modèle en message clair au lieu d'un plantage.

## « Tu peux me l'envoyer ? »

Les parties précédentes tournaient dans un terminal. Tu tapais `python main.py`, l'agent répondait, et c'était très bien pour apprendre. Puis un jour, quelqu'un te demande : « C'est génial, tu peux me l'envoyer ? »

Et là, tu mesures le problème. Ta sœur n'a pas Python. Ton collègue n'a pas envie de créer un environnement virtuel. Ton client veut cliquer sur un lien.

Un vrai assistant de voyage vit là où vivent les voyageurs : dans un navigateur. Ce chapitre pose ce socle. Une page web, une API derrière, un modèle au bout. Pas encore d'outils, pas encore de mémoire. Juste un chemin complet, du clavier au modèle et retour, qui marche, et qui répond **en direct**.

## Client, serveur, API : le vocabulaire en deux minutes

Quand tu ouvres une page web, ton navigateur est le **client** : il demande. Le programme qui répond est le **serveur**. Ils se parlent en **HTTP**, un protocole fait de requêtes courtes : « GET / » veut dire « donne-moi la page d'accueil », « POST /api/chat » veut dire « voici des données, traite-les ».

Une **API** (*Application Programming Interface*), c'est un ensemble de ces adresses prévues pour des programmes plutôt que pour des humains. Elles échangent du **JSON**, un format texte qui ressemble à un dictionnaire Python.

Pour écrire l'API, myTravel utilise **FastAPI**. Trois raisons : on déclare une route avec un simple décorateur, la forme des données reçues se décrit avec une classe Pydantic et FastAPI refuse tout seul ce qui ne colle pas, et une documentation interactive est générée gratuitement à l'adresse `/docs`. Pour faire tourner l'application, on utilise **uvicorn**, le serveur qui écoute le réseau et passe chaque requête à FastAPI.

Pour la page, pas de React ni d'outil de construction : une seule page HTML, avec son CSS et un peu de JavaScript. Tu peux la lire d'un bout à l'autre, et c'est le but.

> 💡 **À retenir** — La page ne parle jamais au modèle. Elle parle à **ton** serveur, qui seul connaît la clé d'API. Une clé dans du JavaScript est une clé publiée : n'importe qui la lit avec F12.

## Vingt secondes devant une page blanche

Un modèle met souvent dix à vingt secondes pour écrire une réponse complète. Plus tard, quand cinq agents travailleront pour toi, ce sera une minute. Si la page attend la fin pour afficher quoi que ce soit, le voyageur fixe trois petits points, se demande si ça a planté, et recharge. Sa question part une deuxième fois. Toi, tu paies deux fois.

Le modèle, lui, n'écrit pas tout d'un coup : il produit sa réponse morceau par morceau (un **token**, c'est-à-dire un bout de mot). Autant les montrer à mesure qu'ils arrivent. C'est le **streaming** : la réponse coule dans la page comme dans ChatGPT.

Pour ça, le serveur ne renvoie pas un JSON unique à la fin. Il garde la connexion ouverte et envoie des **événements**, l'un après l'autre. Le format le plus simple pour ça s'appelle **SSE** (*Server-Sent Events*) : du texte, une ligne `data:` par événement, une ligne vide après chacun.

```text
POST /api/chat
{"message": "Visa pour le Japon ?"}

data: {"type": "token", "text": "Pour un séjour"}

data: {"type": "token", "text": " de moins de 90 jours…"}

data: {"type": "done", "answer": "Pour un séjour de…"}
```

myTravel n'aura jamais besoin que de quatre types d'événements. On les fixe dès maintenant, et ils ne changeront plus jusqu'au chapitre 20 :

| Type | Sens | Arrive à partir du |
|---|---|---|
| `token` | un morceau de réponse | chapitre 7 |
| `done` | la réponse entière, et la fin du flux | chapitre 7 |
| `error` | une panne survenue en cours de route | chapitre 7 |
| `step` | une étape démarre : un outil, puis un agent | chapitre 9 |

Pourquoi pas les **WebSockets**, qu'on cite souvent pour le temps réel ? Ils servent quand les deux côtés parlent en même temps, comme dans un jeu en ligne. Ici, le voyageur envoie une question et le serveur répond : un seul sens suffit, et SSE n'est que du HTTP ordinaire.

> 💡 **À retenir** — Le modèle ne va pas plus vite. Mais le premier mot s'affiche au bout d'une seconde au lieu de vingt : l'attente devient visible, et on attend volontiers ce qu'on voit venir.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

```text
chapitre-07-environnement/mytravel/
├── server.py          ← l'API : 3 routes, et le flux SSE
├── static/index.html  ← la page de chat, qui lit le flux
├── app/
│   ├── chat.py        ← un message, les tokens du modèle
│   └── modele.py      ← la prise OpenRouter
├── conftest.py        ← une fausse clé pour les tests
└── tests/             ← 6 tests, sans clé ni réseau
```

| Fichier | Rôle |
|---|---|
| `server.py` | sert la page (`/`), répond à `/api/chat` en flux, dit s'il est vivant (`/health`) |
| `static/index.html` | affiche les bulles, envoie la question, écrit la réponse à mesure qu'elle arrive |
| `app/chat.py` | construit les messages et transmet chaque morceau écrit par le modèle |
| `app/modele.py` | crée le modèle LangChain branché sur OpenRouter |

### Lancer le chapitre

L'environnement est installé une fois pour tout le livre, à la racine (voir le chapitre 6). Ensuite :

```bash
cd chapitre-07-environnement/mytravel
python -m app.modele      # ta clé marche ? modèles gratuits ?
uvicorn server:app --reload
pytest                    # 6 passed
```

Ouvre http://localhost:8000 et pose une question, n'importe laquelle. Regarde la réponse s'écrire mot après mot. myTravel répond, mais remarque qu'il répond *de mémoire* : demande-lui la météo de demain à Lisbonne, il te dira qu'il ne peut pas savoir, ou pire, il inventera. C'est normal, il n'a encore aucun outil.

Puis ouvre http://localhost:8000/docs. C'est la documentation que FastAPI fabrique tout seul. Clique sur `POST /api/chat`, puis *Try it out*, envoie `{"message": ""}` : FastAPI répond 422, « le texte doit faire au moins un caractère ». Tu n'as écrit aucune ligne pour ça.

### À toi d'abord

Avant de lire la suite, ouvre `server.py` et `static/index.html`. Cherche dans la page le mot `fetch` : c'est l'endroit où le navigateur appelle le serveur. Puis trouve dans `server.py` la fonction qui reçoit cet appel, et celle qui écrit les lignes `data:`. Si tu fais le lien entre les trois, tu as compris l'essentiel du chapitre.

## On lit le code ensemble

### `server.py` : je commence par la porte

Comme dans « Lire du code comme un pro », je commence par le fichier que la commande de lancement nomme : `server:app`. J'y cherche `app`, puis les décorateurs `@app.` : ce sont les routes, la liste de tout ce que le serveur sait faire.

<!-- code: mytravel/server.py 21-40 -->
```python
app = FastAPI(title="myTravel")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


@app.get("/")
def page():
    return FileResponse(PAGE)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(body: ChatRequest):
    return live(stream_mytravel(body.message))
```

`ChatRequest` est le contrat de la route : un champ `message`, du texte, entre 1 et 2 000 caractères. Je me demande toujours pourquoi une limite haute existe. Ici, c'est simple : sans elle, quelqu'un pourrait envoyer un roman, et c'est toi qui paierais les tokens. Le contrôle coûte une ligne. Le paramètre `body: ChatRequest` fait tout le travail de lecture : FastAPI lit le JSON, vérifie qu'il colle au contrat, et te donne un objet. Si ça ne colle pas, ta fonction n'est même pas appelée.

`/health` paraît inutile. Il ne l'est pas : au chapitre 18, Google Cloud Run l'appellera pour savoir si ton application est vivante.

La route `/api/chat` tient en une ligne : elle passe les événements de `stream_mytravel` à `live`. Je descends donc lire `live` :

<!-- code: mytravel/server.py 43-57 -->
```python
def live(events):
    """Each event sent as soon as it comes: a Server-Sent Event."""
    def lines():
        try:
            for event in events:
                yield sse(event)
        except Exception as error:  # the stream has started
            yield sse(failure(error))
    return StreamingResponse(lines(),
                             media_type="text/event-stream")


def sse(event):
    """One event: a "data:" line, then a blank line."""
    return f"data: {json.dumps(event)}\n\n"
```

`StreamingResponse` est la réponse de FastAPI qui n'attend pas la fin : elle prend un **générateur** (une fonction avec `yield`) et envoie au navigateur chaque morceau qu'il produit, dès qu'il le produit. `sse` met un événement au format SSE : `data:`, le JSON, une ligne vide. Et `media_type="text/event-stream"` prévient le navigateur qu'il reçoit un flux, pas une page.

Reste le `try`. Le premier octet est déjà parti quand le modèle tombe en panne : trop tard pour répondre « erreur 503 », le code HTTP 200 a été envoyé. La panne devient donc un événement de plus, que `failure` prépare :

<!-- code: mytravel/server.py 60-74 -->
```python
def failure(error):
    """Too late for an HTTP error: the error is one more event."""
    if isinstance(error, RateLimitError):
        # Free quotas are shared by everyone: it is not your code.
        return {"type": "error", "detail": "Le modèle gratuit est "
                "saturé : réessaie dans une minute."}
    if isinstance(error, APIError):
        # The details stay in the server's terminal: they can
        # carry pieces of a key or of a prompt.
        print(f"Model error: {error}")
        return {"type": "error", "detail": "Erreur du modèle : "
                "regarde le terminal du serveur."}
    print(f"Server error: {error!r}")  # a bug
    return {"type": "error", "detail": "Erreur inattendue : "
            "regarde le terminal du serveur."}
```

Deux pannes *vont* arriver. `RateLimitError`, c'est l'erreur 429 : le modèle gratuit est saturé, partagé par des milliers de gens. `APIError` couvre le reste, dont la clé expirée. Dans les deux cas, je renvoie un message qu'un humain comprend. Le détail de l'erreur reste dans le terminal : il peut contenir un morceau de ta clé, et la page n'a pas à le voir. Le dernier cas, ce sont nos propres bugs : la page reçoit quand même un événement qu'elle sait afficher.

> ⚠️ **Piège classique** — Laisser remonter l'exception brute dans un flux. Le navigateur voit la connexion se couper au milieu d'une phrase, la page reste figée, et tu cherches pendant une heure un bug qui n'est qu'un quota épuisé.

### `app/chat.py` : le plus petit agent possible

Je suis le fil : `stream_mytravel` vient de `app.chat`.

<!-- code: mytravel/app/chat.py -->
```python
"""myTravel's first answer: one message in, words out.

No memory yet, no tools yet: the point is to prove the whole
chain works, page -> server -> OpenRouter -> model -> page,
and that the answer shows word by word, as the model writes it.
"""

from app.modele import get_chat_model

PROMPT = """You are myTravel, a travel assistant. You find and
compare offers; the traveler books and pays on the provider's
website. Answer in the traveler's language, in a few lines."""


def stream_mytravel(message):
    """Each piece of the answer as soon as the model writes it."""
    answer = ""
    for chunk in get_chat_model().stream(
            [("system", PROMPT), ("user", message)]):
        if chunk.content:  # some chunks carry no text
            answer += chunk.content
            yield {"type": "token", "text": chunk.content}
    yield {"type": "done", "answer": answer}
```

Deux messages : le prompt système, qui dit au modèle qui il est, et ta question. `stream` les envoie et rend la réponse en morceaux, au lieu de `invoke` qui attend la fin. Chaque morceau part tout de suite en événement `token`. Le `if` saute les morceaux vides : certains modèles en envoient quelques-uns au début et à la fin. À la fin, `done` porte la réponse entière : c'est elle que la page gardera.

Pourquoi le prompt est-il en anglais alors que myTravel répond en français ? Les modèles suivent un peu mieux les consignes en anglais, et la dernière phrase leur demande de répondre dans la langue du voyageur. Essaie de lui écrire en espagnol.

### `app/modele.py` : la seule porte vers un modèle

<!-- code: mytravel/app/modele.py 19-40 -->
```python
BASE_URL = "https://openrouter.ai/api/v1"
# Free (":free" costs nothing) and able to call tools.
DEFAULT_MODEL = "google/gemma-4-31b-it:free"
MODEL = os.environ.get("MODELE", DEFAULT_MODEL)
# If a model is busy, OpenRouter tries the next one by itself.
# Not "openrouter/free": it may pick a model that only grades
# messages and answers "User Safety: safe".
FREE_BACKUPS = ["google/gemma-4-26b-a4b-it:free",
                "nvidia/nemotron-3-ultra-550b-a55b:free"]


def get_chat_model(model=MODEL):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is missing: copy "
                           ".env.example to .env, paste your key.")
    # "models": OpenRouter's own fallback list, tried in order
    # when a model answers 429 "busy". Then we retry twice.
    backups = [name for name in FREE_BACKUPS if name != model]
    return ChatOpenAI(model=model, base_url=BASE_URL, api_key=key,
                      temperature=0, max_retries=2,
                      extra_body={"models": [model, *backups]})
```

Tu reconnais le principe du chapitre 2 : `ChatOpenAI` parle le dialecte d'OpenAI, et OpenRouter aussi. On change seulement l'adresse (`base_url`). Résultat : changer de modèle, c'est une ligne `MODELE=...` dans `.env`, sans toucher au code.

Trois réglages méritent une phrase. `temperature=0` rend le modèle plus constant : un assistant de voyage n'a pas à être créatif sur un numéro de vol. `extra_body={"models": [...]}` donne à OpenRouter une liste de secours : si le modèle gratuit répond « occupé » (erreur 429), OpenRouter passe tout seul au suivant, dans la même requête. `FREE_BACKUPS` en nomme deux, gratuits eux aussi. Pas `openrouter/free`, ce routeur qui choisit seul un modèle gratuit libre : il m'a un jour répondu « User Safety: safe » et rien d'autre. Il était tombé sur un modèle qui ne répond pas, il classe les messages. Et `max_retries=2` relance deux fois toute la liste, en attendant un peu plus à chaque fois. L'événement `error` « saturé » n'arrive que si tout le monde est saturé.

### `static/index.html` : lire un flux, et le seul vrai danger

Le JavaScript tient en trois fonctions. La première découpe le flux en événements :

<!-- code: mytravel/static/index.html 159-175 -->
```html
// The server sends "data: {...}" blocks, a blank line after
// each, as they come: read them one by one, as they arrive.
async function* events(response) {
  const reader = response.body
    .pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const {value, done} = await reader.read();
    if (done) return;
    buffer += value;
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop();  // the last one may be cut in half
    for (const block of blocks) {
      yield JSON.parse(block.slice("data: ".length));
    }
  }
}
```

`fetch` est l'appel HTTP du navigateur. `response.body` est le flux brut, que `TextDecoderStream` transforme en texte. Un morceau reçu du réseau ne tombe pas forcément pile sur la fin d'un événement : on garde le dernier bloc, peut-être coupé en deux, pour le compléter au tour suivant. `async function*` en fait un générateur : la page lit les événements avec un simple `for await`.

Pourquoi pas `EventSource`, l'objet que les navigateurs offrent pour SSE ? Il ne sait faire que des `GET`, et notre question part en `POST`, avec du JSON.

La deuxième fonction envoie la question et range chaque événement :

<!-- code: mytravel/static/index.html 189-209 -->
```html
    if (!response.ok) {  // refused before the stream started
      const reply = await response.json().catch(() => ({}));
      throw new Error(reply.detail);
    }
    for await (const event of events(response)) {
      if (event.type === "step") {
        const pill = document.createElement("span");
        pill.className = "chip step";
        pill.textContent = event.text;
        started.appendChild(pill);
      } else if (event.type === "token") {
        draft ??= bubble("bot", "");
        // Plain text while it comes: Markdown once it is done.
        draft.textContent += event.text;
        chat.scrollTop = chat.scrollHeight;
      } else if (event.type === "error") {
        throw new Error(event.detail);
      } else if (event.type === "done") {
        show(event);  // the whole answer replaces the draft
      }
    }
```

Si le serveur refuse la question avant de commencer (422, par exemple), `response.ok` est faux et on affiche son message. Sinon, chaque `token` s'ajoute au brouillon, en texte brut. Le `done` remplace ce brouillon par la réponse entière, mise en forme. Le drapeau `busy`, plus haut, interdit une deuxième question tant que la première n'a pas sa réponse : sinon la touche Entrée pendant l'attente enverrait deux fois la question, et deux fois la facture. Les `step` ne servent pas encore : ils arriveront au chapitre 9 avec les outils.

Pourquoi un brouillon en texte brut, et pas le Markdown tout de suite ? La troisième fonction, celle qui met la réponse en forme, répond :

<!-- code: mytravel/static/index.html 127-144 -->
```html
// Add a bubble. Model text is Markdown: render it, then clean it,
// because a web page could have slipped HTML into the answer.
function bubble(who, text) {
  const div = document.createElement("div");
  div.className = "bubble " + who;
  if (who === "bot") {
    div.innerHTML = DOMPurify.sanitize(marked.parse(text));
    // A new tab per link: the conversation stays on screen.
    for (const link of div.querySelectorAll("a")) {
      link.target = "_blank";
    }
  } else {
    div.textContent = text;
  }
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}
```

Le modèle écrit en Markdown (titres, listes, gras). `marked` le transforme en HTML. Et là, attention : dès le chapitre 9, la réponse contiendra des morceaux de pages web. Si l'une d'elles cache une balise `<script>`, l'insérer telle quelle dans la page l'exécuterait dans le navigateur du voyageur. `DOMPurify.sanitize` retire tout ce qui peut s'exécuter. Pour le brouillon, `textContent` suffit : le texte reste du texte, quoi qu'il contienne. Enfin, `target = "_blank"` ouvre chaque lien dans un nouvel onglet : le voyageur consulte une source sans perdre sa conversation.

> ⚠️ **Piège classique** — Écrire `div.innerHTML = reply.answer` parce que « c'est mon modèle, il ne m'attaquera pas ». Ton modèle, non. Les pages qu'il lit, si. Cette faille s'appelle XSS (*cross-site scripting*), et c'est l'une des plus répandues du web.

Les deux balises `<script>` en haut de la page chargent `marked` et `DOMPurify` depuis cdnjs, avec un attribut `integrity` : une empreinte du fichier attendu. Si quelqu'un modifiait le fichier sur le serveur de cdnjs, le navigateur refuserait de l'exécuter. On y revient au chapitre 15.

## QCM

**1.** Pourquoi la page n'appelle-t-elle pas OpenRouter directement ?

- **a)** Parce que la clé serait lisible par n'importe quel visiteur
- **b)** Parce que le navigateur ne sait pas envoyer de JSON
- **c)** Parce que le serveur doit pouvoir contrôler ce qui part au modèle
- **d)** Parce qu'OpenRouter refuse les navigateurs

**2.** Que fait FastAPI si on envoie `{"message": ""}` à `/api/chat` ?

- **a)** Il appelle le modèle avec un message vide
- **b)** Il répond 422 sans appeler la fonction `chat`
- **c)** Il plante
- **d)** Il applique la règle `min_length=1` de `ChatRequest`

**3.** Qu'apporte le streaming au voyageur ?

- **a)** Un modèle plus rapide
- **b)** Les premiers mots en une seconde au lieu d'attendre la fin
- **c)** Une réponse moins chère
- **d)** La preuve que la page n'a pas planté

**4.** Le modèle tombe en panne au milieu d'une réponse. Que reçoit la page ?

- **a)** Une erreur HTTP 503
- **b)** Un événement `error` avec un message clair
- **c)** Rien : la connexion se coupe
- **d)** Les morceaux déjà écrits, puis l'événement `error`

**5.** Pourquoi le brouillon s'affiche-t-il en texte brut ?

- **a)** Parce que le Markdown est trop lent
- **b)** Parce que `textContent` n'exécute rien de ce qu'il contient
- **c)** Parce que la réponse entière, mise en forme et nettoyée, arrive avec `done`
- **d)** Parce que SSE ne transporte pas le Markdown

**6.** Pourquoi la page lit-elle le flux avec `fetch` plutôt qu'avec `EventSource` ?

- **a)** `EventSource` ne fait que des `GET`, et la question part en `POST`
- **b)** `EventSource` n'existe pas dans les navigateurs
- **c)** `fetch` est plus rapide
- **d)** `EventSource` ne lit pas le JSON

**7.** Où change-t-on de modèle ?

- **a)** Dans `server.py`
- **b)** Dans la ligne `MODELE=` du fichier `.env`
- **c)** Dans `static/index.html`
- **d)** Nulle part, il est fixé par OpenRouter

**Réponses.** Q1 : a, c · Q2 : b, d · Q3 : b, d · Q4 : b, d · Q5 : b, c · Q6 : a · Q7 : b

## Ce qu'il faut retenir

1. Le navigateur (client) demande, le serveur répond, en HTTP et en JSON. Une API est un ensemble d'adresses faites pour des programmes.
2. FastAPI valide les données d'entrée à partir d'une classe Pydantic : ce qui ne colle pas n'atteint jamais ton code.
3. La clé d'API reste sur le serveur. La page ne parle qu'à ton API.
4. La réponse part en flux SSE : `token` à mesure que le modèle écrit, `done` à la fin, `error` si ça casse en route. Un générateur Python et `StreamingResponse` suffisent.
5. Une panne du modèle devient un message clair, et le détail reste dans le terminal.
6. Tout texte venu du modèle est nettoyé avant d'entrer dans la page ; le brouillon reste du texte brut.

**Au chapitre suivant :** demande à myTravel « je pars à Lisbonne », puis « et en mai ? ». Il a déjà oublié Lisbonne. On lui donne une mémoire, et c'est LangGraph qui la garde.

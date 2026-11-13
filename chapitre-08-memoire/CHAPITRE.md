# Chapitre 8 — Mémoire : la conversation

> **Dossier GitHub associé :** `chapitre-08-memoire/`

**À la fin de ce chapitre, tu sauras :**

- expliquer pourquoi un modèle n'a aucune mémoire, et qui en a une à sa place ;
- garder une conversation avec un *checkpointer* LangGraph, rangé dans SQLite ;
- retrouver la bonne conversation grâce à un identifiant envoyé par la page ;
- laisser le modèle retrouver dans la conversation ce que le voyageur a dit de lui (nationalité, ville de départ, budget) ;
- diffuser la réponse d'un agent LangGraph mot à mot, avec `stream_mode="messages"` ;
- tester qu'une conversation ne fuit jamais dans une autre.

## « Et en mai ? »

Lance le chapitre 7 et fais l'essai. Tu écris « Je pars à Lisbonne ». myTravel s'enthousiasme, te parle des tramways jaunes et des pastéis de nata. Tu ajoutes : « Et en mai ? ». Réponse : « En mai, où ça ? »

C'est le poisson rouge. Chaque message arrive seul, sans le précédent, et le modèle répond à une phrase sans contexte. Au chapitre 1, tu avais réglé ça avec une liste Python. Mais une liste vit dans la mémoire du programme : redémarre le serveur, elle disparaît. Et un serveur web parle à cent personnes en même temps : une seule liste mélangerait les cent conversations.

Il faut donc une mémoire **par conversation**, et qui survit à un redémarrage.

## Une mémoire, relue à chaque tour

Le modèle ne se souvient de rien. À chaque appel, il relit ce qu'on lui envoie, et c'est tout. « Mémoire » veut donc dire : ce que **ton code** renvoie au modèle à chaque tour.

Pour myTravel, ce sera **la conversation** : tous les messages, dans l'ordre. LangGraph la garde pour nous avec un **checkpointer** : un objet qui enregistre l'état du graphe après chaque étape, sous un identifiant de conversation (*thread id*). Au message suivant, LangGraph recharge l'état, ajoute ton message, et le modèle relit tout.

Et ce que tu dis de toi ? « Je suis belge », « je pars de Lyon », « 1 500 € maximum » : ce sont des messages comme les autres. Ils sont dans la conversation, donc le modèle les relit à chaque tour. Pas besoin d'un formulaire à côté : une ligne du prompt système lui demande de s'en servir au lieu de te reposer la question.

D'où vient l'identifiant ? De la page. Au premier chargement, elle tire un identifiant au hasard (`crypto.randomUUID()`), le garde dans le navigateur (`localStorage`) et l'envoie avec chaque message. Même navigateur, même conversation. Autre navigateur, autre conversation.

> 💡 **À retenir** — Le modèle est sans mémoire. La mémoire, c'est ce que ton code choisit de lui renvoyer. Ici, le checkpointer renvoie toute la conversation, y compris ce que le voyageur a dit de lui.

Une précision sur l'outil choisi. `create_agent`, de LangChain, fabrique un petit graphe LangGraph autour du modèle : c'est la boucle du chapitre 1, toute faite. Pour l'instant, cet agent n'a aucun outil. On l'utilise quand même ici pour une seule raison : il accepte un checkpointer, et c'est tout ce dont on a besoin.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

```text
chapitre-08-memoire/mytravel/
├── server.py          ← + l'identifiant de conversation
├── static/index.html  ← + l'identifiant, créé et envoyé
├── app/
│   ├── assistant.py   ← NOUVEAU : un agent avec mémoire
│   ├── memory.py      ← NOUVEAU : SQLite et le checkpointer
│   └── modele.py
└── tests/             ← 10 tests
```

| Fichier | Ce qui change |
|---|---|
| `app/memory.py` | ouvre `mytravel.db`, fournit le checkpointer |
| `app/assistant.py` | remplace `app/chat.py` : l'agent, son prompt, sa mémoire |
| `server.py` | reçoit l'identifiant de conversation et le passe à l'agent |
| `static/index.html` | crée l'identifiant, le garde, l'envoie avec chaque message |

### Lancer le chapitre

```bash
cd chapitre-08-memoire/mytravel
uvicorn server:app --reload
pytest                    # 10 passed
```

Refais l'essai : « Je pars à Lisbonne », puis « Et en mai ? ». Cette fois, il sait. Arrête le serveur (Ctrl+C), relance-le, écris « Tu te souviens où je pars ? » : il sait encore. Un fichier `mytravel.db` est apparu dans le dossier, c'est là que tout est rangé.

Puis écris « Je suis belge », et un peu plus tard « Il me faut un visa pour le Canada ? ». La réponse parle des Belges, sans que tu l'aies redit. Enfin, ouvre une fenêtre de navigation privée : nouvelle conversation, myTravel ne te connaît pas.

### À toi d'abord

Ouvre `app/assistant.py` et cherche le mot `conversation`. Suis-le jusqu'à LangGraph. Puis ouvre `app/memory.py` et devine : où sont créées les tables SQL de la conversation ? Ce fichier n'en écrit aucune.

## On lit le code ensemble

### `server.py` : ce qui arrive en plus

Je compare avec le chapitre 7, c'est le réflexe à prendre : qu'est-ce qui a changé ? Le contrat de `/api/chat` a un champ de plus, `conversation`, entre 8 et 64 caractères. La route le passe tel quel à l'agent :

<!-- code: mytravel/server.py 39-41 -->
```python
@app.post("/api/chat")
def chat(body: ChatRequest):
    return live(stream_mytravel(body.message, body.conversation))
```

Une seule ligne a changé, et c'est voulu : le serveur ne sait rien du voyageur. Il transmet l'identifiant, l'agent fait le reste. Je vais voir où il va.

### `app/assistant.py` : où vit la mémoire

<!-- code: mytravel/app/assistant.py 16-39 -->
```python
PROMPT = """You are myTravel, a travel assistant. Today is {today}.
Use what the traveler said earlier (nationality, home city,
budget) instead of asking again.
You find and compare; the traveler books and pays on the
provider's website. Answer in the traveler's language, with short
Markdown sections."""

saver = checkpointer()


def stream_mytravel(message, conversation):
    """One message in; the answer out, word by word."""
    prompt = PROMPT.format(today=date.today())
    agent = create_agent(get_chat_model(), [],
                         system_prompt=prompt, checkpointer=saver)
    config = {"configurable": {"thread_id": conversation}}
    # "messages": the model's tokens, as it writes them.
    for token, _ in agent.stream(
            {"messages": [("user", message)]}, config,
            stream_mode="messages"):
        if token.content:
            yield {"type": "token", "text": token.content}
    answer = agent.get_state(config).values["messages"][-1]
    yield {"type": "done", "answer": answer.content}
```

Je commence par le prompt. Sa deuxième phrase est nouvelle : « sers-toi de ce que le voyageur a déjà dit ». Sans elle, un petit modèle gratuit a tendance à redemander ta nationalité à chaque question, alors qu'elle est trois messages plus haut. Puis trois lignes portent toute la mémoire, et je les lis lentement.

`saver = checkpointer()` est créé **une seule fois**, au chargement du module. C'est lui qui parle à SQLite. L'agent, lui, est reconstruit à chaque message, et ça ne coûte rien : c'est un assemblage d'objets, sans le moindre appel réseau.

`config = {"configurable": {"thread_id": conversation}}` est la ligne la plus importante du chapitre. C'est elle qui dit à LangGraph : « range et relis sous ce nom-là ». Oublie-la, et LangGraph refuse de tourner avec un checkpointer. Mets la même valeur pour tout le monde, et tous les visiteurs partagent une seule conversation.

`agent.stream({"messages": [("user", message)]}, config, ...)` n'envoie **que** le nouveau message. Je me suis posé la question la première fois : où est l'historique ? Il est déjà dans SQLite. LangGraph le recharge, ajoute le nouveau message à la suite, appelle le modèle, enregistre la réponse.

`stream`, et pas `invoke` : c'est le streaming du chapitre 7, version LangGraph. `stream_mode="messages"` demande les tokens du modèle à mesure qu'il les écrit, chacun avec ses métadonnées (qu'on ignore ici, d'où le `_`). Une fois le flux terminé, `agent.get_state(config)` relit l'état enregistré : son dernier message est la réponse entière, qui part dans `done`.

Le prompt système, lui, n'est pas enregistré : il est reconstruit à chaque message, avec la date du jour. Seuls les messages s'empilent dans SQLite.

> ⚠️ **Piège classique** — Croire que le modèle « retient » ta nationalité. Il la **relit**, dans l'historique, à chaque tour. Change de conversation (autre navigateur, stockage vidé) et elle a disparu. Et si tu te contredis (« je suis belge », puis « mon passeport est français »), c'est le modèle qui tranche, le plus souvent en faveur du dernier message. Pour un visa, redis-le clairement plutôt que de parier.

### `app/memory.py` : un fichier SQLite

<!-- code: mytravel/app/memory.py 14-21 -->
```python
DB = os.environ.get("MYTRAVEL_DB", "mytravel.db")
# FastAPI answers in several threads: allow them to share the
# connection, one query at a time (SqliteSaver locks it).
saver_db = sqlite3.connect(DB, check_same_thread=False)


def checkpointer():
    return SqliteSaver(saver_db)
```

Huit lignes, et une seule mérite une explication : `check_same_thread=False`. FastAPI traite les requêtes dans plusieurs fils d'exécution (*threads*) en parallèle. Par défaut, SQLite en Python refuse qu'une connexion ouverte dans un fil serve dans un autre. Cette option lève l'interdiction, mais elle ne rend pas la connexion sûre pour deux fils **en même temps** : il faut faire passer les requêtes une par une. `SqliteSaver` s'en charge avec son propre verrou.

Réponse à la question de tout à l'heure : ce fichier ne crée **aucune** table. C'est `SqliteSaver` qui crée les siennes tout seul, au premier usage, et qui y range chaque étape de chaque conversation.

Et `MYTRAVEL_DB` ? Les tests mettent `:memory:` : une base qui vit en mémoire et disparaît à la fin. Les tests ne salissent donc jamais ton vrai fichier.

### `static/index.html` : l'identifiant

<!-- code: mytravel/static/index.html 123-128 -->
```html
// One id per browser: the server finds the conversation with it.
let conversation = localStorage.getItem("conversation");
if (!conversation) {
  conversation = crypto.randomUUID();
  localStorage.setItem("conversation", conversation);
}
```

Un identifiant tiré au hasard, gardé dans le navigateur, puis glissé dans chaque envoi : `JSON.stringify({conversation, ...body})`. Ce n'est pas un compte utilisateur, et ce n'est pas fait pour : il n'y a ni mot de passe ni adresse e-mail. Vide le stockage du site, et tu repars de zéro. Pour un assistant de voyage sans inscription, c'est ce qu'on veut.

## QCM

**1.** Où vit la mémoire de la conversation ?

- **a)** Dans le modèle, qui apprend de chaque message
- **b)** Dans SQLite, rangée par le checkpointer
- **c)** Dans le navigateur, avec les messages
- **d)** Sous l'identifiant de conversation envoyé par la page

**2.** Que se passe-t-il si tous les visiteurs envoient le même `thread_id` ?

- **a)** Ils partagent une seule conversation
- **b)** LangGraph refuse
- **c)** Chacun voit les messages des autres dans le contexte du modèle
- **d)** Rien, le modèle les sépare tout seul

**3.** Tu as écrit « Je suis belge » il y a trois messages. Comment myTravel le sait-il encore ?

- **a)** Le modèle l'a appris pendant la conversation
- **b)** Le message est dans l'historique, relu à chaque tour
- **c)** Un formulaire l'a rangé à part
- **d)** Le prompt lui demande de se servir de ce que le voyageur a déjà dit

**4.** `agent.stream` ne reçoit que le nouveau message. Où est l'historique ?

- **a)** Perdu, il faut le renvoyer
- **b)** Rechargé par LangGraph depuis le checkpointer
- **c)** Dans `localStorage`
- **d)** Dans le prompt système

**5.** Qui crée les tables SQL de la conversation ?

- **a)** `app/memory.py`, au démarrage
- **b)** `SqliteSaver`, au premier usage
- **c)** La page, dans le navigateur
- **d)** Personne : SQLite range tout dans une seule table fixe

**6.** Pourquoi les tests mettent-ils `MYTRAVEL_DB=:memory:` ?

- **a)** Pour aller plus vite
- **b)** Pour ne jamais toucher au vrai `mytravel.db`
- **c)** Parce que SQLite exige un fichier en production
- **d)** Pour que chaque lancement des tests reparte d'une base vide

**Réponses.** Q1 : b, d · Q2 : a, c · Q3 : b, d · Q4 : b · Q5 : b · Q6 : b, d

## Ce qu'il faut retenir

1. Le modèle n'a aucune mémoire : la mémoire est ce que ton code lui renvoie à chaque appel.
2. Le checkpointer de LangGraph enregistre la conversation après chaque étape, sous un `thread_id`. Un identifiant par conversation, sinon les conversations se mélangent.
3. Ce que le voyageur dit de lui (nationalité, ville, budget) est un message comme un autre : le modèle le relit dans l'historique, et le prompt lui demande de s'en servir.
4. SQLite suffit pour commencer : un fichier, aucune installation, et `SqliteSaver` crée ses tables tout seul.
5. La page tire un identifiant au hasard et le garde dans le navigateur : pas de compte, pas de mot de passe.

**Au chapitre suivant :** myTravel se souvient, mais il ne sait toujours rien du monde. Demande-lui s'il te faut un visa pour le Japon : il répond de mémoire, peut-être juste, peut-être d'il y a deux ans. On lui apprend à chercher sur les sites officiels et à citer la page lue.

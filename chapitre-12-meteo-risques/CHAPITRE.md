# Chapitre 12 — Météo et risques

> **Dossier GitHub associé :** `chapitre-12-meteo-risques/`

**À la fin de ce chapitre, tu sauras :**

- interroger une API météo gratuite, sans clé, en deux appels (lieu, puis jours) ;
- choisir entre prévision et historique selon la date du voyage, et le dire au voyageur ;
- résumer les conseils officiels aux voyageurs à partir de la page du ministère ;
- reconnaître les signes d'un agent qui a trop d'outils ;
- prêter tes outils à d'autres agents avec MCP, et savoir quand c'est inutile.

## « Il fera beau, c'est l'été »

Une amie partait à Bali en août. Elle demande à un chatbot le temps qu'il fera. Réponse : « En août, c'est la saison sèche à Bali, ensoleillé, 30 °C. » C'était vrai en moyenne. Elle est tombée sur une semaine de pluie, et surtout, elle n'avait jamais lu qu'un volcan de l'île de Lombok, juste à côté, faisait annuler des vols cette semaine-là. L'information était sur la page « Conseils aux voyageurs » du ministère, mise à jour la veille.

Deux leçons. Pour la météo, une moyenne n'est pas une prévision, et il faut dire laquelle des deux on donne. Pour les risques, la seule source sérieuse est la page officielle du jour.

## Prévision, ou l'an dernier

**Open-Meteo** est un service météo libre et gratuit, sans clé, qui agrège les modèles des grands instituts (Météo-France, le centre européen, l'agence américaine). Il offre trois services utiles ici :

- le **géocodage** : « Lisbonne » devient une latitude et une longitude ;
- la **prévision**, jour par jour, jusqu'à 16 jours ;
- l'**archive** : le temps qu'il a fait, jour par jour, depuis des décennies.

Une prévision au-delà de 16 jours n'existe pas : personne ne sait le temps qu'il fera à Rome dans quatre mois. Pour un voyage lointain, l'outil donne donc le temps relevé **l'an dernier aux mêmes dates**, et le dit en toutes lettres : « last year, same dates (not a forecast) ». C'est un ordre de grandeur honnête, pas une promesse.

Pour les risques, l'outil `travel_advice` cherche la page « Conseils aux voyageurs » du pays sur diplomatie.gouv.fr et la lit. C'est la page que le ministère tient à jour : sécurité, zones déconseillées, risques naturels, santé.

> 💡 **À retenir** — Une donnée sans sa nature (« prévision » ou « relevé de l'an dernier ») trompe le lecteur, même si elle est exacte. L'outil écrit la nature de la donnée dans sa réponse, pour que le modèle ne puisse pas l'oublier.

## MCP : prêter tes outils à d'autres agents

Tes deux outils marchent. Imagine maintenant qu'une collègue veuille la même météo dans Claude Code, pendant qu'elle code. Ou qu'une autre équipe la veuille dans son agent, écrit en TypeScript. Personne n'ira importer ton `app/tools.py`.

**MCP** (*Model Context Protocol*) règle ce problème. C'est un protocole ouvert, lancé par Anthropic fin 2024, puis adopté par OpenAI, Google et la plupart des éditeurs d'outils pour développeurs. Un **serveur MCP** publie des outils. Un **client MCP** (un agent, un éditeur de code, Claude Desktop) s'y connecte, demande la liste des outils, puis les appelle. Pour chaque outil, la liste donne ce que tu mettais dans `tools` au chapitre 1 : un nom, une description, des arguments typés. Sauf qu'ici, personne ne recopie la fiche : le client la demande au serveur.

Une précision qui t'évitera des heures de plomberie : **myTravel n'en a pas besoin**. Ses agents tournent dans le même programme que ses outils, et appellent `weather` comme n'importe quelle fonction Python. Passer par MCP ajouterait un processus, un aller-retour réseau et une cause de panne, pour le même résultat. Beaucoup d'agents en production se passent de MCP, et ils ont raison.

MCP devient utile quand l'outil et l'agent ne vivent pas au même endroit :

- **des agents que tu n'as pas écrits** doivent s'en servir : Claude Code, Claude Desktop, Cursor, l'agent d'une autre équipe ;
- **un autre langage** : ton outil est en Python, l'agent en TypeScript ou en Java ;
- **un outil tenu par quelqu'un d'autre** : GitHub, Notion ou Stripe publient leur serveur MCP, tu le branches au lieu de réécrire un client pour leur API ;
- **plusieurs agents, un seul outil** : les droits, les quotas et le cache vivent à un seul endroit.

Il ne sert à rien quand un seul programme possède ses agents et ses outils, et encore moins « au cas où ». Ici, on coche la première case : la météo et les conseils aux voyageurs de myTravel serviront aussi à Claude Code, sans toucher une ligne des agents.

> 💡 **À retenir** — MCP ne rend pas un agent plus malin : il rend un outil **partageable**. Tant qu'un seul programme se sert de tes outils, une fonction Python suffit.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

| Fichier | Ce qui change |
|---|---|
| `app/tools.py` | les outils `weather` et `travel_advice` |
| `app/sources.py` | `OFFICIAL` gagne le sujet `"safety"` |
| `app/assistant.py` | `TOOLS` passe à dix outils |
| `mcp_server.py` | NOUVEAU : `weather` et `travel_advice` servis en MCP aux autres agents |

### Lancer le chapitre

```bash
cd chapitre-12-meteo-risques/mytravel
uvicorn server:app --reload
pytest                    # 32 passed
```

Trois essais :

1. « Quel temps à Lisbonne la semaine prochaine ? » : une prévision, jour par jour.
2. « Et à Tokyo du 10 au 20 mars prochain ? » : la réponse doit préciser que ce sont les relevés de l'an dernier.
3. « Le Pérou, c'est sûr pour un voyageur seul ? » : un résumé de la page du ministère, avec son lien.

Puis refais l'expérience du chapitre 11, en plus gros : « Plan complet pour Rome, 4 jours en mai, 800 €, départ de Lyon, passeport français. » Avec dix outils, observe le terminal. Selon le modèle gratuit du jour, tu verras sans doute un de ces symptômes : un outil appelé deux fois avec les mêmes arguments, une partie de la question ignorée (la météo, souvent), une réponse qui s'arrête avant la fin, ou une erreur 429 parce que l'agent a enchaîné trop d'appels.

Dernier essai : prête la météo à un autre agent. Dans un second terminal, lance le serveur MCP, puis branche-le sur Claude Code si tu l'as :

```bash
cd chapitre-12-meteo-risques/mytravel
python mcp_server.py      # http://127.0.0.1:8001/mcp
# dans un troisième terminal :
claude mcp add --transport http mytravel http://127.0.0.1:8001/mcp
claude mcp list           # mytravel: ... ✔ Connected
```

Demande à Claude Code « Quel temps à Lisbonne ce week-end ? » : il te demande la permission d'appeler l'outil `weather` du serveur `mytravel`, et répond avec les chiffres d'Open-Meteo. Sans Claude Code, l'inspecteur officiel (`npx @modelcontextprotocol/inspector`, il faut Node.js) ouvre une page où tu listes et appelles les outils à la main. Quand tu as fini : `claude mcp remove mytravel`.

### À toi d'abord

Dans `weather`, trouve la ligne qui décide entre prévision et archive. Puis demande-toi : que se passe-t-il pour un voyage qui commence dans 10 jours et dure 3 semaines ?

Ouvre aussi `mcp_server.py`, et cherche où est écrit le code de la météo.

## On lit le code ensemble

### `weather` : deux appels, une décision

La fonction est la plus longue du projet, alors je la coupe en deux. D'abord, trouver le lieu et choisir la source :

<!-- code: mytravel/app/tools.py 132-154 -->
```python
@tool
def weather(city: str, start: str, end: str) -> str:
    """Weather in a city between two dates (YYYY-MM-DD).

    The forecast if the trip ends within 16 days; otherwise the
    weather of last year on the same dates, as a guide.
    """
    places = httpx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "fr"},
        timeout=15).json().get("results")
    if not places:
        return f"Unknown city: {city}"
    place = places[0]
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if (last - date.today()).days < 16:
        url = "https://api.open-meteo.com/v1/forecast"
        kind = "forecast"
    else:  # no forecast that far: the same days, a year earlier
        url = "https://archive-api.open-meteo.com/v1/archive"
        first, last = (first - timedelta(days=365),
                       last - timedelta(days=365))
        kind = "last year, same dates (not a forecast)"
```

Le géocodage renvoie une liste de lieux ; `count: 1` garde le plus probable. `.get("results")` et pas `["results"]` : quand la ville n'existe pas, Open-Meteo ne renvoie pas de liste vide, il ne renvoie **pas de clé** du tout. Je l'ai appris en tapant « Lisbone » avec une faute.

La décision tient en une ligne : `(last - date.today()).days < 16`. Elle porte sur la **fin** du voyage. Réponse à ta question : un voyage qui commence dans 10 jours et dure 3 semaines finit dans 31 jours, donc on bascule sur l'archive. On aurait pu mélanger prévision et archive jour par jour. J'ai choisi la règle la plus simple à expliquer au voyageur.

Pourquoi `timedelta(days=365)` plutôt que changer l'année avec `first.replace(year=...)` ? Parce que `date(2028, 2, 29).replace(year=2027)` lève une erreur : le 29 février n'existe pas toutes les années. Soustraire 365 jours marche toujours, au prix d'un jour d'écart les années bissextiles. Pour une météo indicative, c'est sans importance.

Ensuite, lire les jours :

<!-- code: mytravel/app/tools.py 155-168 -->
```python
    days = httpx.get(url, timeout=15, params={
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "start_date": str(first), "end_date": str(last),
        "daily": "temperature_2m_min,temperature_2m_max,"
                 "precipitation_sum",
        "timezone": "auto"}).json()["daily"]
    lines = [f"{day}: {low:.0f} to {high:.0f} °C, {rain} mm"
             for day, low, high, rain in zip(
                 days["time"], days["temperature_2m_min"],
                 days["temperature_2m_max"],
                 days["precipitation_sum"])]
    return (f"{place['name']} ({place['country']}), {kind}, "
            "source https://open-meteo.com\n" + "\n".join(lines))
```

La prévision et l'archive acceptent les mêmes paramètres : c'est pour ça qu'un seul appel suffit, avec une adresse qui change. Open-Meteo renvoie des **colonnes** (une liste de dates, une liste de minimums, une liste de maximums) ; `zip` les recolle en lignes, une par jour.

La dernière ligne est celle que je veux que tu remarques. Elle met dans la réponse le lieu trouvé, la **nature** de la donnée et la **source**. Si le géocodage s'est trompé de ville (il existe un Paris au Texas), le modèle et le voyageur le voient tout de suite.

### `travel_advice` : chercher, prendre le premier, lire

<!-- code: mytravel/app/tools.py 171-183 -->
```python
@tool
def travel_advice(country: str) -> str:
    """The French government's official advice for a country."""
    domains = ["diplomatie.gouv.fr"]
    results = search_web(f"conseils aux voyageurs {country}",
                         domains)
    if not results:
        return "No official advice found. Say so; do not guess."
    url = results[0]["url"]
    try:
        return f"{url}\n{read_page(url, domains)}"
    except (ValueError, httpx.HTTPError) as error:
        return f"Could not read {url}: {error}"
```

Cet outil fait en un seul appel ce que l'agent ferait en deux (chercher, puis lire). Pourquoi ? Parce que c'est toujours la même page qu'on veut, et qu'un appel d'outil en moins, c'est un aller-retour avec le modèle en moins. Quand le chemin est toujours le même, on l'écrit en code ; on laisse le modèle choisir quand il y a vraiment un choix.

La liste ne contient qu'un domaine. Pour les conseils de sécurité, je ne veux pas de mélange : la page du ministère, ou rien.

### `mcp_server.py` : une deuxième porte, les mêmes outils

<!-- code: mytravel/mcp_server.py 12-31 -->
```python
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from app.tools import travel_advice, weather

load_dotenv()  # the same .env as the app: TAVILY_API_KEY

server = MCPServer("mytravel")
# The same functions as the agents use: one code, two doors. The
# name, the docstring and the typed arguments become the tool
# description any MCP client reads.
server.add_tool(weather.func)
server.add_tool(travel_advice.func)

if __name__ == "__main__":
    # HTTP rather than stdio: in stdio, standard output belongs to
    # the protocol, and the JSON logs of chapter 17 would break it.
    # 127.0.0.1 only: nobody else on the network can call it.
    server.run("streamable-http", port=8001)
```

Réponse à ta question : le code de la météo n'est pas dans ce fichier. `weather` est l'outil LangChain que tu viens de lire, et `weather.func` est la fonction Python qu'il enveloppe. `add_tool` lit son nom, sa docstring et ses annotations de type, et en tire la fiche que reçoit tout client MCP. Un seul code, deux portes : les agents de myTravel entrent par l'appel direct, les autres par MCP. Si tu corriges la météo, les deux portes en profitent.

`MCPServer` vient du SDK officiel, le paquet `mcp`. Jusqu'à sa version 2, il s'appelait `FastMCP` : tu croiseras encore ce nom dans beaucoup de tutoriels.

MCP connaît deux façons de parler. En **stdio**, le client lance le serveur comme un sous-programme et lui écrit sur son entrée standard ; c'est le choix le plus courant pour un outil local. Mais alors la sortie standard appartient au protocole : le moindre `print` y glisse une ligne qui n'est pas un message MCP, et le client décroche. Or au chapitre 17, myTravel écrira ses journaux justement là. On prend donc **HTTP**, sur le port 8001, puisque la page occupe déjà le 8000. `load_dotenv()` lit le même `.env` que l'application : sans lui, `travel_advice` ignorerait ta clé Tavily.

Par défaut, `run` n'écoute que sur `127.0.0.1` : seule ta machine peut appeler le serveur. Il n'a pas de mot de passe, il ne doit donc pas en sortir. Le chapitre 15 revient sur ce point, et sur le risque inverse : brancher chez toi le serveur MCP d'un inconnu.

Les deux nouveaux tests de `tests/test_ch12_weather_risks.py` connectent un vrai client MCP au serveur, dans le même processus (`Client(server)`) : ni réseau, ni port ouvert.

> ⚠️ **Piège classique** — Ajouter MCP entre tes agents et tes propres outils « pour faire propre ». Tu paies un processus de plus, des pannes de plus et une latence de plus, pour un service que personne d'autre n'utilise. Ouvre la porte MCP le jour où un autre programme frappe.

### Dix outils : le diagnostic

Regarde `TOOLS` dans `app/assistant.py` : dix outils, et un prompt qui demande à l'agent de tout savoir faire. Les symptômes que tu as vus en lançant le plan complet ont une cause simple. À chaque tour, le modèle relit dix descriptions, et doit garder en tête une question qui touche cinq sujets. C'est beaucoup pour un modèle gratuit, et ça coûte cher pour un modèle payant. C'est aussi le revers de MCP : branche trois serveurs de vingt outils sur un agent, et il relit soixante descriptions à chaque tour.

La solution n'est pas un meilleur prompt. C'est de **découper** : plusieurs agents, chacun avec deux ou trois outils et une mission courte, et un chef d'orchestre qui répartit. C'est le chapitre 13.

> ⚠️ **Piège classique** — Soigner un agent surchargé en allongeant son prompt (« N'oublie pas la météo ! Appelle chaque outil une seule fois ! »). Chaque consigne ajoutée est une chose de plus à retenir. Si l'agent oublie des consignes, retire-lui du travail au lieu de lui en écrire d'autres.

## QCM

**1.** Le voyage a lieu dans quatre mois. Que donne l'outil `weather` ?

- **a)** Une prévision à quatre mois
- **b)** Le temps relevé l'an dernier aux mêmes dates
- **c)** Une réponse qui précise que ce n'est pas une prévision
- **d)** Une erreur

**2.** Pourquoi `.get("results")` et pas `["results"]` sur le géocodage ?

- **a)** Parce qu'une ville inconnue ne renvoie pas la clé `results`
- **b)** Pour aller plus vite
- **c)** Pour éviter une `KeyError` et répondre « Unknown city »
- **d)** Parce que `httpx` l'exige

**3.** Pourquoi soustraire 365 jours plutôt que changer l'année ?

- **a)** Parce que le 29 février n'existe pas toutes les années
- **b)** Parce que `replace` est lent
- **c)** Parce qu'Open-Meteo refuse les années
- **d)** Parce que `timedelta` ne lève jamais d'erreur sur un 29 février

**4.** Pourquoi `travel_advice` cherche et lit en un seul outil ?

- **a)** Parce que la page voulue est toujours la même
- **b)** Pour économiser un aller-retour avec le modèle
- **c)** Parce que le modèle ne sait pas lire de page
- **d)** Parce que diplomatie.gouv.fr l'exige

**5.** Un agent avec dix outils oublie la météo dans un plan complet. Quelle est la meilleure réponse ?

- **a)** Ajouter « N'oublie pas la météo » au prompt
- **b)** Découper le travail entre plusieurs agents spécialisés
- **c)** Retirer l'outil météo
- **d)** Donner moins d'outils à chaque agent

**6.** Dans quels cas un serveur MCP se justifie-t-il ?

- **a)** Les agents de myTravel appellent leurs propres outils, dans le même programme
- **b)** Claude Code doit pouvoir appeler la météo de myTravel
- **c)** Une autre équipe veut ton outil Python dans son agent écrit en TypeScript
- **d)** On veut rendre l'agent plus intelligent

**7.** Pourquoi `mcp_server.py` parle-t-il HTTP plutôt que stdio ?

- **a)** HTTP est toujours plus rapide
- **b)** stdio n'existe pas sous Windows
- **c)** En stdio, la sortie standard appartient au protocole, et un `print` la casse
- **d)** Les journaux du chapitre 17 sont écrits sur la sortie standard

**Réponses.** Q1 : b, c · Q2 : a, c · Q3 : a, d · Q4 : a, b · Q5 : b, d · Q6 : b, c · Q7 : c, d

## Ce qu'il faut retenir

1. Open-Meteo donne géocodage, prévision et archive, gratuitement et sans clé.
2. Au-delà de 16 jours, il n'y a pas de prévision : on donne l'an dernier aux mêmes dates, et on le dit.
3. Un outil écrit dans sa réponse la nature et la source de la donnée, pour que le modèle ne puisse pas les perdre.
4. Quand le chemin est toujours le même (chercher puis lire la page du ministère), on l'écrit en code dans un seul outil.
5. Dix outils pour un seul agent, c'est trop : la solution est de découper, pas d'allonger le prompt.
6. MCP rend un outil partageable entre programmes, agents et langages. Tant qu'un seul programme s'en sert, une fonction Python suffit.

**Au chapitre suivant :** on découpe. Un agent Mission qui comprend et répartit, cinq spécialistes qui travaillent en même temps, un agent Synthèse qui assemble. Le tout dessiné avec LangGraph, et le schéma complet de l'architecture.

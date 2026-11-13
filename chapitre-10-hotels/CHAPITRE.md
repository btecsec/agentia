# Chapitre 10 — Hôtels : les vrais prix du jour

> **Dossier GitHub associé :** `chapitre-10-hotels/`

**À la fin de ce chapitre, tu sauras :**

- appeler une API de prix d'hôtels gratuite et sans clé, Xotelo ;
- retrouver un identifiant qu'on n'a pas, avec la recherche web du chapitre 9 ;
- lancer plusieurs appels réseau en même temps plutôt que l'un après l'autre ;
- distinguer un outil qui cherche d'un outil qui fabrique, et dire pourquoi le second ne se trompe jamais ;
- construire un lien de recherche prérempli, proprement encodé ;
- appeler une autre API publique sans clé (les taux de la Banque centrale européenne).

## « À partir de 64 € »

Tu as sûrement vécu ça. Un article de blog promet « des hôtels à Porto à partir de 64 € la nuit ». Tu cherches tes dates. Plus rien à 64 €. L'article datait de l'an dernier, et de toute façon il parlait d'un mardi de novembre.

Un prix d'hôtel n'existe que pour **des dates**, chez **un vendeur**, **aujourd'hui**. Tout le reste est une estimation, et une estimation ne sert à rien à quelqu'un qui veut réserver. myTravel n'en donnera jamais.

Le problème, c'est que les vraies API de prix (celles de Booking ou d'Expedia) sont réservées à leurs partenaires commerciaux. Il existe heureusement **Xotelo** : un service gratuit, sans clé, qui lit les prix affichés sur TripAdvisor. Pour un hôtel et deux dates, il répond par le prix d'une nuit chez chaque vendeur (Booking.com, Agoda, Trip.com…). Un vrai prix, son vendeur, lu à l'instant : on n'en demandait pas plus.

## Deux sortes d'outils

Ce chapitre donne trois outils à l'agent, et ils ne se ressemblent pas.

Un **outil qui interroge** demande au monde et rapporte ce qu'il trouve : `hotel_offers` choisit les hôtels les mieux notés d'une ville, puis demande à Xotelo leur prix pour tes dates. Son résultat peut être vide : un hôtel complet n'a pas de prix. Le modèle doit le dire, pas l'inventer.

Un **outil qui fabrique** calcule une réponse exacte à partir de ses entrées : `hotel_links` assemble une adresse Booking. Il ne peut pas se tromper si on lui donne les bonnes dates. Pourquoi en faire un outil plutôt que laisser le modèle écrire le lien ? Parce qu'un modèle qui écrit une URL de mémoire se trompe sur un paramètre une fois sur trois, et invente parfois un domaine qui n'existe pas.

Le troisième, `exchange_rate`, interroge **Frankfurter**, un service gratuit et sans clé qui publie les taux de référence de la Banque centrale européenne. Pour un hôtel à Tokyo affiché en yens, l'agent peut convertir sans deviner.

Reste une difficulté. Xotelo connaît les villes par leur code TripAdvisor (`g189158` pour Lisbonne), et le service qui traduit un nom de ville en code est payant. On le contourne avec ce qu'on a déjà : la recherche du chapitre 9. Les pages d'hôtels de TripAdvisor ont une adresse qui contient ce code : `Hotel_Review-g189158-...`. Il suffit de chercher « hôtel Lisbonne avis tripadvisor » et de lire les adresses.

> 💡 **À retenir** — Un prix se donne avec ses dates, son vendeur et son lien. Tout ce qui peut être calculé exactement est calculé par du code, pas écrit par le modèle : un lien, une conversion, un total.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

```text
chapitre-10-hotels/mytravel/
└── app/
    ├── hotels.py      ← NOUVEAU : les prix du jour (Xotelo)
    ├── tools.py       ← + hotel_links, exchange_rate
    └── assistant.py   ← + 3 outils dans TOOLS (5 en tout)
```

| Fichier | Ce qui change |
|---|---|
| `app/hotels.py` | trouve les hôtels d'une ville, lit le prix d'une nuit chez chaque vendeur |
| `app/tools.py` | deux outils qui fabriquent : le lien Booking, le taux de change |
| `app/assistant.py` | l'agent reçoit les trois outils, et une règle : jamais un prix lu ailleurs |

### Lancer le chapitre

```bash
cd chapitre-10-hotels/mytravel
uvicorn server:app --reload
pytest                    # 22 passed
```

Demande : « Un hôtel à Porto, du 2027-05-02 au 2027-05-06, pour deux, budget 90 € la nuit. » Dans la bulle d'attente, la pastille `hotel_offers` apparaît. Puis la réponse : cinq hôtels notés 4 sur 5 ou plus, chacun avec son prix de la nuit, son vendeur, et deux liens, ses avis et sa recherche Booking à tes dates. Ouvre un lien Booking : la recherche est déjà remplie. Puis : « Et à Tokyo, combien ça fait en yens, 120 € la nuit ? » L'agent appelle `exchange_rate`, et le taux du jour s'affiche avec sa date.

Essaie enfin sans dates : « Un hôtel sympa à Porto ? ». L'agent te demande tes dates. Sans dates, pas de prix : c'est voulu.

### À toi d'abord

Ouvre `app/hotels.py` et trouve la ligne qui lit le code de la ville dans les adresses TripAdvisor. Puis compte les requêtes envoyées à Xotelo pour cinq hôtels : sont-elles envoyées l'une après l'autre ?

## On lit le code ensemble

### `city_key` : un identifiant qu'on n'a pas

<!-- code: mytravel/app/hotels.py 22-31 -->
```python
def city_key(city):
    """TripAdvisor's code for a city, g189158 for Lisbon: read in
    the addresses of its hotel pages."""
    pages = search_web(f"hôtel {city} avis tripadvisor",
                       ["tripadvisor.com"], max_results=8)
    codes = re.findall(r"Hotel_Review-(g\d+)-",
                       " ".join(page["url"] for page in pages))
    if not codes:
        raise ValueError(f"no TripAdvisor hotel page for {city}")
    return Counter(codes).most_common(1)[0][0]
```

Réponse à ta première question : c'est `re.findall`, avec le motif `Hotel_Review-(g\d+)-`. Les parenthèses capturent le code, `g` suivi de chiffres. Je lis aussi ce qui se passe quand la recherche ramène une page d'une autre ville, celle d'un hôtel de Sintra par exemple : `Counter(...).most_common(1)` garde le code le plus fréquent. Sur huit pages, la ville cherchée gagne. Et si aucune page n'a ce motif, l'outil lève une erreur claire, que le middleware du chapitre 9 transforme en message pour le modèle.

### `best_hotels` et `night` : deux appels, deux questions

<!-- code: mytravel/app/hotels.py 34-56 -->
```python
def best_hotels(city):
    """The best value hotels of a city, rated 4 out of 5 or more."""
    found = httpx.get(f"{HOTELS}/list", timeout=30, params={
        "location_key": city_key(city), "sort": "best_value",
        "limit": 10}).json()["result"]["list"]
    return [hotel for hotel in found
            if hotel["review_summary"]["rating"] >= 4
            ][:HOTELS_PER_CITY]


def rooms(adults):
    return -(-adults // 2)  # two per room, rounded up


def night(hotel, checkin, checkout, adults):
    """The cheapest room for one night on these dates, with its
    seller; None if nobody sells it."""
    found = httpx.get(f"{HOTELS}/rates", timeout=30, params={
        "hotel_key": hotel["key"], "chk_in": checkin,
        "chk_out": checkout, "adults": adults,
        "rooms": rooms(adults), "currency": "EUR"}).json()
    rates = (found["result"] or {}).get("rates") or []
    return min(rates, key=lambda rate: rate["rate"], default=None)
```

`best_hotels` demande à Xotelo la liste des hôtels de la ville, triée par **rapport qualité-prix** (`sort: best_value`), et garde les cinq premiers notés 4 sur 5 ou plus. Cinq, c'est un choix, pas un catalogue : au-delà, la réponse devient illisible et les appels se multiplient.

`night` demande le prix d'un hôtel à tes dates. Xotelo répond une liste de vendeurs, chacun avec son prix : `min(...)` garde le moins cher, avec son nom. `rooms` compte les chambres, deux personnes par chambre, arrondi au-dessus : `-(-3 // 2)` vaut 2, une astuce Python pour arrondir une division vers le haut. Et `default=None` dit quoi faire quand personne ne vend de chambre : rien. Pas de prix inventé, l'hôtel sort simplement de la liste.

### `hotel_offers` : cinq requêtes en même temps

<!-- code: mytravel/app/hotels.py 71-88 -->
```python
@tool
def hotel_offers(city: str, checkin: str, checkout: str,
                 adults: int) -> str:
    """The best value hotels of a city, with today's price of a
    night on these dates and its seller. Dates: YYYY-MM-DD.
    """
    hotels = best_hotels(city)
    # One request per hotel: sent together, not one by one.
    with ThreadPoolExecutor() as pool:
        rates = list(pool.map(
            lambda hotel: night(hotel, checkin, checkout, adults),
            hotels))
    lines = [hotel_text(hotel, rate, checkin, checkout, adults)
             for hotel, rate in zip(hotels, rates) if rate]
    if not lines:
        return "No room sold on these dates. Say so."
    return "\n".join(["Prix du jour, une nuit, sur TripAdvisor :"]
                     + lines)
```

Réponse à ta seconde question : non, pas l'une après l'autre. Chaque appel à Xotelo prend une à deux secondes. Cinq à la suite, ça fait dix secondes de silence. `ThreadPoolExecutor` les envoie en même temps : le temps total devient celui du plus lent. `pool.map` rend les résultats dans l'ordre des hôtels, ce qui permet de les remettre ensemble avec `zip`.

La docstring est la partie que le modèle lit : elle dit ce que l'outil rend (le prix d'une nuit, son vendeur) et le format des dates. Le texte rendu, lui, vient de `hotel_text`, juste au-dessus : le nom, la note, le nombre d'avis, le prix et le vendeur, la page TripAdvisor et le lien Booking aux dates. Le modèle n'a qu'à recopier.

> ⚠️ **Piège classique** — Laisser le modèle « compléter » une liste vide. Si aucun hôtel n'a de chambre à tes dates, l'outil le dit (« No room sold on these dates. Say so. »), et le prompt de l'agent interdit tout prix lu ailleurs. Sans ces deux phrases, un petit modèle te sortirait un prix vu dans un vieux blog, et c'est précisément ce qu'on voulait éviter.

### `booking_url` : le lien qui ne se trompe pas

<!-- code: mytravel/app/tools.py 71-75 -->
```python
def booking_url(city, checkin, checkout, adults):
    query = urlencode({"ss": city, "checkin": checkin,
                       "checkout": checkout,
                       "group_adults": adults})
    return f"https://www.booking.com/searchresults.fr.html?{query}"
```

`urlencode` transforme le dictionnaire en paramètres d'URL, et surtout il **encode** les caractères spéciaux : un espace devient `+`, un `é` devient `%C3%A9`. Si tu écrivais l'adresse à la main avec une f-string, « Saint-Jean-de-Luz » passerait, mais « Île de Ré » casserait le lien.

Pourquoi une fonction ordinaire *et* un outil `hotel_links` qui l'appelle ? Parce que la fonction sert aussi ailleurs : `hotel_text` l'appelle pour chaque hôtel, et au chapitre 14 la fiche de réservation l'utilisera directement, sans passer par le modèle. L'outil, lui, sert quand le voyageur n'a pas encore de dates : l'agent lui donne un lien de recherche, jamais un prix.

### `exchange_rate` : une API publique en six lignes

<!-- code: mytravel/app/tools.py 89-99 -->
```python
@tool
def exchange_rate(currency: str) -> str:
    """Today's rate of 1 euro in a currency code (JPY, USD...)."""
    code = currency.upper()
    url = "https://api.frankfurter.dev/v1/latest"
    data = httpx.get(url, params={"base": "EUR", "symbols": code},
                     timeout=15).json()
    if code not in data.get("rates", {}):
        return f"No ECB rate for {code}."
    rate = data["rates"][code]
    return f"1 EUR = {rate} {code} (ECB, {data['date']})"
```

Je lis toujours trois choses dans un appel d'API : l'adresse, les paramètres, ce qui se passe quand la réponse n'est pas celle qu'on attend. `params=` laisse `httpx` construire `?base=EUR&symbols=JPY` proprement, et `.upper()` rattrape le modèle qui écrirait `jpy`. La BCE ne publie qu'une trentaine de devises : demande le dirham marocain, et `rates` ne contient pas `MAD`. Au lieu d'une `KeyError`, l'outil répond une phrase claire. Enfin, la réponse contient la **date** du taux : un taux sans date ne vaut rien.

> ⚠️ **Piège classique** — Oublier `timeout=`. Sans lui, certaines bibliothèques attendent indéfiniment. Un service lent bloque alors toute la réponse de l'agent. Mets toujours un délai, et choisis-le : 15 secondes pour un taux, 30 pour Xotelo, plus lent.

### `app/assistant.py` : une règle de plus

La liste `TOOLS` passe de deux à cinq outils. Le prompt gagne une phrase : un prix vient de `hotel_offers`, avec son vendeur, jamais d'ailleurs. C'est la docstring de chaque outil qui apprend au modèle quand s'en servir, et cette phrase qui lui interdit de combler un trou.

## QCM

**1.** Qu'est-ce qui fait un vrai prix d'hôtel, pour myTravel ?

- **a)** Des dates précises
- **b)** Un vendeur nommé
- **c)** Un prix « à partir de » trouvé sur un blog
- **d)** Un lien pour le vérifier

**2.** Comment myTravel trouve-t-il le code TripAdvisor d'une ville ?

- **a)** Il le demande au modèle
- **b)** Il le lit dans les adresses de pages d'hôtels trouvées par la recherche web
- **c)** Il appelle un service payant
- **d)** Il garde le code le plus fréquent parmi les pages trouvées

**3.** Pourquoi `hotel_offers` utilise-t-il `ThreadPoolExecutor` ?

- **a)** Pour envoyer les requêtes des cinq hôtels en même temps
- **b)** Pour que le temps total soit celui de l'appel le plus lent, pas la somme
- **c)** Parce que Xotelo l'exige
- **d)** Pour économiser des tokens

**4.** Aucun vendeur n'a de chambre dans un hôtel à tes dates. Que fait myTravel ?

- **a)** Il donne le prix moyen de l'hôtel
- **b)** L'hôtel sort de la liste
- **c)** Il demande au modèle d'estimer
- **d)** `night` renvoie `None`

**5.** Pourquoi le lien Booking est-il fabriqué par du code plutôt qu'écrit par le modèle ?

- **a)** Un modèle qui écrit une URL se trompe facilement de paramètre
- **b)** Le code encode correctement les caractères spéciaux
- **c)** Le modèle n'a pas le droit d'écrire des liens
- **d)** Une fonction déterministe donne le même lien à chaque fois

**6.** Le voyageur demande un hôtel sans donner de dates. Que fait l'agent ?

- **a)** Il donne les prix du mois prochain
- **b)** Il demande les dates, et peut donner un lien de recherche
- **c)** Il invente des dates
- **d)** Il appelle `exchange_rate`

**Réponses.** Q1 : a, b, d · Q2 : b, d · Q3 : a, b · Q4 : b, d · Q5 : a, b, d · Q6 : b

## Ce qu'il faut retenir

1. Un prix d'hôtel n'existe que pour des dates, chez un vendeur, aujourd'hui. myTravel donne ce prix-là, avec son lien, et jamais une estimation.
2. Xotelo lit les prix de TripAdvisor, vendeur par vendeur, sans clé. Le code de la ville se lit dans les adresses trouvées par la recherche web.
3. Plusieurs appels réseau indépendants partent en même temps avec `ThreadPoolExecutor`.
4. Un outil qui interroge peut revenir vide, et il le dit ; un outil qui fabrique (un lien, un taux) ne se trompe pas.
5. Chaque appel d'API a un délai maximal et un plan pour la réponse inattendue.

**Au chapitre suivant :** il faut aussi y aller, à Porto. Les vols, avec de vraies offres là aussi, et la voiture de location.

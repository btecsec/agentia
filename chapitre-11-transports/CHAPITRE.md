# Chapitre 11 — Vols et voiture : de vraies offres

> **Dossier GitHub associé :** `chapitre-11-transports/`

**À la fin de ce chapitre, tu sauras :**

- obtenir de vraies offres de vol (compagnie, vendeur, prix, lien d'achat) avec l'API gratuite de Travelpayouts ;
- dire d'où vient un prix de vol et quel jour il a été vu ;
- chercher les offres les plus proches quand personne n'a regardé tes dates exactes ;
- encoder un morceau d'URL avec `quote`, et dire quand préférer `urlencode` ;
- mesurer le coût réel d'un outil de plus : dans le prompt, à chaque appel.

## Huit outils dans la poche

Un plombier arrive avec une caisse de quarante outils. Il sait les trouver les yeux fermés, parce que c'est son métier depuis vingt ans. Donne la même caisse à un apprenti le premier jour : il cherchera la clé de 12 pendant dix minutes et finira par prendre la pince.

Un modèle de langage, à chaque question, est cet apprenti au premier jour. Il relit la description de chaque outil, puis choisit. À la fin de ce chapitre, myTravel en aura huit. Ça marche encore très bien. Mais garde un œil sur la caisse : au chapitre 12, elle en contiendra dix, et c'est là qu'on verra l'apprenti hésiter.

## Le vol, le prix, le bouton

Le voyageur ne veut pas lire « Paris-Lisbonne en mai, à partir de 70 € ». Il veut **le** vol : la compagnie, l'heure, le prix pour ses dates, et le bouton pour l'acheter. Une recherche web ne sait pas faire ça. Il faut une **API de prix** : un service qui répond, pour un trajet et des dates, par des offres en données structurées.

Les grandes (Amadeus, Skyscanner, Kiwi) sont fermées aux développeurs indépendants ou payantes. **Travelpayouts**, le programme partenaire du comparateur Aviasales, donne un jeton gratuit, sans carte ni téléphone. Ce qu'il renvoie mérite d'être bien compris :

- ce sont des **offres réelles** : un vol, une compagnie, un vendeur, un prix, et le lien pour l'acheter ;
- elles ont été **vues par d'autres voyageurs** ces derniers jours, sur Aviasales. Le prix peut avoir bougé : on donne toujours la date où il a été vu, et le lien ouvre la recherche à jour chez le vendeur ;
- elles sont **clairsemées** : une date que personne n'a cherchée n'a pas d'offre. L'outil cherche alors les offres réelles les plus proches, à trois jours au plus, pour un séjour de même durée.

Sans jeton, pas de prix : l'agent le dit et donne un lien Google Flights prérempli. Jamais un prix lu sur une page quelconque.

Pour la voiture, un seul outil qui fabrique un lien Kayak : il n'existe pas d'API gratuite de prix de location, et le lien est plus honnête qu'une estimation.

## Ce que coûte un outil

À chaque appel au modèle, LangChain envoie la description de **tous** les outils : nom, docstring, paramètres. Huit outils, c'est environ 800 tokens de plus, à chaque tour de la boucle, avant même ta question. Un agent qui fait quatre tours pour répondre les paie quatre fois.

Et le coût n'est pas que financier. Plus la liste est longue, plus deux outils se ressemblent (`flight_offers` et `hotel_offers` ont des docstrings voisines), et plus le modèle risque de choisir le mauvais ou d'en appeler trois pour une question qui n'en demandait qu'un. Les modèles gratuits y sont plus sensibles que les grands modèles payants.

> 💡 **À retenir** — Un outil n'est pas gratuit : sa description est envoyée à chaque appel, et chaque outil de plus rend le choix plus difficile. Ajoute un outil quand il apporte un fait que le modèle ne peut pas avoir autrement. Un vrai prix de vol en est un.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

```text
chapitre-11-transports/mytravel/
└── app/
    ├── flights.py     ← NOUVEAU : les offres de vol (Travelpayouts)
    ├── tools.py       ← + flight_links, car_links
    └── assistant.py   ← + 3 outils dans TOOLS (8 en tout)
```

| Fichier | Ce qui change |
|---|---|
| `app/flights.py` | trouve le code d'une ville, lit les offres, cherche les jours voisins, écrit chaque offre |
| `app/tools.py` | `flights_url`, `cars_url`, et les outils `flight_links`, `car_links` |
| `app/assistant.py` | `TOOLS` passe à huit outils ; un prix vient de `flight_offers` ou `hotel_offers` |

### Lancer le chapitre

Crée d'abord ton jeton : inscris-toi sur travelpayouts.com, puis *Profil*, *API token*. Ajoute la ligne `TRAVELPAYOUTS_TOKEN=...` dans le `.env` de la racine.

```bash
cd chapitre-11-transports/mytravel
uvicorn server:app --reload
pytest                    # 27 passed
```

Demande : « Un vol Lyon-Lisbonne du 2027-05-02 au 2027-05-06 pour deux, et une voiture sur place ? » Tu dois voir trois offres, chacune avec sa compagnie, son vendeur, son prix par adulte et pour deux, la date où le prix a été vu, et un lien Aviasales. Puis un lien Kayak pour la voiture. Clique : la recherche s'ouvre avec tes dates et deux voyageurs.

Puis fais une expérience. Pose une question qui touche tout : « Porto, 4 jours en mai, avec hôtel, vol depuis Paris, et il me faut un passeport ? » Regarde les pastilles dans la bulle d'attente : la réponse met plus de temps, et selon le modèle, il arrive qu'un outil soit appelé deux fois ou qu'une partie de la question soit oubliée. Note ce que tu observes, on en reparle au chapitre 13.

### À toi d'abord

Ouvre `app/flights.py`. Le lien d'une offre se termine par un chiffre : `/search/PAR1212LIS16121`. Avant de lire la suite, trouve ce que dit ce dernier chiffre, et la ligne qui le change.

## On lit le code ensemble

### `city_code` et `fares` : deux appels, un jeton

<!-- code: mytravel/app/flights.py 23-43 -->
```python
def city_code(city):
    """The code that covers every airport of a city: PAR."""
    found = httpx.get(PLACES, timeout=15, params={
        "term": city, "locale": "en", "types[]": "city"}).json()
    if not found:
        raise ValueError(f"no airport found for {city}")
    return found[0]["code"]


def fares(origin, destination, depart, back=""):
    """Round trips seen lately; depart is a day or a month."""
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:  # the agent reads this and gives links instead
        raise RuntimeError("no TRAVELPAYOUTS_TOKEN in .env: real "
                           "prices unavailable")
    return httpx.get(FARES, timeout=15, params={
        "origin": city_code(origin),
        "destination": city_code(destination),
        "departure_at": depart, "return_at": back,
        "one_way": "false", "currency": "eur", "sorting": "price",
        "limit": 1000, "token": token}).json()["data"] or []
```

Travelpayouts ne connaît pas « Paris » : il connaît `PAR`, le code qui couvre tous les aéroports d'une ville (Orly, Roissy, Beauvais). `city_code` le demande à son service d'autocomplétion, public et sans jeton. Le paramètre `types[]: city` écarte les aéroports seuls : demander `CDG` raterait les vols depuis Orly.

`fares` lit les offres. Le jeton vient de l'environnement, jamais du code. S'il manque, l'erreur dit exactement quoi faire, et le middleware du chapitre 9 la transforme en message pour le modèle, qui donne alors le lien Google Flights. `departure_at` accepte un jour (`2027-05-02`) ou un mois (`2027-05`) : on s'en sert juste après. Et `or []` couvre le cas où l'API répond `"data": null`.

### `flight_offers` : l'outil que voit le modèle

<!-- code: mytravel/app/flights.py 101-117 -->
```python
@tool
def flight_offers(origin: str, destination: str, depart: str,
                  back: str, adults: int) -> str:
    """Real round-trip offers, cheapest first, each with its
    seller and the link to buy. Dates: YYYY-MM-DD.
    """
    found = fares(origin, destination, depart, back)
    title = "Aviasales, offres réelles à ces dates :"
    if not found:  # nobody looked at these days: the nearest ones
        found = around(origin, destination, depart, back, 3)
        title = ("Aucune offre vue à ces dates exactes. Offres "
                 "réelles les plus proches (départ à 3 jours "
                 "près, durée la plus proche) :")
    if not found:
        return "No offer seen near these dates. Say so."
    return "\n".join([title] + [offer(f, adults)
                                for f in found[:3]])
```

D'abord les offres aux dates exactes. Si personne n'a cherché ces jours-là, `around` cherche autour, à trois jours près. Le titre change alors pour le dire au modèle : « aucune offre à ces dates exactes, voici les plus proches ». C'est une information, pas un détail : le voyageur doit savoir qu'on lui propose le 3 mai au lieu du 2. Trois offres au plus : la moins chère, et deux pour comparer.

### `around` : les jours voisins

<!-- code: mytravel/app/flights.py 55-73 -->
```python
def around(origin, destination, start, end, shift):
    """Offers that move the whole trip at most shift days, for the
    same number of nights, or the nearest number seen: the
    cheapest of each pair of days, cheapest first."""
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    shift = timedelta(days=min(shift, MAX_SHIFT))
    low = max(first - shift, date.today() + timedelta(days=1))
    seen = [fare for month in months(low, first + shift)
            for fare in fares(origin, destination, month)]
    found = {}
    for fare in sorted(seen, key=lambda f: f["price"]):
        out = date.fromisoformat(fare["departure_at"][:10])
        back = date.fromisoformat(fare["return_at"][:10])
        gap = abs((back - out) - (last - first)).days
        if (low <= out and abs(out - first) <= shift
                and gap <= MAX_GAP):
            found.setdefault((out, back), (gap, fare))
    nearest = min((gap for gap, _ in found.values()), default=0)
    return [fare for gap, fare in found.values() if gap == nearest]
```

Je lis cette fonction en trois temps. D'abord la fenêtre : de `first - shift` à `first + shift`, sans jamais commencer avant demain (on ne vend pas de vol pour hier). Ensuite la récolte : `months` liste les mois de la fenêtre, et `fares` est appelé une fois par mois, avec `departure_at` au format `AAAA-MM` : une seule requête rapporte tout un mois d'offres.

Enfin le tri, du moins cher au plus cher. Pour chaque offre, `gap` est l'écart de durée avec le séjour demandé : 4 nuits demandées, une offre de 5 nuits a un écart de 1. `setdefault` ne garde que l'offre la moins chère de chaque paire de jours. Et la dernière ligne ne garde que l'écart le plus petit trouvé : si aucune offre ne dure exactement 4 nuits, on prend 5 plutôt que rien. Le paramètre `shift` servira encore au chapitre 20, quand le voyageur dira « je peux décaler de quelques jours ».

### `offer` : une ligne que le modèle peut citer

<!-- code: mytravel/app/flights.py 76-98 -->
```python
def seen_on(link):
    """The day a traveler saw this price: search_date=21102026."""
    day = parse_qs(urlparse(link).query)["search_date"][0]
    return f"{datetime.strptime(day, '%d%m%Y'):%Y-%m-%d}"


def offer(fare, adults):
    """One fare, as a line the model can quote."""
    # /search/PAR1212LIS16121: the last digit is the travelers.
    path, query = fare["link"].split("?", 1)
    link = f"https://www.aviasales.com{path[:-1]}{adults}?{query}"
    nights = (date.fromisoformat(fare["return_at"][:10])
              - date.fromisoformat(fare["departure_at"][:10])).days
    return (
        f"- {fare['price']} € par adulte, soit "
        f"{fare['price'] * adults} € pour {adults} : aller le "
        f"{fare['departure_at'][:16]} de {fare['origin_airport']}, "
        f"retour le {fare['return_at'][:10]} ({nights} nuits), vol "
        f"{fare['airline']} {fare['flight_number']}, "
        f"escales : {fare['transfers']} à l'aller, "
        f"{fare['return_transfers']} au retour, vendu par "
        f"{fare['gate']}, "
        f"prix vu le {seen_on(fare['link'])}. Réserver : {link}")
```

Réponse à ta question : le dernier chiffre du chemin est le nombre de voyageurs. Travelpayouts renvoie des liens pour un adulte ; `path[:-1]` retire le chiffre, `{adults}` met le bon. Le voyageur qui clique voit le prix pour son groupe. Et `seen_on` lit la date dans le paramètre `search_date` du lien : c'est le jour où un voyageur a vu ce prix.

Le texte est en français et complet : prix par adulte et total, heure de départ, aéroport, compagnie, numéro de vol, escales, vendeur, date, lien. Le modèle n'a qu'à recopier. Tout ce qu'il recopie, il ne l'invente pas.

> ⚠️ **Piège classique** — Présenter une offre vue il y a cinq jours comme un prix garanti. Le prix d'un vol bouge plusieurs fois par jour. L'outil donne la date où l'offre a été vue, et le lien ouvre la recherche à jour chez le vendeur : c'est là que le voyageur voit le prix ferme.

### Deux liens, deux façons d'encoder

<!-- code: mytravel/app/tools.py 104-113 -->
```python
def flights_url(origin, destination, depart, back, adults):
    trip = (f"Flights from {origin} to {destination} on {depart} "
            f"through {back} for {adults} adults")
    # Google reads the sentence only on its English page: hl=en.
    return ("https://www.google.com/travel/flights?hl=en&q="
            + quote(trip))


def cars_url(city, start, end):
    return f"https://www.kayak.fr/cars/{quote(city)}/{start}/{end}"
```

`booking_url` utilise `urlencode`, `flights_url` utilise `quote`. La raison tient dans la forme des adresses. Booking prend **plusieurs paramètres nommés** (`?ss=...&checkin=...`) : `urlencode` fabrique toute cette partie d'un coup à partir d'un dictionnaire. Google Flights prend **un seul paramètre**, `q`, qui contient une phrase : `quote` encode juste cette phrase. Et Kayak met la ville **dans le chemin** de l'adresse (`/cars/Lisbonne/...`) : là aussi, `quote` encode un seul morceau.

Google Flights comprend une phrase en anglais dans `q` : pas besoin de codes d'aéroport. Il y a une condition, et je l'ai apprise en cliquant. Depuis un navigateur réglé en français, Google affiche sa page en français, ignore la phrase, et ouvre son accueil vide. D'où le `hl=en` : la page s'ouvre en anglais, la recherche est faite, les prix restent en euros. Le test `test_flights_url_is_prefilled` vérifie que ce paramètre ne disparaît pas. C'est pour ça que je vérifie toujours un lien fabriqué en l'ouvrant pour de vrai, au moins une fois.

## QCM

**1.** Que contient une offre de Travelpayouts ?

- **a)** Un vol, une compagnie et un vendeur
- **b)** Un prix garanti jusqu'au départ
- **c)** Un lien pour l'acheter
- **d)** Le jour où le prix a été vu

**2.** Personne n'a cherché tes dates exactes. Que fait `flight_offers` ?

- **a)** Il estime un prix moyen
- **b)** Il cherche les offres réelles à trois jours près, de durée la plus proche
- **c)** Il le dit au modèle dans le titre de sa réponse
- **d)** Il renvoie une erreur

**3.** Pourquoi `around` appelle-t-il `fares` avec un mois plutôt qu'avec chaque jour ?

- **a)** Une seule requête rapporte les offres de tout le mois
- **b)** Travelpayouts refuse les jours
- **c)** Pour faire moins d'appels réseau
- **d)** Pour que le modèle choisisse le jour

**4.** Le jeton `TRAVELPAYOUTS_TOKEN` manque. Que voit le voyageur ?

- **a)** Un prix lu sur une page web
- **b)** Un lien Google Flights prérempli, sans prix
- **c)** Une erreur 500
- **d)** Une phrase qui dit que les prix réels ne sont pas disponibles

**5.** Pourquoi `flights_url` utilise-t-elle `quote` et pas `urlencode` ?

- **a)** Parce qu'elle encode une seule valeur, la phrase du paramètre `q`
- **b)** Parce que `urlencode` ne gère pas les accents
- **c)** Parce que `urlencode` fabrique plusieurs paramètres nommés à partir d'un dictionnaire
- **d)** Pour aller plus vite

**6.** Que coûte un outil de plus à l'agent ?

- **a)** Rien, il n'est payé que quand il est appelé
- **b)** Sa description, envoyée au modèle à chaque appel
- **c)** Un choix plus difficile entre des outils qui se ressemblent
- **d)** Une requête réseau à chaque question

**Réponses.** Q1 : a, c, d · Q2 : b, c · Q3 : a, c · Q4 : b, d · Q5 : a, c · Q6 : b, c

## Ce qu'il faut retenir

1. Un vrai prix de vol vient d'une API de prix, pas d'une page web : Travelpayouts donne des offres réelles, gratuites, avec vendeur et lien.
2. Une offre se donne avec le jour où elle a été vue. Le lien ouvre le prix ferme chez le vendeur.
3. Quand personne n'a regardé tes dates, l'outil cherche les offres réelles les plus proches, et le dit.
4. `urlencode` fabrique des paramètres nommés ; `quote` encode un seul morceau d'adresse. Un lien fabriqué se vérifie en l'ouvrant pour de vrai.
5. Chaque outil se paie à chaque appel, en tokens et en clarté. Huit, ça passe. On approche de la limite.

**Au chapitre suivant :** la météo de tes dates, en direct, et les conseils officiels aux voyageurs. Deux outils de plus, dix en tout. Et un agent qui commence vraiment à se perdre.

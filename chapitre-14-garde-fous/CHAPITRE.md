# Chapitre 14 — Garde-fous et humain dans la boucle

> **Dossier GitHub associé :** `chapitre-14-garde-fous/`

**À la fin de ce chapitre, tu sauras :**

- placer un contrôle **avant** le modèle, et un autre **après** lui ;
- refuser un numéro de carte bancaire sans refuser deux dates qui lui ressemblent ;
- retirer d'une réponse tout lien qu'aucun outil n'a renvoyé, ou qui vise un site qui n'est pas de confiance ;
- mettre un graphe LangGraph en pause avec `interrupt`, et le reprendre avec ta décision ;
- dire pourquoi une consigne dans un prompt n'est jamais un garde-fou.

## « Je te donne ma carte, réserve-moi tout »

Le jour où myTravel est en ligne, quelqu'un lui écrira ceci : « Super plan ! Ma carte c'est 4111 1111 1111 1111, exp 08/28, réserve tout. » Ce n'est pas une hypothèse, c'est ce qui arrive à tous les assistants publics. Les gens sont pressés, et ils font confiance.

Que se passe-t-il alors dans le myTravel du chapitre 13 ? Le message entre dans la conversation. Le checkpointer l'enregistre dans `mytravel.db`. Il part chez OpenRouter, puis chez le fournisseur du modèle. Et il y restera, dans chaque contexte renvoyé au modèle, tant que la conversation dure. Trois copies d'un numéro de carte, pour un service qui ne paie rien.

Le deuxième danger est plus discret. Synthèse a pour consigne de ne garder que les liens des rapports. Un jour sur cinquante, il glisse quand même un lien de sa mémoire : un site de visa payant, un domaine qui n'existe plus. Plus souvent encore, il « arrange » un vrai lien : l'outil a renvoyé `kayak.fr/cars/Lisbon/2027-06-10/2027-06-15`, la réponse affiche `kayak.com/cars/Lisbon?start=2027-06-10`. Même site, autre page. Le voyageur clique, et ne trouve pas ce qu'on lui a promis.

Ce chapitre pose trois garde-fous. Un à l'entrée, un à la sortie, et un troisième, humain : ton accord avant que myTravel prépare quoi que ce soit en ton nom.

## Avant, après, et entre les deux

Un **garde-fou** est un contrôle écrit en code, qui ne dépend pas de la bonne volonté du modèle. On en place à trois endroits.

**À l'entrée**, dans `server.py`, avant même le graphe. Si le message contient un numéro de carte, on le refuse et on sort. Il n'atteint ni le modèle ni la mémoire. Pour reconnaître une carte, une expression régulière cherche une suite d'au moins 13 chiffres, puis on applique la **formule de Luhn**, une somme de contrôle que tout vrai numéro de carte respecte. Les dates au format 2027-05-02 sont effacées avant : deux dates collées font 16 chiffres, et sans cette précaution myTravel prendrait ton voyage pour ta carte.

**À la sortie**, un nouveau nœud du graphe, `check_output`, relit la réponse de Synthèse. Chaque lien passe deux contrôles. Le premier : un outil l'a-t-il renvoyé, **tel quel** ? Pendant que les agents travaillent, le code relève chaque adresse que leurs outils ont rendue (résultats de recherche, pages lues, liens préremplis) ; c'est leur **provenance**. Le second : le site est-il dans la liste de confiance ? Un lien qui échoue à l'un des deux disparaît (le texte reste, le lien part), les autres deviennent les **sources** affichées sous la réponse.

**Entre les deux**, l'**humain dans la boucle** (*human in the loop*). Quand tu demandes « prépare la réservation », Mission met `booking=True` dans la fiche, et le graphe passe par un nœud `confirm`. Ce nœud appelle `interrupt` : LangGraph **met le graphe en pause**, enregistre son état dans le checkpointer, et renvoie une question à la page. La page affiche une carte « Oui / Non ». Ta réponse part sur `/api/confirm`, qui **reprend** le graphe exactement là où il s'était arrêté, avec ta décision.

Que prépare myTravel quand tu dis oui ? Une fiche avec trois liens remplis (vols, hôtel, voiture) et une liste de vérifications. Il ne réserve toujours rien. Pourquoi demander ton accord pour si peu ? Parce que c'est l'endroit où, un jour, tu brancheras une vraie action : envoyer un e-mail, bloquer une option chez un partenaire. La pause est en place avant que l'action soit dangereuse.

> 💡 **À retenir** — Une consigne dans un prompt est une demande. Un garde-fou est du code qui s'exécute à chaque fois. Ce qui ne doit jamais arriver se contrôle dans le code.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

| Fichier | Ce qui change |
|---|---|
| `app/guardrails.py` | NOUVEAU : `check_message` (carte refusée), `links_in` (les adresses d'un texte), `clean_answer` (liens filtrés) |
| `app/agents.py` | `run_agent` renvoie aussi les adresses rendues par ses outils, et les recopie au bas du rapport |
| `app/graph.py` | `Trip.booking`, le champ `found`, les nœuds `confirm` et `check_output` ; `stream_confirm`, et `run`, le flux commun aux deux routes |
| `app/sources.py` | `TRUSTED`, l'union de tous les sites de confiance, et `GOOGLE_FLIGHTS` |
| `server.py` | le contrôle d'entrée, la route `/api/confirm`, en flux elle aussi |
| `static/index.html` | la carte « Oui / Non », les pastilles de sources, le brouillon remplacé par la réponse vérifiée |

### Lancer le chapitre

```bash
cd chapitre-14-garde-fous/mytravel
uvicorn server:app --reload
pytest                    # 57 passed
```

Trois essais :

1. Écris « Ma carte : 4111 1111 1111 1111 » (c'est un numéro de test, il ne sert à rien). La réponse arrive instantanément : aucun modèle n'a été appelé. Regarde le terminal : aucune trace de l'appel.
2. Demande un visa pour le Japon. Sous la réponse, des pastilles grises : les sources, après filtrage.
3. Demande un plan pour Lisbonne avec des dates, puis « Prépare la réservation ». Une carte orange apparaît. Réponds « Oui » : la fiche arrive avec trois liens. Recommence et réponds « Non » : rien n'est préparé.

### À toi d'abord

Dans `app/graph.py`, trouve la fonction `confirm`. Elle s'arrête au milieu, sur `interrupt(...)`. Avant de lire la suite, essaie de répondre : quand le graphe reprend, est-ce qu'il repart de la ligne suivante, ou du début de la fonction ?

## On lit le code ensemble

Quatre idées à comprendre, une par garde-fou. Le reste du code n'est que du détail autour.

### 1. L'entrée : refuser la carte avant tout

<!-- code: mytravel/app/guardrails.py 52-70 -->
```python
def has_card_number(text):
    text = DATE.sub(" ", text)  # two dates are not a card
    for match in CARD.finditer(text):
        digits = [c for c in match.group() if c.isdigit()]
        # A card hidden in a longer run of digits still counts.
        for size in range(13, 20):
            for start in range(len(digits) - size + 1):
                if passes_luhn(digits[start:start + size]):
                    return True
    return False


def check_message(text):
    """None if the message may go on, else why it may not."""
    if has_card_number(text):
        return ("Ne m'envoie jamais un numéro de carte : myTravel "
                "ne paie rien. Tu réserves toi-même sur le site du "
                "fournisseur. Ton message n'a pas été enregistré.")
    return None
```

Lis `check_message` d'abord : il renvoie `None` si tout va bien, sinon la phrase de refus. `server.py` l'appelle **avant** le graphe. Le message refusé ne touche donc ni le modèle ni la mémoire.

`has_card_number` évite deux erreurs. Elle efface les dates, sinon deux dates collées passeraient pour une carte. Et elle teste chaque morceau de 13 à 19 chiffres, pour trouver une carte cachée dans une suite plus longue.

### 2. La sortie : un lien doit avoir une preuve

<!-- code: mytravel/app/guardrails.py 100-109 -->
```python
def clean_answer(text, found):
    """(text without the bad links, the links kept)."""
    sources = []

    # found: what the tools returned. Anything else is made up.
    def kept(url):
        if url in found and trusted(url):
            sources.append(url)
            return True
        return False
```

Toute la règle tient dans `kept` : un lien reste **seulement si** un outil l'a renvoyé (`found`) **et** si son site est de confiance (`trusted`). Le lien `kayak.com` « corrigé » de l'introduction échoue au premier test : aucun outil ne l'a renvoyé tel quel, il disparaît.

`found` est rempli dans `app/agents.py` : à chaque appel d'outil, on relève les adresses de sa réponse. Le reste de `clean_answer` sert à repérer les liens sous toutes leurs formes, même déguisés en HTML. Une seule exception à retenir : on n'accepte pas tout `google.com`, car `google.com/url?q=...` redirige n'importe où. Seuls les liens Google Flights passent.

### 3. La pause : `interrupt`

<!-- code: mytravel/app/graph.py 205-217 -->
```python

def confirm(state):
    trip = state["trip"]
    # The graph stops here and saves itself. The page shows the
    # question; /api/confirm resumes with True or False.
    approved = interrupt(
        f"Je prépare les liens de réservation pour "
        f"{trip['destination']}, du {trip['start']} au "
        f"{trip['end']}, {trip['travelers']} voyageur(s). "
        f"On y va ?")
    if not approved:
        return {"answer": "D'accord, je ne prépare rien."}
    sheet = booking_sheet(trip)
```

Réponse à ta question : à la reprise, LangGraph **relance le nœud `confirm` depuis le début**. La deuxième fois, `interrupt` ne s'arrête pas, il renvoie ta réponse (`True` ou `False`).

Retiens la conséquence : tout ce qui est écrit avant `interrupt` s'exécute deux fois. Ici, c'est une simple lecture. Un envoi d'e-mail placé là partirait deux fois.

### 4. La reprise : `Command(resume=...)`

<!-- code: mytravel/app/graph.py 273-278 -->
```python
def stream_confirm(conversation, approved):
    """The human's answer. None if no booking was waiting."""
    config = {"configurable": {"thread_id": conversation}}
    if not graph.get_state(config).interrupts:
        return None
    return run(Command(resume=approved), conversation)
```

Pour reprendre, on n'envoie pas un nouveau message : on répond à la question en attente avec `Command(resume=approved)`. S'il n'y a pas de pause, la fonction renvoie `None` **avant** tout flux, et l'API peut encore répondre un vrai 404. Sinon, la reprise passe par `run`, le même flux que pour une question : la page lit `/api/confirm` exactement comme `/api/chat`, et la question « On y va ? » arrive dans le champ `confirm` de l'événement `done`. Côté page, `static/index.html` affiche la carte « Oui / Non » et renvoie ton clic sur `/api/confirm`.

> ⚠️ **Piège classique** — Oublier que la réponse est déjà à l'écran. Avec le streaming, les mots de Synthèse arrivent dans la page **avant** que `check_output` ne les relise. Si le brouillon était mis en forme au fil de l'eau, un lien douteux serait cliquable pendant quelques secondes. D'où deux règles dans la page : le brouillon reste du texte brut (`textContent`), et l'événement `done`, qui porte la réponse vérifiée, le **remplace** entièrement. Ce qui a été filtré disparaît de l'écran.

> ⚠️ **Piège classique** — Mettre la confirmation uniquement dans la page (« Êtes-vous sûr ? » en JavaScript). N'importe qui peut appeler l'API sans passer par la page. La pause doit vivre côté serveur, dans le graphe : c'est lui qui refuse de continuer sans réponse.

## QCM

**1.** Pourquoi le contrôle de carte bancaire est-il dans `server.py`, avant le graphe ?

- **a)** Pour que le message n'atteigne jamais le modèle
- **b)** Pour qu'il ne soit jamais enregistré par le checkpointer
- **c)** Parce que le graphe ne sait pas lire de chiffres
- **d)** Pour aller plus vite

**2.** À quoi sert la formule de Luhn ici ?

- **a)** À vérifier que la carte a des fonds
- **b)** À ne pas confondre deux dates avec un numéro de carte
- **c)** À reconnaître un vrai numéro de carte
- **d)** À chiffrer le numéro

**3.** Que fait `check_output` d'un lien vers `cheap-visa.example.com` ?

- **a)** Il le garde et l'affiche en source
- **b)** Il retire le lien et garde le texte
- **c)** Il refuse toute la réponse
- **d)** Il le remplace par un lien officiel

**4.** Pourquoi n'accepte-t-on pas tout `google.com` ?

- **a)** Parce que `google.com/url?q=` redirige n'importe où
- **b)** Parce que Google est payant
- **c)** Parce que seuls les liens Google Flights fabriqués par `flights_url` sont utiles
- **d)** Parce que Google bloque les robots

**5.** Le graphe reprend après `interrupt`. Où reprend-il ?

- **a)** À la ligne qui suit `interrupt`
- **b)** Au début du nœud `confirm`, qui est relancé
- **c)** Au début du graphe
- **d)** Au nœud `check_output`

**6.** Pourquoi la pause doit-elle être côté serveur et pas seulement dans la page ?

- **a)** Parce que n'importe qui peut appeler l'API sans la page
- **b)** Parce que JavaScript ne sait pas afficher de boutons
- **c)** Parce que c'est le graphe qui doit refuser de continuer sans réponse
- **d)** Pour économiser des tokens

**7.** L'outil a renvoyé `https://www.kayak.fr/cars/Lisbon/2027-06-10/2027-06-15`. La réponse affiche `https://www.kayak.com/cars/Lisbon?start=2027-06-10`. Que se passe-t-il ?

- **a)** Le lien est gardé : Kayak est un site connu
- **b)** Le lien disparaît, parce qu'aucun outil ne l'a renvoyé tel quel
- **c)** Le lien disparaît, parce que `kayak.com` n'est pas dans `TRUSTED`
- **d)** `check_output` remplace l'adresse par la bonne

**Réponses.** Q1 : a, b · Q2 : b, c · Q3 : b · Q4 : a, c · Q5 : b · Q6 : a, c · Q7 : b, c

## Ce qu'il faut retenir

1. Un garde-fou est du code, pas une consigne : on contrôle avant le modèle et après lui.
2. Une donnée sensible est refusée avant le graphe : elle n'atteint ni le modèle ni la mémoire.
3. Un bon garde-fou ne crie pas au loup : la formule de Luhn distingue une carte de deux dates.
4. En sortie, un lien n'est gardé que si un outil l'a renvoyé tel quel et que son site est de confiance ; les liens restants deviennent les sources affichées.
5. `interrupt` met le graphe en pause dans le checkpointer ; `Command(resume=...)` le reprend en relançant le nœud depuis le début.

**Au chapitre suivant :** les garde-fous protègent le voyageur de ses erreurs et de celles du modèle. Reste un adversaire : celui qui attaque exprès. Une page web qui donne des ordres au modèle, un script qui envoie mille messages, une redirection vers ton réseau local.

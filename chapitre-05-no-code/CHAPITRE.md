# Chapitre 5 — Agents no-code : n8n, Make et les autres

> **Dossier GitHub associé :** `chapitre-05-no-code/`

**À la fin de ce chapitre, tu sauras :**

- dire pour quels cas une plateforme no-code est le bon outil, et pour lesquels elle ne l'est pas ;
- situer n8n, Make, Zapier, Flowise et Langflow les uns par rapport aux autres ;
- importer et lancer un scénario « recherche, synthèse, e-mail » dans n8n, branché sur un modèle OpenRouter ;
- écrire le même scénario en Python et comparer les deux ;
- repérer les signaux qui disent qu'il est temps de repasser au code.

## Le prototype qui a pris quarante minutes

Lundi matin, une collègue marketing te demande : « Peux-tu m'envoyer chaque semaine un résumé de ce qu'on dit de Lisbonne, pour la newsletter ? » Tu ouvres ton éditeur. Tu penses : une fonction de recherche, un appel de modèle, un envoi d'e-mail, un déclencheur hebdomadaire, un endroit où héberger le tout, une alerte quand ça plante.

Ou alors tu ouvres un navigateur, tu glisses quatre boîtes sur un écran, tu les relies par des flèches, et tu as un prototype avant le café de dix heures.

Les deux approches ont raison, à des moments différents. Les quatre chapitres précédents t'ont appris à écrire des agents. Celui-ci t'apprend **quand ne pas en écrire**, et à reconnaître le jour où le prototype glissé sur un écran doit retourner dans ton éditeur.

## Pourquoi du no-code ?

Une plateforme **no-code** (ou *low-code*) te fait construire un programme en assemblant des boîtes sur un canevas. Chaque boîte fait une chose : lire un site, appeler une API, envoyer un e-mail, appeler un modèle. Des flèches indiquent l'ordre.

Trois forces la rendent utile. D'abord la vitesse : les connecteurs vers les services courants existent déjà, avec leur écran d'authentification, et tu n'écris pas la gestion d'OAuth pour lire un agenda. Ensuite l'ouverture : une personne qui ne programme pas lit le canevas, comprend le scénario et le modifie, ce qui compte énormément quand les métiers veulent garder la main sur leur automatisation. Enfin l'exécution clé en main : déclencheur hebdomadaire, historique des exécutions, identifiants rangés dans un coffre, tout est déjà là. Ton collègue marketing te remerciera surtout pour ce dernier point, parce que personne n'a envie d'être réveillé un dimanche par un cron qui a planté.

> 💡 **À retenir** — Le no-code excelle quand le scénario est une **ligne droite de connecteurs** : déclencheur, quelques appels, un envoi. Il souffre quand la logique devient du **raisonnement** : boucles, mémoire, décisions fines.

## Panorama des plateformes

Le paysage bouge vite, et les noms de produits changent presque chaque saison. Retiens les familles plutôt que les étiquettes.

**n8n.** Une plateforme d'automatisation dont le code source est ouvert sous une licence dite *fair-code* : tu peux l'héberger toi-même gratuitement pour ton usage, avec des conditions pour la revente. Elle propose des boîtes dédiées aux agents (un nœud « AI Agent », des nœuds de modèle, de mémoire, d'outils). C'est celle de l'atelier, parce qu'on peut la lancer chez soi sans carte bancaire.

**Make** (ex-Integromat). Un service en ligne, très visuel, avec des centaines de connecteurs. Il se facture à l'usage (par opération exécutée). On ne l'héberge pas soi-même. Les scénarios se construisent sur un canevas proche de n8n.

**Zapier.** Le plus ancien du genre : des enchaînements « quand ceci arrive, fais cela ». Il propose des étapes d'IA et des agents, dont les noms changent régulièrement. Très simple, un peu moins souple pour les scénarios à branches.

**Flowise et Langflow.** Autre famille : des canevas **spécialisés dans les applications de modèles** (chaînes, agents, bases vectorielles), open source, qui reposent sur des bibliothèques comme LangChain. Tu y assembles ce que tu as codé aux chapitres 2 et 3, en boîtes.

| Besoin | Plutôt |
|---|---|
| Brancher beaucoup de services, hébergement chez soi | n8n |
| Prototype sans rien installer, équipe métier | Make ou Zapier |
| Application de modèle (RAG, agent) en boîtes | Flowise ou Langflow |
| Contrôle total, tests, déploiement maîtrisé | du code (chapitres 1 à 4) |

## Pratique : qui fait quoi, et comment le lancer

Ce chapitre a deux visages : un workflow n8n, que tu dessines et importes, et son équivalent en Python. Le dossier contient les deux.

### Les fichiers et leur rôle

```text
chapitre-05-no-code/
├── workflows/
│   └── research-summary-email.n8n.json
│                  ← le workflow n8n à importer
├── docker-compose.yml  ← lance n8n chez toi
├── pipeline.py  ← le même scénario en Python
├── main.py      ← point d'entrée de la version Python
├── modele.py    ← la prise : client OpenRouter
└── tests/       ← testent le JSON, sans n8n
```

### Lancer le programme

Pour la version Python, l'installation du chapitre 1 suffit :

```bash
cd chapitre-05-no-code
python modele.py          # 1. modèles gratuits
python main.py            # 2. sujet par défaut : Lisbon
python main.py "Kyoto"    #    ou un autre sujet
pytest                    # 3. 12 tests, hors ligne
```

Sans `SMTP_HOST`, l'e-mail est écrit dans `outbox/summary.eml` : aucun courrier ne part par surprise. Pour la version n8n, il faut Docker :

```bash
docker compose up -d      # puis ouvre http://localhost:5678
docker compose down       # arrêt ; workflows conservés
```

Dans n8n : *Workflows*, puis *Import from file*, et choisis le fichier `.n8n.json`. Il te reste à créer deux identifiants, un « Header Auth » pour OpenRouter et un « SMTP ». L'atelier plus bas détaille ces étapes.

### Les cinq détails à comprendre avant de lire le code

1. **Le workflow est un fichier JSON.** C'est pour cela qu'on peut le tester sans n8n : structure, connexions, absence de secret.
2. **Aucune clé dans le fichier.** Il ne contient que des références d'identifiants, à renseigner dans n8n.
3. **La boîte « Found Something? » est un `if`.** Rien trouvé, rien envoyé : une ligne en Python, une boîte sur le canevas.
4. **`deliver` écrit un `.eml` par défaut.** L'envoi réel n'a lieu que si `SMTP_HOST` est défini.
5. **Chaque boîte du canevas a son équivalent en code.** Lire les deux côte à côte montre ce que le no-code masque.

## L'atelier : recherche, synthèse, e-mail dans n8n

Le scénario : on cherche un sujet sur Wikipedia, on demande à un modèle de le résumer en deux phrases, on envoie le résumé par e-mail. Si la recherche ne trouve rien, on n'envoie rien.

Six boîtes, dans l'ordre :

1. **Manual Trigger** : le déclencheur, un clic.
2. **Set Topic** : fixe le sujet (« Lisbon »).
3. **Search Wikipedia** : appelle l'API de résumé de Wikipedia.
4. **Found Something?** : une boîte `IF`. Si la recherche renvoie un texte, on continue.
5. **Summarize with OpenRouter** : appelle le modèle.
6. **Send Email** : envoie le résumé.

Pour le lancer chez toi :

```bash
cd chapitre-05-no-code
docker compose up -d        # démarre n8n sur http://localhost:5678
```

À la première ouverture, n8n te demande de créer un compte local. Puis : **Workflows**, **Import from file**, et choisis `workflows/research-summary-email.n8n.json`. Le canevas affiche les six boîtes déjà reliées.

> ⚠️ **Piège classique** — Les nœuds n8n changent de version et leurs réglages aussi. Je n'ai pas pu rejouer l'import du fichier du livre sur toutes les versions de n8n. Si l'import râle sur un nœud, ne perds pas de temps : recrée la boîte à la main avec la liste ci-dessus et les réglages que décrit le fichier. Un scénario no-code se reconstruit en dix minutes, c'est aussi sa qualité.

> ⚠️ **Piège classique** — Dans n8n, un champ qui commence par `=` contient une *expression* (du code évalué), un champ sans `=` contient du texte brut. Oublier le `=` devant `{{ $json.extract }}` envoie la chaîne `{{ $json.extract }}` telle quelle au modèle. Si le résumé parle de « double accolade », c'est ça.

### Brancher le modèle, sans clé dans le fichier

La boîte 5 est un simple appel HTTP vers `https://openrouter.ai/api/v1/chat/completions`, avec un corps JSON : le même dialecte que dans tout le livre. Le modèle est écrit dans le corps de la requête :

```text
model: google/gemma-4-31b-it:free
messages: [ système : « Tu résumes en 2 phrases. »,
            utilisateur : <le texte trouvé> ]
```

La clé, elle, **n'est pas dans le fichier**. Le workflow référence un identifiant (*credential*) que tu crées dans n8n : **Credentials**, **Header Auth**, avec le nom `Authorization` et la valeur `Bearer sk-or-...`. n8n range cela dans son coffre. Le fichier reste partageable : un des tests vérifie qu'il ne contient jamais `sk-or-`.

> 💡 **À retenir** — Un secret ne se range jamais dans un fichier de scénario. On met dans le fichier un *nom* d'identifiant, et la valeur dans le coffre de la plateforme. C'est ce qui permet de versionner et de partager le workflow sans risque.

Même principe pour l'envoi : crée un identifiant **SMTP** avec tes paramètres de messagerie. Pour tester sans envoyer de vrai message, un serveur de test local (comme MailHog) évite de spammer qui que ce soit.

C'est ici que le no-code montre son intérêt. Pour utiliser un autre modèle (OpenAI, Anthropic, un modèle local derrière une API compatible), tu changes une URL et un identifiant. Le livre garde toutefois sa règle : même ici, le modèle passe par OpenRouter. Pour un modèle local, n8n propose des nœuds dédiés (Ollama, par exemple), qui conviennent à un prototype sans réseau.

### Le même scénario en Python

Le dossier contient `pipeline.py`, qui fait exactement la même chose en code. Les boîtes deviennent des fonctions. La recherche d'abord :

<!-- code: pipeline.py 1-34 -->
```python
"""The same scenario as the n8n workflow, written in Python.

Search -> summarize -> email. Same boxes, same order. Reading both
side by side shows what a no-code platform gives you (a canvas,
connectors, credential screens) and what it hides (every line
below is yours to change).
"""

import json
import os
import smtplib
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path

from modele import MODEL, get_client

WIKIPEDIA = "https://en.wikipedia.org/api/rest_v1/page/summary/"
USER_AGENT = "agentia-book/1.0 (github.com/btecsec)"


def fetch_summary(topic):
    """Box 1: search. The Wikipedia summary, or '' if none."""
    title = urllib.parse.quote(topic.strip().replace(" ", "_"))
    request = urllib.request.Request(
        WIKIPEDIA + title, headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as reply:
            return json.load(reply).get("extract") or ""
    except OSError:
        # No page, no network: the pipeline stops cleanly later.
        return ""
```

Une page introuvable ou un réseau coupé donnent une chaîne vide, pas une exception : la suite décidera quoi en faire. Puis la synthèse, avec le client du chapitre 1 :

<!-- code: pipeline.py 37-48 -->
```python
def summarize(text, client=None, model=MODEL):
    """Box 2: summarize with the model, in two sentences."""
    client = client or get_client()
    reply = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "Summarize travel facts in 2 sentences."},
            {"role": "user", "content": text},
        ],
    )
    return reply.choices[0].message.content or ""
```

Puis l'e-mail, construit puis livré :

<!-- code: pipeline.py 51-80 -->
```python
def build_email(subject, body, to, sender):
    """Box 3: build the email."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to
    message.set_content(body)
    return message


def deliver(message, outbox=Path("outbox")):
    """Box 4: send through SMTP, or save an .eml file if none set.

    Saving a file is the safe default: a tutorial must never send
    a real email by surprise.
    """
    host = os.environ.get("SMTP_HOST")
    if host:
        port = int(os.environ.get("SMTP_PORT", 587))
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(
                os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"]
            )
            smtp.send_message(message)
        return None
    outbox.mkdir(exist_ok=True)
    path = outbox / "summary.eml"
    path.write_bytes(bytes(message))
    return path
```

`deliver` envoie par SMTP si `SMTP_HOST` est défini et, sinon, **écrit un fichier `.eml`** dans `outbox/`. Ce choix par défaut est volontaire : un tutoriel ne doit jamais envoyer de courrier par surprise. Les identifiants SMTP viennent de l'environnement, comme la clé du modèle : jamais dans le code.

Enfin, le scénario entier :

<!-- code: pipeline.py 83-100 -->
```python
def run(topic, to="you@example.com", client=None,
        outbox=Path("outbox")):
    """The whole scenario. Returns the saved path, or None.

    The guard the n8n workflow draws as an IF box is one line here:
    nothing found, nothing sent.
    """
    research = fetch_summary(topic)
    if not research:
        return None
    summary = summarize(research, client=client)
    message = build_email(
        subject=f"Your summary: {topic}",
        body=summary,
        to=to,
        sender="mytravel@example.com",
    )
    return deliver(message, outbox=outbox)
```

Lis ces lignes : c'est le canevas n8n, en texte. Le `if not research: return None` est la boîte `IF`. Il reste le point d'entrée :

<!-- code: main.py -->
```python
"""Run chapter 5:  python main.py [topic]

Runs the Python version of the n8n scenario. The email is saved in
outbox/summary.eml unless SMTP_HOST is set.
"""

import sys

from openai import RateLimitError

from pipeline import run


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "Lisbon"
    path = run(topic)
    if path is None:
        print(f"Nothing found for {topic!r}: no email produced.")
    else:
        print(f"Email saved in {path}")


if __name__ == "__main__":
    try:
        main()
    except RateLimitError:
        # Free quotas are shared by everyone: it is not your code.
        sys.exit("The model is saturated (429). Wait a minute, or "
                 "change MODELE in .env (python modele.py).")
```

Lance `python main.py` :

```text
Email saved in outbox/summary.eml
```

Ouvre le fichier : le résumé de Lisbonne est dedans.

## Ce que le no-code ne sait pas (bien) faire

Le prototype a tenu quarante minutes. Voyons où il casse. Voici ce que j'ai rencontré, ou ce que tu rencontreras.

**Les boucles et le raisonnement.** Pour « cherche, lis le résultat, décide s'il faut chercher encore », il faut une boucle avec condition d'arrêt, exactement ce que LangGraph fait en trois lignes. Sur un canevas, tu empiles des boîtes `IF` et `Loop`, et le dessin devient illisible dès la troisième branche. Les nœuds « AI Agent » règlent une partie du problème en cachant la boucle, mais retrouvent la limite du chapitre 2 : tu ne vois plus ce qui se passe.

**La mémoire.** Garder le fil d'une conversation, se souvenir d'un voyageur d'une semaine sur l'autre : possible avec des nœuds de mémoire, mais configuré dans une boîte, pas dans une structure que tu testes.

**Le coût.** Les plateformes en ligne facturent à l'opération ou à l'exécution. Un agent qui boucle consomme des dizaines d'opérations pour une question. L'hébergement chez soi supprime la facture de la plateforme, pas celle du modèle, et ajoute ton temps d'exploitation.

**La dépendance au fournisseur** (*vendor lock-in*). Un scénario Make ne s'exporte pas vers n8n. Le format est propriétaire. Un fichier JSON n8n, lui, se versionne dans Git, mais ne tourne que sur n8n.

**L'observabilité.** Tu as un historique d'exécutions, c'est précieux. Tu n'as pas de tests automatiques, pas de comparaison de deux versions du prompt, pas de traces fines du raisonnement. Les chapitres sur l'évaluation et l'observabilité traitent exactement de ce qui manque.

**Le travail à plusieurs.** Deux personnes qui modifient le même canevas sans revue de code : c'est ainsi que des automatisations métier se mettent à envoyer de faux e-mails un vendredi soir.

> ⚠️ **Piège classique** — Passer en production un prototype no-code « parce qu'il marche ». Il marche sur le cas heureux. Avant de lui confier une tâche qui touche de vrais clients ou de l'argent, pose-toi la question : qui est prévenu quand il plante, et comment je teste une modification avant de l'activer ?

## Quand repasser au code

Voici les signaux qui me font sortir de la plateforme. Un seul suffit parfois, deux ou trois ensemble ne laissent pas de doute.

| Signal | Passer à |
|---|---|
| Le scénario a une vraie boucle ou une décision fine | LangGraph (chapitre 3) |
| Plusieurs rôles qui se passent un document | CrewAI (chapitre 4) |
| Un agent avec outils et mémoire à tester | LangChain (chapitre 2) |
| Le coût par exécution devient significatif | du code, sur ton infrastructure |
| Tu veux des tests automatiques, des revues de code, du CI | du code |
| Les données sont sensibles et doivent rester chez toi | du code, ou n8n auto-hébergé |

> 💡 **À retenir** — Le prototype no-code sert à valider l'idée avec le métier. Le code sert à la rendre fiable. Les deux ne se font pas concurrence : ils se suivent.

Dans la pratique, tu fais les deux dans l'ordre. Quand l'idée a tenu sur le canevas, tu réécris le noyau en code, comme avec `pipeline.py`. La plateforme garde le rôle de colle : le déclencheur, l'envoi, la surveillance.

## QCM

**1.** Où une plateforme no-code excelle-t-elle ?

- **a)** Un prototype monté vite
- **b)** Une équipe non développeuse
- **c)** Une boucle avec raisonnement fin
- **d)** Un scénario en ligne droite de connecteurs

**2.** Qu'est-ce qui ne doit jamais figurer dans un workflow exporté ?

- **a)** Les noms des nœuds
- **b)** Les clés d'API
- **c)** Les mots de passe
- **d)** Les flèches entre nœuds

**3.** Ton scénario envoie un e-mail vide quand la recherche ne trouve rien. Que manque-t-il ?

- **a)** Un nœud de mémoire
- **b)** Une boucle `Loop`
- **c)** Une boîte `IF` après la recherche
- **d)** Un second modèle

**4.** Quels signaux disent de repasser au code ?

- **a)** Le besoin de tests automatiques
- **b)** Un coût par exécution devenu significatif
- **c)** Un déclencheur simple
- **d)** Une vraie boucle ou une décision fine

**5.** Qu'est-ce que le *vendor lock-in* ?

- **a)** Le verrouillage d'un canevas par un collègue
- **b)** Le chiffrement des clés
- **c)** Le quota gratuit d'un modèle
- **d)** La dépendance au fournisseur : un scénario Make ne s'exporte pas vers n8n

**Réponses.** Q1 : a, b, d · Q2 : b, c · Q3 : c · Q4 : a, b, d · Q5 : d

## Ce qu'il faut retenir
1. Une plateforme no-code assemble des boîtes sur un canevas. Elle excelle pour un scénario en ligne droite de connecteurs, vite, et pour des équipes non développeuses.
2. n8n (auto-hébergeable, fair-code), Make et Zapier (services en ligne), Flowise et Langflow (canevas pour applications de modèles) répondent à des besoins différents.
3. Un modèle se branche dans une boîte HTTP vers OpenRouter. La clé vit dans un identifiant du coffre de la plateforme, jamais dans le fichier du scénario.
4. Les limites : boucles et raisonnement illisibles, mémoire fragile, coût à l'opération, verrouillage par le fournisseur, peu de tests et de traces.
5. Prototype sur le canevas, réécris le noyau en code dès que la logique devient du raisonnement ou que tu as besoin de tests, de revue et de contrôle des coûts.

**Au chapitre suivant :** la partie fondamentale est terminée. Tu sais écrire un agent à la main, avec LangChain, avec LangGraph, à plusieurs agents avec CrewAI, et tu sais quand préférer un canevas. Il est temps d'attaquer un vrai projet : myTravel, un assistant de voyage complet. On commence par ce que tout projet sérieux exige avant la première ligne de code : des spécifications.

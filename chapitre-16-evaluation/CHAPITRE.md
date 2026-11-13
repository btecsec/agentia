# Chapitre 16 — Évaluer myTravel

> **Dossier GitHub associé :** `chapitre-16-evaluation/`

**À la fin de ce chapitre, tu sauras :**

- distinguer ce que les tests vérifient (la logique) de ce qu'une évaluation mesure (la qualité) ;
- écrire des cas d'évaluation à partir des règles de la spécification ;
- écrire des contrôles automatiques simples, qui ne se contredisent jamais ;
- savoir quels agents ont travaillé sur une réponse, et pourquoi c'est la première chose à vérifier ;
- rejouer l'évaluation après chaque changement de prompt ou de modèle.

## « Ça a l'air mieux »

Tu changes une phrase du prompt de l'agent Administration. Tu poses ta question préférée, la réponse te semble meilleure. Tu commites. Trois jours plus tard, quelqu'un remarque que myTravel ne cite plus aucune source pour la santé. La phrase que tu as changée disait « focus on visas », et l'agent a cessé de chercher le reste.

« Ça a l'air mieux » sur une question, c'est une impression. Pour savoir si un changement améliore myTravel, il faut le mesurer sur **plusieurs** questions, toujours les mêmes, avec des critères écrits avant de regarder les réponses.

Les 62 tests du dossier ne servent à rien ici, et c'est normal. Ils remplacent le modèle par un faux qui répond toujours pareil. Ils prouvent que la **logique** est juste : le graphe va au bon nœud, la carte bancaire est refusée. Ils ne disent rien de la **qualité** des réponses du vrai modèle. Pour ça, il faut une évaluation.

## Des cas, des contrôles, un score

Une **évaluation**, c'est trois choses.

**Des cas.** Une question réelle et ce qu'une bonne réponse doit contenir. Ils viennent tout droit de la spécification du chapitre 6 : chaque règle d'acceptation devient un ou plusieurs cas. « Une règle de visa porte un lien officiel » devient : la question sur le Japon doit citer un site `gouv.fr`.

**Des contrôles.** myTravel en a trois, volontairement bêtes :

- les **agents attendus** ont-ils travaillé ? Une question de visa doit passer par Administration ;
- les **sources attendues** sont-elles citées ? Au moins un lien vers tel domaine ;
- les **mots attendus** sont-ils dans la réponse ? « passeport » pour une question d'entrée.

Pourquoi si bêtes ? Parce qu'un contrôle bête ne se trompe jamais sur lui-même. On aurait pu demander à un autre modèle de noter les réponses de 1 à 10 (on appelle ça un *LLM juge*). C'est utile pour juger le ton ou la clarté, mais le juge se trompe aussi, et il ne note pas deux fois pareil. Pour des faits vérifiables (un agent, un domaine, un mot), un `if` suffit et ne varie pas.

**Un score.** Le nombre de cas réussis. On le relève avant un changement, puis après. S'il baisse, le changement repart.

Pour le premier contrôle, il faut savoir qui a travaillé. C'est la nouveauté du graphe dans ce chapitre : chaque nœud ajoute son nom à une liste `steps`, que l'API renvoie avec la réponse. Mission, Administration, Synthèse. Une question de visa qui passerait par Hôtel trahit une erreur de Mission, même si la réponse finale a l'air correcte.

> 💡 **À retenir** — Les tests vérifient ton code avec un faux modèle. L'évaluation mesure les vrais agents, avec le vrai modèle, sur de vraies questions. Il te faut les deux.

## Pratique : qui fait quoi, et comment le lancer

### Les fichiers et leur rôle

| Fichier | Rôle |
|---|---|
| `app/evaluation.py` | NOUVEAU : `check_case`, les trois contrôles |
| `evaluate.py` | NOUVEAU : rejoue chaque cas sur les vrais agents, affiche le score |
| `data/eval_cases.json` | NOUVEAU : six cas, tirés de la spécification |
| `app/graph.py` | chaque nœud ajoute son nom à `steps` |
| `app/agents.py` | `run_agent` renvoie aussi les outils appelés |
| `server.py` | la réponse refusée (carte bancaire) renvoie aussi `steps` |

### Lancer le chapitre

```bash
cd chapitre-16-evaluation/mytravel
pytest                    # 70 passed : la logique
python evaluate.py        # la qualité, avec ta clé
```

`evaluate.py` utilise ta vraie clé et ton quota : six cas, de trois à dix appels au modèle chacun. Avec un modèle gratuit, compte plusieurs minutes, et attends-toi à un 429 si le quota du jour est presque épuisé. Tu verras quelque chose comme :

```text
PASS Je suis français. Ai-je besoin d'un visa pour aller au…
PASS Quel temps fera-t-il à Lisbonne la semaine prochaine ?
FAIL Est-ce que le Pérou est sûr pour un voyageur seul ?
     - agents not called: ['Risque']
...
5/6 cases passed
```

Puis fais l'expérience qui donne tout son sens au chapitre : change le modèle dans `.env` (prends un des modèles gratuits que liste `python -m app.modele`), et relance. Le score change. Tu as maintenant un chiffre pour comparer deux modèles, au lieu d'une impression.

### À toi d'abord

Ouvre `data/eval_cases.json` et ajoute un cas à toi : une question que tu poserais vraiment avant un voyage, avec ce que la réponse doit contenir. Relance `python evaluate.py`.

## On lit le code ensemble

### Je commence par les cas

Pour comprendre une évaluation, je ne commence pas par le code, je commence par les **cas**. Ce sont eux qui disent ce que « bon » veut dire.

```json
{
  "question": "Je suis français. Ai-je besoin d'un visa…",
  "agents": ["Administration"],
  "must_cite": ["gouv.fr"],
  "must_say": ["passeport"]
}
```

Je remarque ce qui n'y est **pas** : la réponse exacte. On ne vérifie pas « il ne faut pas de visa pour moins de 90 jours », parce que cette règle peut changer, et le cas deviendrait faux le jour où la règle change. On vérifie ce qui fait une bonne réponse quelle que soit la règle : le bon agent, une source officielle, le mot qui prouve qu'il a parlé du sujet.

### `check_case` : trois contrôles, une liste

<!-- code: mytravel/app/evaluation.py 9-23 -->
```python
def check_case(case, reply):
    """The list of problems of one reply. Empty means passed."""
    problems = []
    called = {step.split(" (")[0] for step in reply["steps"]}
    missing = set(case.get("agents", [])) - called
    if missing:
        problems.append(f"agents not called: {sorted(missing)}")
    for site in case.get("must_cite", []):
        if not any(site in url for url in reply["sources"]):
            problems.append(f"no source from {site}")
    answer = reply["answer"].lower()
    for word in case.get("must_say", []):
        if word.lower() not in answer:
            problems.append(f"does not say {word!r}")
    return problems
```

La fonction renvoie la **liste des problèmes**, pas un vrai ou faux. Un cas raté dit pourquoi il a raté, et c'est ce qui te dit quoi corriger : « agents not called » pointe vers le prompt de Mission, « no source from » vers un spécialiste ou vers la recherche.

`step.split(" (")[0]` retire la parenthèse des outils : `"Météo (weather)"` redevient `"Météo"`. La soustraction d'ensembles, ligne suivante, est le genre de ligne que j'aime : `set(attendus) - set(obtenus)`, c'est mot pour mot « ceux qu'on attendait et qu'on n'a pas eus ». `case.get("agents", [])` permet d'écrire un cas sans tous les champs.

`site in url` est une comparaison de sous-chaîne, et tu te souviens du chapitre 9 : c'est précisément ce qu'on avait interdit pour la sécurité. Ici, c'est acceptable : les sources ont déjà été filtrées par `check_output`, et on veut juste savoir si l'une d'elles vient de `gouv.fr`, sans lister tous les sous-domaines.

### `evaluate.py` : une conversation neuve par cas

<!-- code: mytravel/evaluate.py 20-31 -->
```python
def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    passed = 0
    for case in cases:
        conversation = uuid.uuid4().hex
        reply = ask_mytravel(case["question"], conversation)
        problems = check_case(case, reply)
        passed += not problems
        print("PASS" if not problems else "FAIL", case["question"])
        for problem in problems:
            print("     -", problem)
    print(f"\n{passed}/{len(cases)} cases passed")
```

`uuid.uuid4().hex` donne un identifiant neuf à chaque cas. Sans lui, tous les cas partageraient une conversation, et le deuxième cas verrait la question du premier : un plan pour Lisbonne contaminé par le visa japonais. Une évaluation dont les cas se parlent ne mesure plus rien.

`passed += not problems` est un raccourci Python : une liste vide est fausse, `not []` vaut `True`, qui compte pour 1. `ask_mytravel` lit jusqu'au bout le même flux que la page, et garde le dernier événement, `done` : on évalue **les vrais agents**, par la même porte que les voyageurs.

### Les `steps` dans le graphe

Dans `app/graph.py`, chaque nœud renvoie désormais un nom en plus de son travail, par exemple `{"trip": ..., "steps": ["Mission"]}`, et les agents renvoient leur libellé (`AGENTS[name]["label"]`), suivi entre parenthèses des outils qu'ils ont appelés : `"Hôtel (search_hotels, hotel_links)"`. Ces noms, `run_agent` les lit dans `app/agents.py` : chaque message du modèle porte ses `tool_calls`, il suffit de les relever. `dict.fromkeys` garde chaque nom une fois, dans l'ordre. Mission vérifie qui a travaillé ; toi, tu vois avec quoi. Le champ `steps` utilise le même réducteur `fresh` que les rapports : les agents parallèles s'ajoutent, et chaque question repart d'une liste vide.

> ⚠️ **Piège classique** — Évaluer une seule fois, au début, et ne plus jamais relancer. Une évaluation sert à comparer : avant et après un changement de prompt, de modèle, de bibliothèque. Relance-la à chaque fois, et garde le score dans le message de commit.

## QCM

**1.** Pourquoi les tests du dossier ne mesurent-ils pas la qualité de myTravel ?

- **a)** Parce qu'ils utilisent un faux modèle qui répond toujours pareil
- **b)** Parce qu'ils vérifient la logique, pas les réponses du vrai modèle
- **c)** Parce qu'ils sont trop peu nombreux
- **d)** Parce qu'ils tournent sans réseau

**2.** Pourquoi un cas ne vérifie-t-il pas la réponse exacte sur un visa ?

- **a)** Parce que la règle peut changer, et le cas deviendrait faux
- **b)** Parce que le modèle ne répond jamais deux fois pareil
- **c)** Parce que JSON ne sait pas stocker de phrase
- **d)** Parce qu'on vérifie ce qui fait une bonne réponse : l'agent, la source, le sujet

**3.** Le cas sur le Pérou échoue avec « agents not called: ['Risque'] ». Où chercher ?

- **a)** Dans le prompt de l'agent Mission, qui choisit les agents
- **b)** Dans `check_case`
- **c)** Dans la page web
- **d)** Dans la liste `agents` de la fiche `Trip`

**4.** Pourquoi chaque cas a-t-il sa propre conversation ?

- **a)** Pour que les cas ne se contaminent pas
- **b)** Pour aller plus vite
- **c)** Parce que le checkpointer garderait sinon les questions précédentes
- **d)** Parce que l'API l'exige

**5.** Quel avantage un contrôle « bête » (un `if`) a-t-il sur un LLM juge ?

- **a)** Il ne varie pas d'un lancement à l'autre
- **b)** Il juge mieux le ton
- **c)** Il ne se trompe pas sur des faits vérifiables
- **d)** Il est gratuit

**Réponses.** Q1 : a, b · Q2 : a, d · Q3 : a, d · Q4 : a, c · Q5 : a, c, d

## Ce qu'il faut retenir

1. Les tests vérifient la logique avec un faux modèle ; l'évaluation mesure les vrais agents avec le vrai modèle.
2. Un cas d'évaluation vient d'une règle de la spécification, et vérifie ce qui fait une bonne réponse, pas une réponse mot pour mot.
3. Des contrôles simples (agents, sources, mots) ne se contredisent jamais ; un LLM juge sert pour ce qui ne se vérifie pas avec un `if`.
4. Savoir quels agents ont travaillé est la première chose à contrôler : une bonne réponse par le mauvais chemin est une chance, pas une qualité.
5. On évalue avant et après chaque changement, et on compare les scores.

**Au chapitre suivant :** l'évaluation dit qu'un cas échoue. Elle ne dit pas ce qui s'est passé à l'intérieur. Quel agent a cherché quoi, combien de temps, avec quel résultat ? On rend myTravel observable.

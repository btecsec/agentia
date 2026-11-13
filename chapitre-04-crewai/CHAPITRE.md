# Chapitre 4 — CrewAI : des agents par rôle

> **Dossier GitHub associé :** `chapitre-04-crewai/`

**À la fin de ce chapitre, tu sauras :**

- décrire des agents avec un rôle, un but et une histoire (`role`, `goal`, `backstory`) ;
- enchaîner des tâches qui se transmettent leurs résultats (`Task`, `context`) ;
- choisir entre un processus séquentiel et un processus hiérarchique ;
- comparer CrewAI et LangGraph sur le même travail, et dire lequel choisir ;
- tester un groupe d'agents sans clé d'API.

## Le rédacteur qui a ajouté un tramway

J'ai lancé trois agents sur un paragraphe à propos de Lisbonne. Le chercheur a rendu quatre faits : 550 000 habitants, des tramways sur des collines escarpées, les pasteis de nata, 290 jours de soleil par an. Le rédacteur a écrit son texte. Il y glissait un détail : le « tram 28 », qui monte sur des câbles.

Le tram 28 existe, c'est même le plus célèbre de la ville. Mais il ne figurait pas dans la recherche. Le troisième agent, le vérificateur, a relu le paragraphe contre les faits, a trouvé le détail non sourcé et l'a supprimé. Le texte final disait simplement « les tramways ».

Personne n'a écrit de règle « supprime le tram 28 ». Chaque agent avait un métier, et le troisième avait pour mission de ne rien laisser passer qui ne vienne pas de la recherche. Le résultat est sorti de la façon dont on a découpé le travail.

C'est l'idée de **CrewAI** : au lieu de dessiner un chemin, tu composes un **groupe d'agents**, un *crew*. Tu décris des métiers, tu distribues des tâches, et les rôles font le reste.

## La philosophie : des métiers, pas des étapes

CrewAI est un framework pensé pour faire travailler plusieurs agents ensemble. Sa promesse tient en une phrase : décris les gens, pas la tuyauterie. Imagine que tu montes une petite rédaction : tu n'écris pas le chemin de chaque article, tu embauches un enquêteur, une plume et un relecteur pointilleux, puis tu leur dis qui passe le texte à qui.

Trois objets suffisent pour démarrer.

L'**Agent** est un personnage. Il a un **rôle** (« Chercheur voyage »), un **but** (« collecter des faits exacts sur {city} ») et une **histoire** (*backstory*, « tu es méticuleux, tu n'avances jamais un fait que ton outil ne t'a pas donné »). Ces trois champs sont recopiés dans le prompt envoyé au modèle. Ils ne sont pas décoratifs : ils orientent ses réponses.

La **Task** (tâche) est un travail à faire : une description, un résultat attendu (`expected_output`), l'agent responsable. Une tâche peut recevoir les résultats d'autres tâches via `context`.

Le **Crew** (équipage) est le groupe d'agents : la liste des agents, la liste des tâches, et le **processus** qui dit comment elles s'enchaînent.

Pourquoi CrewAI plutôt que LangGraph pour ce chapitre ? Parce que le travail s'y prête : produire un contenu en passant un texte de main en main, du chercheur au vérificateur, est exactement un métier par étape. Le framework sait le dire en trente lignes lisibles par quelqu'un qui ne programme pas. Pour un flux avec des boucles et des pauses, LangGraph garde l'avantage, et on y revient plus bas.

> 💡 **À retenir** — CrewAI décrit des agents par rôles. LangGraph décrit un chemin par nœuds et flèches. Même travail possible dans les deux, mais l'un se lit comme un organigramme, l'autre comme un schéma de circulation.

### Installation : CrewAI et Python 3.13

Un point pratique avant de coder. CrewAI ne tourne pas encore sur Python 3.14, au moment où ces lignes sont écrites. Si ton environnement du livre est en 3.14 (`python --version`), crée-en un second pour ce chapitre. Place-toi dans le dossier du chapitre (`requirements.txt` y est) :

```bash
cd chapitre-04-crewai
```

Puis :

```bash
py -3.13 -m venv .venv-crewai          # Windows
.venv-crewai\Scripts\activate
pip install -r requirements.txt
```

Le `requirements.txt` du chapitre contient `crewai>=1.15`. Sur Python 3.14 l'installation échoue : c'est pour cela qu'on crée un environnement en 3.13. Le `requirements.txt` de la racine, lui, ignore `crewai` sur 3.14 pour ne pas bloquer les autres chapitres.

> ⚠️ **Piège classique** — Derrière certains antivirus ou proxys d'entreprise, l'appel au modèle échoue avec `CERTIFICATE_VERIFY_FAILED`. Python ne trouve pas le certificat de l'intercepteur. Le correctif : pointer la variable d'environnement `SSL_CERT_FILE` vers le fichier de certificats fourni par l'outil (chez moi, celui de mon antivirus). Ce n'est pas un bug de CrewAI.

## Pratique : qui fait quoi, et comment le lancer

Un seul fichier de logique dans ce chapitre. Avant de le lire, voici comment le dossier s'organise.

### Les fichiers et leur rôle

```text
chapitre-04-crewai/
├── main.py    ← point d'entrée : lance les agents sur « Lisbon »
├── crew.py    ← agents, outil, tâches, équipage
├── modele.py  ← la prise : modèle CrewAI pointé sur OpenRouter
└── tests/     ← modèle scripté, sans clé d'API
```

### Lancer le programme

Python 3.13 ou plus ancien est nécessaire, comme expliqué plus haut. Le chapitre a son propre `requirements.txt` et son propre environnement :

```bash
cd chapitre-04-crewai
py -3.13 -m venv .venv-crewai   # Windows
.venv-crewai\Scripts\activate
# macOS / Linux :
# python3.13 -m venv .venv-crewai
# source .venv-crewai/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env      # puis colle ta clé OpenRouter
```

Puis, toujours dans le dossier du chapitre :

```bash
python modele.py   # 1. modèles gratuits capables d'outils
python main.py     # 2. les agents, rôle par rôle
pytest             # 3. 13 tests, sans clé ni réseau
```

Trois agents font plusieurs appels de modèle par exécution : surveille ton quota gratuit. La sortie de `main.py` est montrée plus bas.

### Les cinq détails à comprendre avant de lire le code

1. **Un agent, c'est un personnage.** Rôle, but et histoire sont du texte que le modèle lit comme consigne.
2. **Une tâche, c'est un travail précis.** Une description, un résultat attendu, un agent responsable.
3. **`context` fait circuler l'information.** Le rédacteur ne voit les faits que parce que sa tâche les reçoit.
4. **Le processus fixe l'ordre.** Séquentiel : l'ordre de la liste. Hiérarchique : un manager décide, au prix d'appels en plus.
5. **L'outil ne connaît que deux villes.** Les données sont fixes, donc le chercheur ne peut rien inventer sans que cela se voie.

## Les agents : un rôle, un but, une histoire

Voici les agents du chapitre, dans `crew.py`. Les faits, l'outil, puis les trois agents :

<!-- code: crew.py 1-60 -->
```python
"""A content team with CrewAI: researcher, writer, reviewer.

CrewAI thinks in ROLES, not in graphs:

- an AGENT is a character: a role, a goal, a backstory;
- a TASK is a job: a description and the expected output;
- a CREW is the team: who does which task, in which process.

Nothing here says "go to node X then Y". The order comes from the
process (sequential) and from each task's `context`, i.e. which
earlier results it receives.
"""

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool

from modele import get_crew_llm

# The "web" of this chapter: a few facts, the same every run.
FACTS = {
    "lisbon": "550,000 inhabitants; trams on steep hills; "
              "pasteis de nata; 290 sunny days a year.",
    "kyoto": "1.4 million inhabitants; over 1,600 temples; "
             "imperial capital until 1868.",
}


@tool("Look up a city")
def lookup_city(city: str) -> str:
    """Return verified facts about a city (Lisbon, Kyoto)."""
    facts = FACTS.get(city.strip().lower())
    return facts or f"No facts for {city!r}."


def build_crew(llm=None, hierarchical=False):
    """Assemble the team. Tests inject a fake `llm`."""
    llm = llm or get_crew_llm()

    researcher = Agent(
        role="Travel Researcher",
        goal="Collect accurate facts about {city}",
        backstory="You are a meticulous researcher. You never "
                  "state a fact you did not get from your tool.",
        tools=[lookup_city],
        llm=llm,
    )
    writer = Agent(
        role="Travel Writer",
        goal="Write a vivid paragraph about {city}",
        backstory="You write for a travel magazine: short "
                  "sentences, concrete details, no cliches.",
        llm=llm,
    )
    reviewer = Agent(
        role="Fact Checker",
        goal="Make sure every claim comes from the research",
        backstory="You are an editor who deletes anything the "
                  "research does not support.",
        llm=llm,
    )
```

L'outil, `lookup_city`, est factice : un petit dictionnaire de faits, pour que les tests soient stables. Remarque que le décorateur `@tool` vient de CrewAI (`crewai.tools`), pas de LangChain. Même idée qu'au chapitre 2 : le nom et la docstring décrivent l'outil au modèle.

Remarque aussi `{city}` dans le but. Les accolades sont des trous, remplis au lancement par `kickoff(inputs={"city": "Lisbon"})`. Même principe que le `PromptTemplate` du chapitre 2.

Le modèle de chaque agent vient de `get_crew_llm`, la fonction que `modele.py` ajoute à la copie du chapitre 1 :

<!-- code: modele.py 57-66 -->
```python
def get_crew_llm():
    """The same OpenRouter model, seen through CrewAI.

    CrewAI has its own LLM class; the `openrouter/` prefix tells it
    where to go. Same key, same MODELE as chapter 1.
    """
    # Imported here: `python modele.py` must work without CrewAI.
    from crewai import LLM
    return LLM(model=f"openrouter/{MODEL}",
               api_key=get_client().api_key)
```

CrewAI a sa propre classe `LLM` ; le préfixe `openrouter/` lui dit de passer par OpenRouter, avec la même clé et le même modèle que les chapitres précédents.

Le rédacteur écrit « pour un magazine : phrases courtes, détails concrets, pas de clichés ». Le vérificateur a pour histoire : « tu es un éditeur qui supprime tout ce que la recherche ne soutient pas ». C'est cette phrase qui a fait disparaître le tram 28.

> 💡 **À retenir** — La `backstory` est une consigne déguisée en personnage. Écris-la comme tu écrirais une règle de comportement : ce que cet agent fait, et surtout ce qu'il refuse de faire.

## Les tâches : qui reçoit quoi

Chaque agent a besoin d'un travail. C'est le rôle des `Task`, la suite de `build_crew` :

<!-- code: crew.py 62-80 -->
```python
    research = Task(
        description="Find the key facts about {city}.",
        expected_output="A bullet list of 3 to 5 facts.",
        agent=researcher,
    )
    writing = Task(
        description="Write a paragraph of 3 sentences about {city} "
                    "using the research.",
        expected_output="One paragraph of 3 sentences.",
        agent=writer,
        context=[research],  # the writer receives the facts
    )
    review = Task(
        description="Check the paragraph against the research and "
                    "return the corrected final version.",
        expected_output="The final paragraph, nothing else.",
        agent=reviewer,
        context=[research, writing],
    )
```

Le champ `expected_output` compte beaucoup. C'est le critère de réussite que l'agent lit : « liste de 3 à 5 faits », « un paragraphe de trois phrases ». Plus il est précis, moins tu as de surprises.

Le champ `context` est la plomberie du crew. La tâche d'écriture reçoit le résultat de la tâche de recherche, la relecture reçoit les deux. Un agent ne voit que ce que tu lui passes : le chercheur ne sait rien du brouillon, et c'est voulu. Un des tests le vérifie en regardant les prompts reçus.

> ⚠️ **Piège classique** — Un `expected_output` du genre « un bon texte ». L'agent ne sait pas à quoi se mesurer et renvoie ce qui lui passe par la tête. Décris la forme (nombre de phrases, liste ou paragraphe) et ce qui est interdit. Pour la relecture, « le paragraphe final, rien d'autre » évite le bavardage du genre « Voici la version corrigée : ».

Deux options existent que ce chapitre laisse volontairement éteintes. Un agent peut **déléguer** (`allow_delegation=True`) : il demande alors un coup de main à un collègue, ce qui ajoute des appels et de l'imprévisible. Et un équipage peut garder une **mémoire** entre exécutions. Commence sans : tu actives une option quand tu as mesuré le besoin, pas avant.

## L'équipage : séquentiel ou hiérarchique

Reste à assembler, à la fin de `build_crew` :

<!-- code: crew.py 82-97 -->
```python
    if hierarchical:
        # A manager agent decides who does what, instead of a fixed
        # order. It needs its own model.
        options = {
            "process": Process.hierarchical,
            "manager_llm": llm,
        }
    else:
        options = {"process": Process.sequential}

    return Crew(
        agents=[researcher, writer, reviewer],
        tasks=[research, writing, review],
        verbose=False,
        **options,
    )
```

Le lancement se fait dans `main.py`, le dernier fichier :

<!-- code: main.py -->
```python
"""Run chapter 4:  python main.py

Needs OPENROUTER_API_KEY in the .env file at the repository root,
and Python 3.13 or older (CrewAI does not support 3.14 yet).
"""

from crew import build_crew


def main():
    result = build_crew().kickoff(inputs={"city": "Lisbon"})

    # One output per task: we SEE what each role produced.
    for task_output in result.tasks_output:
        print(f"\n--- {task_output.agent} ---")
        print(task_output.raw)

    print("\n=== Final result ===")
    print(result.raw)


if __name__ == "__main__":
    main()
```

`kickoff` lance le crew et remplit les `{city}`. En mode **séquentiel**, les tâches s'exécutent dans l'ordre de la liste, chacune avec ses `context`. Le résultat final est celui de la dernière. C'est le mode par défaut, et celui qu'on utilise presque toujours.

Le mode **hiérarchique** (`Process.hierarchical`) ajoute un **agent manager**, qui lit les tâches et décide à qui les confier, quand redemander, quand conclure. Il demande un modèle supplémentaire : `manager_llm`. Dans notre fichier, il s'active avec `build_crew(hierarchical=True)` : c'est le dictionnaire `options` plus haut.

Ce mode semble attrayant : les agents s'organisent tout seuls. Il a un prix. Chaque décision du manager est un appel de modèle de plus, donc du temps, des tokens et de l'incertitude. Et un manager faible choisit mal. Mon réflexe : séquentiel d'abord, hiérarchique seulement quand l'ordre dépend vraiment du contenu.

Lance `python main.py` pour voir passer chaque rôle :

```text
--- Travel Researcher ---
- 550,000 inhabitants
- Trams on steep hills
- Pasteis de nata
- 290 sunny days a year

--- Travel Writer ---
Lisbon hosts 550,000 residents beneath 290 days of ...
Tram 28 surges upward on cables ...

--- Fact Checker ---
Lisbon hosts 550,000 residents under 290 sunny days ...
Trams surge upward on cables ...
```

La sortie d'une exécution réelle, avec le modèle gratuit par défaut, tronquée. Le jour où tu te demandes pourquoi un résultat est faux, cette vue par rôle est ton premier outil de diagnostic : tu vois quel agent a introduit l'erreur.

## CrewAI face à LangGraph : même travail, deux philosophies

Au chapitre 3, on a fait « rédiger, critiquer, réécrire » en graphe. Ici, c'est « chercher, rédiger, vérifier » en agents par rôle. Les deux ressemblent à un pipeline, et pourtant ils diffèrent.

| | CrewAI | LangGraph |
|---|---|---|
| Unité de base | l'agent (un métier) | le nœud (une fonction) |
| Ordre | décrit par le processus et les `context` | décrit par des arêtes |
| Boucle conditionnelle | non, dans le mode simple | oui, c'est son cœur |
| Pause humaine, reprise | pas dans le mode simple | `interrupt_before`, checkpointer |
| Lecture du code | proche d'un organigramme | proche d'un schéma de circulation |
| Contrôle du prompt | indirect (rôle, but, histoire) | total (tu écris chaque prompt) |
| Appels dans notre atelier | 3, toujours | 2, 4 ou 6 selon le contenu |

Le dernier point est celui que les tests montrent : un crew séquentiel fait toujours autant d'appels que de tâches. Notre vérificateur relit une fois, même si le texte est parfait. Pour « relis jusqu'à ce que ce soit bon », CrewAI propose d'autres mécanismes (les *Flows*, qui ajoutent des branches et de l'état), mais on quitte alors le confort du mode simple, et un graphe LangGraph devient souvent plus direct.

Voici comment je tranche :

- **Plusieurs métiers qui se passent un document**, avec un ordre fixe : CrewAI. Le code se lit comme le cahier des charges.
- **Une boucle, une validation humaine, une reprise après plantage** : LangGraph.
- **Des agents avec un ordre fixe, plus tard une boucle** : commence par CrewAI, et passe à LangGraph le jour où tu te retrouves à contourner le framework.

## Forces et limites pour un projet réel

Ce qui marche bien. Le **temps d'écriture** : trois agents en soixante lignes. La **lisibilité** : un collègue non programmeur lit `role`, `goal`, `backstory` et comprend. La **séparation des métiers** : un agent qui n'a qu'une mission fait mieux qu'un agent à qui l'on demande tout, surtout avec un petit modèle.

Ce qui coûte. Le **prompt est généré par le framework** : tu écris des rôles, il fabrique le texte envoyé au modèle. Quand le comportement surprend, tu dois aller lire ce que le framework a vraiment envoyé. Le **coût en tokens** monte vite, car chaque agent embarque son rôle, son histoire, la description de ses outils et les contextes reçus. Le **nombre d'appels** est fixe. Et le **calendrier des versions** compte : CrewAI évolue vite, et sa compatibilité avec la dernière version de Python suit avec du retard, comme tu viens de le voir.

> ⚠️ **Piège classique** — Multiplier les agents « pour faire sérieux ». Chaque agent ajoute au moins un appel de modèle et un point de défaillance. Trois agents bien distincts valent mieux que sept aux rôles qui se recouvrent. Si deux agents pourraient échanger leurs `backstory` sans que rien ne change, fusionne-les.

## QCM

**1.** Qu'est-ce qui décrit un agent CrewAI ?

- **a)** Un but
- **b)** Un rôle
- **c)** Une histoire (`backstory`)
- **d)** Un graphe d'états

**2.** À quoi sert `context` sur une tâche ?

- **a)** À choisir le modèle
- **b)** À définir le rôle de l'agent
- **c)** À limiter le nombre d'appels
- **d)** À dire quels résultats d'autres tâches elle reçoit

**3.** Ton rédacteur invente des faits. Que corriges-tu ?

- **a)** La `backstory` du rédacteur
- **b)** La mission du vérificateur : supprimer ce qui n'est pas sourcé
- **c)** L'`expected_output` du rédacteur
- **d)** La clé d'API

**4.** Tes sept agents coûtent cher sans meilleur résultat. Que fais-tu ?

- **a)** J'ajoute un huitième agent
- **b)** Je rallonge les prompts
- **c)** Je réduis le nombre d'agents
- **d)** Je fusionne les agents dont les rôles se recouvrent

**5.** « Relis jusqu'à approbation, trois fois maximum » : quelles options conviennent ?

- **a)** Un `manager_llm` seul
- **b)** Le mode séquentiel tel quel
- **c)** Les Flows de CrewAI
- **d)** Un graphe LangGraph

**6.** Combien d'appels fait le crew séquentiel de l'atelier ?

- **a)** Deux, quatre ou six selon le contenu
- **b)** Un seul
- **c)** Autant que de mots du texte
- **d)** Trois, toujours : un par tâche

**Réponses.** Q1 : a, b, c · Q2 : d · Q3 : a, b, c · Q4 : c, d · Q5 : c, d · Q6 : d

## Ce qu'il faut retenir
1. CrewAI décrit un groupe d'agents : des `Agent` (rôle, but, histoire), des `Task` (description, résultat attendu) et un `Crew` qui les assemble.
2. `context` dit quels résultats une tâche reçoit, et `inputs` remplit les `{trous}` au lancement. Un agent ne voit que ce que tu lui passes.
3. Le processus séquentiel exécute les tâches dans l'ordre. Le hiérarchique ajoute un manager qui coordonne, au prix d'appels supplémentaires.
4. CrewAI se lit comme un organigramme et s'écrit vite. LangGraph donne le contrôle des boucles, des pauses et des prompts. Même travail, deux outils : le choix dépend de la forme du flux.

**Au chapitre suivant :** tu as écrit trois systèmes d'agents en Python. Et si l'on pouvait en construire un sans écrire une ligne, en glissant des boîtes sur un écran ? Les plateformes no-code (n8n, Make) promettent exactement cela. On les essaie, on mesure ce qu'elles font bien, et on repère le moment où il faut revenir au code.

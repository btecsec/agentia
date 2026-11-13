# Chapitre 6 — Spécifications de myTravel : écrire ce que l'agent doit faire, avant de le coder

> **Dossier GitHub associé :** `chapitre-06-specifications/`

**À la fin de ce chapitre, tu sauras :**

- décrire myTravel par ses cas d'usage, ses fonctionnalités et ses contraintes ;
- dessiner l'architecture globale : frontend, backend, agents, outils, données ;
- remplir la fiche d'un agent : ce qu'il fait, ce qu'il reçoit, ce qu'il produit, qui il attend ;
- écrire des règles d'acceptation qu'un développeur transforme en tests sans rien deviner ;
- relire une spécification et y trouver une contradiction avant qu'elle ne devienne un bug ;
- lancer myTravel fini, en cinq minutes, pour voir où on va.

Ce chapitre ne contient pas une ligne de code à écrire, et son dossier non plus. Il s'adresse autant au développeur qu'au chef de projet, au product owner ou à l'expert métier qui n'a jamais ouvert un fichier Python. La spécification, c'est leur travail. Le code viendra après, et il obéira à ce qui est écrit ici.

## Le voyage qui a mal fini

Un ami m'a raconté son premier assistant de voyage. Il avait demandé : « Lisbonne, cinq jours, 900 € ». L'agent avait répondu avec enthousiasme, un vol à 310 €, un hôtel à 540 €, une location de voiture à 120 €. Total : 970 €. Personne n'avait dit à l'agent que 900 € était un plafond, pas une suggestion.

Le plan suivant était plus sage. Mais il proposait un vol le lendemain à 6 h, pour un voyageur dont le passeport expirait trois mois après le retour. Là encore, aucune règle n'existait : le passeport n'était pas dans la demande, donc il n'existait pas pour l'agent.

Ces deux erreurs n'ont rien à voir avec le modèle. Un modèle bien meilleur aurait fait pareil. Le défaut venait de plus haut : **personne n'avait écrit ce que « un bon plan » voulait dire.**

Ce chapitre ouvre la deuxième partie du livre. Jusqu'ici, tu as écrit des agents pour apprendre. À partir d'ici, on construit un vrai produit, myTravel. Et un produit commence par une spécification : une description précise de ce qu'il doit faire, assez précise pour que n'importe qui, en lisant un plan, puisse dire « c'est bon » ou « ce n'est pas bon ».

## Avant de spécifier : essaie le produit fini

Un meuble en kit, c'est cent vis, trente planches et une notice. Personne n'ouvre la boîte sans avoir regardé la photo du meuble monté. Sans elle, la planche 14 n'est qu'une planche ; avec elle, c'est le dos de l'armoire.

Alors avant de lire la spécification, regarde la photo. Le dossier `chapitre-20-projet-final/mytravel` contient myTravel **fini**, tel qu'il sera à la dernière page : la page web qui répond en direct, les sept agents, les sites officiels, les vrais prix d'hôtels et de vols, la mémoire, les garde-fous. Lance-le maintenant. Chaque chapitre suivant démonte et remonte une de ses pièces, et tu sauras toujours à quoi elle sert.

**1. Les clés.** Une seule est obligatoire, mais prends les trois : avec elles, myTravel trouve ses sources et donne de vrais prix. Toutes sont gratuites.

- `OPENROUTER_API_KEY`, le modèle. Crée un compte sur openrouter.ai, puis une clé dans *Keys*. OpenRouter demande une carte à l'inscription (une vérification anti-robot), mais rien n'est prélevé tant que tu restes sur un modèle gratuit, ceux dont le nom finit par `:free`.
- `TAVILY_API_KEY`, la recherche web (app.tavily.com, sans carte). C'est un moteur fait pour les agents : il trouve mieux les pages officielles. Sans clé, myTravel cherche avec DuckDuckGo.
- `TRAVELPAYOUTS_TOKEN`, les prix de vol (travelpayouts.com, *Profil*, *API token*, sans carte). Sans lui, myTravel ne donne pas de prix de vol, seulement des liens.

Les hôtels (Xotelo), la météo (Open-Meteo) et les sites officiels n'en demandent aucune.

**2. L'installation**, une fois pour tout le livre, à la racine du dépôt :

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # puis colle tes clés
```

Ouvre `.env` et remplis ces trois lignes, sans espace autour du `=` :

```bash
OPENROUTER_API_KEY=sk-or-v1-...  # obligatoire : le modèle
TAVILY_API_KEY=tvly-...          # recherche : sources officielles
TRAVELPAYOUTS_TOKEN=...          # vrais prix de vol
```

Pas de clé pour l'une d'elles ? Mets un `#` devant sa ligne. Ne laisse jamais les `...` : une fausse clé Tavily fait échouer chaque recherche, et myTravel répond sans aucune source.

**3. Le lancement :**

```bash
cd chapitre-20-projet-final/mytravel
uvicorn server:app --reload     # puis http://localhost:8000
```

Dis d'abord qui tu es : « Je suis français et je pars de Lyon. » myTravel s'en souviendra. Puis essaie trois questions, et regarde la bulle d'attente : chaque agent y apparaît au moment où il démarre, puis la réponse s'écrit mot à mot.

1. **« Visa pour le Japon en mars, passeport français ? »** Un seul agent travaille. Les pastilles grises sous la réponse sont les sources : de vraies pages de diplomatie.gouv.fr ou france-visas.gouv.fr.
2. **« Quel temps à Lisbonne la semaine prochaine ? »** Seul l'agent Météo travaille, avec les prévisions d'Open-Meteo, lues à l'instant.
3. **« Plan complet : Rome, 4 jours en mai, 800 €, je peux décaler de trois jours. »** Compte une à deux minutes avec un modèle gratuit. La réponse s'ouvre sur des séjours : vol et hôtel réels, avec leur vendeur, leur lien et un total, aux jours les moins chers. Puis écris « Prépare la réservation » : une carte orange te demande ton accord avant de préparer les liens.

| Ce que tu vois | Ce que ça veut dire | Quoi faire |
|---|---|---|
| « Erreur du modèle : regarde les logs » | clé absente, fausse ou expirée | lis la ligne `model_error` du terminal, refais une clé |
| « Les modèles gratuits sont saturés… » | le modèle gratuit et ses secours ont répondu 429 | « Non, j'attends » réessaie dans une minute ; « Oui » paie quelques centimes |
| pas de prix de vol, seulement un lien | `TRAVELPAYOUTS_TOKEN` manque | crée le jeton, ajoute-le au `.env`, relance |
| aucune pastille de source | `TAVILY_API_KEY` fausse (`search_failed` dans le terminal) | corrige la clé ou mets un `#` devant, relance |
| `address already in use` | le port 8000 est déjà pris | `uvicorn server:app --port 8001` |

Les tests tournent sans clé ni réseau : `pytest`, dans le même dossier. Et ferme ce livre dix minutes : ouvre `server.py` et cherche quelle fonction reçoit ton message. Tu ne trouveras peut-être pas tout, et c'est très bien : chercher d'abord, c'est ce qui fait que l'explication rentre ensuite.

> 💡 **À retenir** — Tu n'as pas besoin de comprendre le code pour lancer myTravel. Lance-le maintenant, garde-le ouvert, et reviens-y à chaque chapitre : c'est la photo sur la boîte.

## Les cas d'usage : trois façons de s'en servir

Un **cas d'usage** (*use case*) est une situation réelle, racontée du point de vue de l'utilisateur. Pas une fonctionnalité technique. Une phrase qu'une vraie personne taperait.

myTravel en a trois.

**Planifier un voyage.** « Lisbonne, cinq jours en mai, 900 €, on est deux. » C'est le cas principal. L'agent doit produire un plan complet : transport, hébergement, visites, repas, formalités. Chaque prix a une source, le total respecte le budget.

**Trouver un hôtel.** « Un endroit calme, près du métro, 3 étoiles minimum, demi-pension, moins de 90 € la nuit. » Ici, l'utilisateur sait déjà où il va. Un seul agent travaille, les autres restent muets. Ce cas sert de test : si myTravel ne sait pas faire ça seul, ajouter des agents ne servira à rien.

**Préparer les formalités.** « Je suis français, je pars au Japon en mars : il me faut un visa ? Je peux prendre mon gel douche en cabine ? » Le voyage est décidé, il reste à ne rien rater. L'agent a besoin de règles officielles, lues le jour même, pas de souvenirs.

Trois cas, trois profils de charge. Le premier réveille tous les agents, le deuxième un seul spécialiste, le troisième un ou deux. Garde cette différence en tête : au chapitre 13, elle décidera de la forme du graphe.

> 💡 **À retenir** — Un cas d'usage s'écrit avec les mots de l'utilisateur, pas avec ceux de l'ingénieur. Si tu ne peux pas le taper dans une zone de saisie, ce n'est pas un cas d'usage, c'est une tâche technique.

## Les fonctionnalités attendues

Des cas d'usage, on déduit ce que myTravel doit savoir faire. Six fonctionnalités, une par domaine.

| Domaine | Ce que myTravel fait |
|---|---|
| Vols | cherche et compare, selon prix, horaires, compagnie, bagage en soute compris ou non |
| Hôtels | propose des établissements bien notés au bon prix, au bon nombre d'étoiles, avec la pension et le transfert aéroport demandés |
| Voiture et transports | loue un véhicule ou conseille les transports locaux |
| Administration | vérifie visa, passeport, formalités, bagages et santé, sur les sites officiels |
| Météo | donne la météo des dates du voyage : la prévision si elle existe, sinon l'an dernier aux mêmes dates |
| Risques | signale les dangers connus (sécurité, catastrophes naturelles, santé), d'après les conseils officiels aux voyageurs |

Une règle de produit traverse toute la liste, et elle est dite dans l'avant-propos : myTravel **trouve et compare, il ne réserve pas et ne paie pas**. Chaque offre arrive avec un lien vers le site du fournisseur. C'est toi qui cliques et qui paies. Ce choix retire d'un coup toute une famille de risques (paiement, données bancaires, erreurs irréversibles). On y reviendra au chapitre 14.

Quatre de ces lignes cachent un piège de comparaison. Un vol à 180 € sans bagage en soute n'est pas moins cher qu'un vol à 240 € bagage compris : c'est le même voyage à 25 € près, ou un surclassement surprise au comptoir d'enregistrement. Même histoire côté hôtel : un 3 étoiles en demi-pension et un 4 étoiles chambre seule ne se comparent pas tant qu'on n'a pas écrit ce que le voyageur voulait. La spécification ajoute donc quatre **options du voyage**, qui voyagent avec la demande du début à la fin :

| Option | Valeurs | Par défaut |
|---|---|---|
| Bagage en soute | oui / non | non |
| Étoiles minimum de l'hôtel | 1 à 5 | 3 |
| Pension | aucune / demi-pension / pension complète | aucune |
| Transfert aéroport ↔ hôtel | oui / non | non |

Chaque option a une valeur par défaut, et c'est le point important. Le voyageur qui écrit « Lisbonne, cinq jours, 900 € » ne parle ni d'étoiles ni de bagages ; sans défaut écrit, l'agent Mission doit deviner, et deux exécutions de la même phrase donnent deux plans différents. Avec un défaut écrit, elles donnent le même, et le voyageur n'a à préciser que ce qui s'écarte de la norme.

Ces options changent aussi le travail des agents. Vols rapatrie le prix du bagage dans le prix affiché, au lieu de le laisser en petits caractères. Hôtel filtre sur les étoiles, inclut la pension dans le prix du séjour et va chercher le transfert.

> ⚠️ **Piège classique** — Écrire « l'agent réserve l'hôtel » dans une spécification parce que ça paraît naturel. Dès cette phrase, tu t'engages sur des paiements, des annulations et du RGPD. Décide tôt ce que l'agent ne fait **pas**. C'est la partie la plus utile d'un cahier des charges.

## Les contraintes : ce qui limite le projet

Une fonctionnalité dit *quoi*. Une **contrainte** dit *à quel prix, à quelle vitesse, avec quelle fiabilité*. On les oublie, puis elles font échouer les projets en production. myTravel en retient cinq.

| Contrainte | Cible | Comment on vérifie |
|---|---|---|
| Coût | moins de 0,50 € d'appels au modèle par plan | compteur de consommation, relevé à chaque plan |
| Latence | un premier plan en moins de 60 secondes | chronomètre, de la demande à l'affichage |
| Fiabilité | un site ou un moteur de recherche en panne ne bloque jamais le plan | essai avec la recherche web coupée exprès |
| Sources | chaque fait porte un lien vers un site officiel ou vers le fournisseur | relecture du plan : un fait sans lien est refusé |
| Fraîcheur | aucune donnée écrite en dur dans le code : tout est lu le jour de la question | chercher dans le dépôt un fichier de prix ou de règles : il n'y en a pas |

Le **coût**, d'abord. Pour quelqu'un qui a un budget de voyage de 900 €, une facture d'IA à deux chiffres serait absurde. Au chapitre 19, on mesure vraiment. La **latence**, c'est le temps d'attente entre la demande et la réponse : un agent qui réfléchit trois minutes sans rien afficher donne l'impression d'être planté. Pour la **fiabilité**, l'agent doit dire « je n'ai pas pu interroger les vols, voici le reste », plutôt que s'arrêter ou, pire, inventer un vol. Les **sources** : un chiffre sans lien est un chiffre qu'on ne peut pas croire. Et la **fraîcheur** : une règle de visa recopiée dans un fichier en janvier est fausse en juin. myTravel ne garde aucune copie, il lit la page officielle au moment où tu poses la question.

Regarde la troisième colonne. Une contrainte dont personne ne sait dire comment la vérifier n'en est pas une, c'est un vœu.

## Pratique : qui fait quoi, et comment s'en servir

Le dossier de ce chapitre ne contient qu'un seul document Word, à ouvrir dans Word, LibreOffice ou Google Docs. Aucune installation, aucune clé, aucun code.

### Le document et ses parties

```text
chapitre-06-specifications/
└── specification-mytravel.docx
    ├── Mode d'emploi        ← qui fait quoi, ce qui est attendu
    ├── Partie 1             ← vue d'ensemble : cas d'usage,
    │                           contraintes, architecture
    ├── Partie 2             ← les outils et les fiches agents
    ├── Partie 3             ← les règles d'acceptation
    ├── Partie 4             ← la checklist de relecture
    └── Annexes A et B       ← fiche vierge, règle vierge
```

| Partie | Ce qu'elle contient | Tu la modifies quand… |
|---|---|---|
| Partie 1 — Vue d'ensemble | le produit, ses contraintes, l'ordre de passage | un besoin ou une contrainte change |
| Partie 2 — Fiches des agents | mission, entrées, sorties, outils, attentes de chaque agent | tu ajoutes ou redécoupes un agent |
| Partie 3 — Règles d'acceptation | les règles qu'un plan doit respecter | tu ajoutes ou changes une règle |
| Partie 4 — Checklist de relecture | les contrôles avant de passer la spec aux développeurs | tu découvres un nouveau type d'oubli |

Chaque partie s'ouvre sur un encadré « Ce qui est attendu dans cette partie » : la liste de ce qu'un relecteur va vérifier. Lis-le avant de remplir quoi que ce soit.

### Qui écrit, qui relit, qui code

```text
fonctionnel ──► fiches + règles ──► relecture (checklist)
                                         │
                                         ▼
                              développeur : une règle = un test
                                         │
                                         ▼
                              plan refusé s'il casse une règle
```

Le fonctionnel écrit. Un collègue relit avec la checklist. Le développeur traduit chaque règle en test automatique, sans rien inventer : si une règle est floue, il la renvoie au fonctionnel au lieu de la deviner.

### Comment s'en servir

1. Lis le mode d'emploi et la partie 1 d'une traite : dix minutes, et tu as le produit en tête.
2. Pour un nouvel agent, copie la fiche vierge de l'annexe A dans la partie 2 et remplis chaque case. Une case vide est une question à poser, pas un détail.
3. Pour une nouvelle règle, copie la règle vierge de l'annexe B dans la partie 3 et écris-la avec un exemple chiffré.
4. Avant de transmettre, passe la checklist de la partie 4. Chaque « non » est un défaut à corriger.

### Les cinq détails à comprendre

1. **Une case par information.** Mission, entrées, sorties, outils, attentes, comportement en cas de panne : un tableau oblige à répondre à tout, un paragraphe permet d'esquiver.
2. **Chaque agent déclare qui il attend.** C'est cette colonne qui fixe l'ordre de passage, pas l'intuition.
3. **Une règle s'écrit avec un exemple chiffré.** « 970 € pour 900 € de budget : refusé. » Le développeur n'a plus rien à interpréter.
4. **La relecture cherche tous les défauts, pas le premier.** On note tout, on corrige tout, puis on relit.
5. **Les règles d'acceptation servent jusqu'au bout.** Au chapitre 16, elles deviennent des cas d'évaluation que la machine rejoue à chaque changement.

## L'architecture globale

Voici myTravel vu de loin. Cinq couches, de l'utilisateur jusqu'aux données.

![Les cinq couches de myTravel : page web, API, agents, outils, données](chapitre-06-specifications/images/couches-mytravel.png){width=11.2cm}

Quelques mots sur ce que tu ne connais peut-être pas encore. La **page web** (le *frontend*) est ce que l'utilisateur voit. L'**API** (le *backend*) est la partie serveur qui reçoit les demandes et coordonne le reste ; plus largement, une API est une porte d'entrée programmable : on lui envoie une requête, elle renvoie des données. La **recherche web officielle** consiste à interroger un moteur de recherche en ne gardant que des sites de confiance (le ministère des Affaires étrangères, l'Institut Pasteur, la compagnie aérienne), puis à lire la page avant de citer quoi que ce soit. On la construit au chapitre 9. La **mémoire** garde la conversation, et avec elle ce que tu dis de toi (nationalité, ville de départ, budget) : chapitre 8.

Regarde la dernière couche. Aucune base de guides, aucun fichier de prix. La seule chose que myTravel stocke, c'est ce que **toi** tu lui as dit.

Le flux typique, de la demande au plan :

1. Tu écris ta demande dans la page web.
2. L'API la reçoit et vérifie qu'elle peut entrer (pas de numéro de carte, pas mille messages à la minute).
3. L'agent Mission la transforme en demande structurée (destination, dates, budget, voyageurs) et choisit les spécialistes utiles.
4. Les spécialistes travaillent en même temps, chacun avec ses outils.
5. L'agent Synthèse assemble, additionne, signale ce qui manque.
6. Le plan revient avec ses sources. C'est toi qui décides, et toi qui réserves.

## Les sept agents, un par un

Pourquoi sept agents plutôt qu'un ? Réponse honnête : on pourrait commencer avec un seul, et c'est ce qu'on fera du chapitre 8 au chapitre 12. Mais un agent qui doit connaître les vols, les visas, la météo et les hôtels reçoit des consignes immenses, dix outils, et choisit mal. Séparer, c'est donner à chacun une mission courte, deux ou trois outils et un résultat qu'on peut vérifier.

| Agent | Mission | Outils |
|---|---|---|
| **Mission** | comprend la demande, choisit les spécialistes utiles | lecture de la conversation |
| **Administration** | vérifie visa, passeport, formalités, bagages, santé | recherche sur sites officiels, lecture de page |
| **Hôtel** | propose des hôtels bien notés dans le budget | recherche sur sites de réservation, lien prérempli, taux de change |
| **Transports** | trouve des vols et, si utile, une voiture | recherche sur sites de voyage, liens préremplis |
| **Météo** | donne la météo des dates du voyage | service météo en direct |
| **Risque** | évalue sécurité, risques naturels, santé | conseils officiels aux voyageurs |
| **Synthèse** | assemble, vérifie le budget, liste les sources | aucun : il lit les rapports des autres |

Un **outil**, ici, c'est un service que l'agent peut appeler pour obtenir un fait : un prix vu sur une page, une règle de visa, une prévision. L'agent ne sait pas ces choses par cœur, il va les chercher.

Chaque ligne du tableau devient une fiche complète dans la partie 2 du document. Voici celle de l'agent Administration, celui dont une erreur coûte le plus cher (un embarquement refusé) :

| Rubrique | Agent Administration |
|---|---|
| Mission | dire ce qu'il faut pour entrer dans le pays : visa, passeport, formalités, et ce qui passe en cabine |
| Reçoit | la demande de voyage, la nationalité du voyageur |
| Produit | un rapport court, chaque règle avec le lien de la page officielle lue |
| Outils | recherche sur sites officiels, lecture de page |
| Attend | Mission |
| Ne fait pas | remplir un formulaire de visa, payer une taxe |
| Si panne | dit qu'il n'a trouvé aucune source officielle, ne devine jamais |

La ligne « Si panne » est la plus importante. Un agent qui devine une règle de visa est pire qu'un agent qui se tait. La ligne « Attend » compte aussi : c'est elle qui fixe l'ordre de passage.

> 💡 **À retenir** — Un bon découpage en agents suit les **dépendances de données**, pas l'organigramme. Si l'agent B a besoin de ce que produit A, il attend. Sinon, ils tournent ensemble et le plan arrive plus vite.

## L'ordre de passage, déduit des fiches

Un **tour**, c'est un groupe d'agents qui démarrent en même temps ; le tour suivant attend que tous aient fini. Personne ne choisit les tours au hasard : ils se lisent dans la ligne « Attend » des fiches, avec une seule règle.

> Un agent passe au tour qui suit celui du dernier agent qu'il attend. Un agent qui n'attend personne passe au tour 1.

Appliquée aux sept fiches :

```text
tour 1   Mission                     (n'attend personne)
tour 2   Administration, Hôtel, Transports,
         Météo, Risque               (attendent Mission)
tour 3   Synthèse                    (attend tous les autres)
```

Trois tours. Aucun spécialiste n'en attend un autre, et ce n'est pas un hasard : c'est ce qui permet de les lancer tous en même temps, donc d'avoir un plan complet en à peine plus de temps que le plus lent d'entre eux. Le jour où quelqu'un écrit « Hôtel attend Transports » dans une fiche (pour dormir près de l'aéroport d'arrivée, par exemple), un quatrième tour apparaît et le plan arrive plus tard. C'est une décision de produit, et elle se prend dans la fiche.

Autre détail : au tour 2, seuls les spécialistes **utiles** se réveillent. « Il me faut un visa pour le Japon ? » ne réveille qu'Administration. Mission choisit.

> ⚠️ **Piège classique** — Deux agents qui s'attendent l'un l'autre. A attend B, B attend A : aucun des deux ne démarre jamais. Sur sept fiches, ça se voit. Sur trente, non. La checklist de relecture pose la question à chaque fois.

## Le cahier des charges qui se vérifie

Reste la partie la plus importante. Revenons au voyage qui a mal fini : budget dépassé, passeport trop court. Aucune de ces erreurs n'était sorcière. Il suffisait de les écrire.

Une **règle d'acceptation** décrit, avec un exemple, ce qui rend un plan acceptable ou non. On l'écrit au format « Étant donné / Quand / Alors », très répandu en gestion de projet : le contexte, l'événement, le résultat attendu.

```text
Règle R1 — Budget
Étant donné  une demande avec un budget de 900 €
Quand        le plan proposé coûte 970 €
Alors        le plan est refusé
Et           le message dit « budget dépassé de 70 € »
```

```text
Règle R4 — Passeport
Étant donné  un voyage qui se termine le 15 mai
Et           un passeport qui expire le 1er août
Quand        myTravel produit un plan
Alors        le plan est refusé
Et           le message dit « passeport valide 78 jours
             après le retour, 183 nécessaires »
```

```text
Règle R5 — Options du voyage
Étant donné  une demande avec 4 étoiles minimum,
Et           la demi-pension et le transfert aéroport
Quand        l'hôtel du plan a 3 étoiles, sans pension ni transfert
Alors        le plan est refusé
Et           le message dit « hôtel 3 étoiles, 4 demandées ;
             pension manquante ; il manque : transfert aéroport »
```

R5 est la règle qui ferme la porte au plan « presque bon ». Sans elle, rien n'empêche un hôtel 2 étoiles d'entrer dans un plan qui respecte le budget : il le respecte même très bien, puisqu'il coûte moins cher. Un cas limite se tranche tout de suite : mieux que demandé reste accepté, un 5 étoiles passe quand on en demandait 4. Mais seulement si le budget tient : R1 veille, et les deux règles se lisent ensemble.

myTravel a cinq règles, toutes dans la partie 3 du document :

| Règle | Un plan est refusé si… |
|---|---|
| R1 Budget | le total dépasse le budget de la demande |
| R2 Sources | un fait n'a pas de lien vers sa source |
| R3 Complet | il manque un vol ou un hébergement |
| R4 Passeport | le passeport expire moins de six mois après le retour |
| R5 Options | une option demandée manque : bagage, étoiles, pension, transfert |

Chaque règle porte un exemple chiffré. Ce n'est pas de la décoration : le développeur reprend exactement ces chiffres pour écrire son test. Si l'exemple manque, il invente le sien, et ce n'est plus ta règle qu'il teste.

Ces règles ne demandent aucune intelligence. Comparer 970 à 900, compter des jours entre deux dates : un programme ordinaire le fait sans jamais se tromper. C'est le fil conducteur de toute la suite : **le modèle propose, une règle écrite vérifie.**

> ⚠️ **Piège classique** — Mettre dans les consignes de l'agent « ne dépasse jamais le budget » et considérer que c'est réglé. Une consigne est une demande, pas une garantie. Un modèle peut l'oublier un jour sur vingt. Le plafond se contrôle après coup, par la règle R1, et un plan fautif est renvoyé à l'agent pour correction.

## Relire sa spécification

Une spec se relit comme un contrat. La checklist de la partie 4 contient une vingtaine de questions ; voici les plus utiles.

- Chaque outil cité dans une fiche est-il décrit quelque part ?
- Chaque outil décrit est-il utilisé par au moins un agent ?
- Chaque agent qu'une fiche « attend » existe-t-il vraiment ?
- Y a-t-il exactement un agent qui n'attend personne (l'entrée) et un seul que personne n'attend (la sortie) ?
- Deux agents s'attendent-ils l'un l'autre, directement ou par un détour ?
- Chaque règle a-t-elle un exemple chiffré, avec le message attendu ?
- Chaque contrainte a-t-elle une façon de se vérifier ?

On répond à **toutes** les questions avant de corriger quoi que ce soit. S'arrêter au premier défaut, c'est garantir trois allers-retours avec les développeurs au lieu d'un.

> 💡 **À retenir** — La relecture se fait à deux. Celui qui a écrit la fiche sait ce qu'il voulait dire, et il le relit au lieu de lire ce qui est écrit.

## QCM

**1.** Qu'est-ce qui distingue un cas d'usage d'une tâche technique ?

- **a)** Il est écrit avec les mots de l'utilisateur
- **b)** Il peut être tapé dans une zone de saisie
- **c)** Il cite le framework utilisé
- **d)** Il décrit une base de données

**2.** myTravel « trouve et compare, il ne réserve pas ». Quel risque cette règle retire-t-elle ?

- **a)** Les erreurs de paiement
- **b)** Les erreurs de calcul du budget
- **c)** Les réservations irréversibles faites par erreur
- **d)** Les pannes d'API

**3.** Le moteur de recherche ne répond plus. Que doit faire myTravel ?

- **a)** Réessayer indéfiniment
- **b)** Dire qu'il n'a pas pu interroger les vols et livrer le reste
- **c)** Inventer un vol plausible
- **d)** Refuser de répondre

**4.** Pourquoi les cinq spécialistes peuvent-ils travailler en même temps ?

- **a)** Aucun n'attend le résultat d'un autre
- **b)** Ils utilisent le même modèle
- **c)** Leurs fiches n'attendent que Mission
- **d)** Ils partagent les mêmes outils

**5.** Où vaut-il mieux contrôler le plafond de budget ?

- **a)** Dans les consignes de l'agent Synthèse uniquement
- **b)** Dans les consignes de chaque agent
- **c)** Dans une règle d'acceptation vérifiée sur chaque plan
- **d)** Dans le frontend

**6.** Pourquoi chaque règle d'acceptation porte-t-elle un exemple chiffré ?

- **a)** Pour que le développeur teste exactement ta règle, sans l'interpréter
- **b)** Parce que le format « Étant donné / Quand / Alors » l'interdit sans chiffres
- **c)** Pour que le message d'erreur attendu soit connu d'avance
- **d)** Pour rendre le document plus long

**7.** Une demande ne dit rien du bagage en soute. Que fait myTravel ?

- **a)** Il applique la valeur par défaut écrite dans la spec : pas de bagage
- **b)** Il choisit le vol le moins cher, bagage ou non
- **c)** Il demande au modèle de trancher au cas par cas
- **d)** Il refuse la demande tant que le voyageur n'a pas précisé

**Réponses.** Q1 : a, b · Q2 : a, c · Q3 : b · Q4 : a, c · Q5 : c · Q6 : a, c · Q7 : a

## Ce qu'il faut retenir

1. Une spécification décrit des cas d'usage (la phrase de l'utilisateur), des fonctionnalités (ce que l'agent fait) et des contraintes (coût, latence, fiabilité, sources, fraîcheur), chacune avec sa façon de se vérifier.
2. Décider tôt ce que l'agent ne fait pas, ici réserver et payer, supprime des risques entiers.
3. myTravel se découpe en cinq couches : page web, API, agents, outils, données. Les données ne contiennent que ce que le voyageur a dit : tout le reste est lu en direct.
4. Chaque agent a sa fiche : mission, entrées, sorties, outils, qui il attend, ce qu'il ne fait pas. L'ordre de passage se déduit de la ligne « Attend ».
5. Une option du voyage (bagage, étoiles, pension, transfert) ne vaut que si sa valeur par défaut est écrite : sans défaut, l'agent devine, et deux fois la même demande donne deux plans.
6. Une règle d'acceptation s'écrit « Étant donné / Quand / Alors », avec un exemple chiffré. Le développeur la transforme en test ; ce qu'une règle sait vérifier, on ne le demande pas à un modèle.
7. Une spécification n'exige pas de savoir coder. Elle exige d'être précis.

**Au chapitre suivant :** assez de papier. Tu vas lancer myTravel, fini, sur ta machine : la page web, les sept agents, les garde-fous. Tu verras où on va avant de construire quoi que ce soit, et tu sauras quel chapitre explique quelle pièce.

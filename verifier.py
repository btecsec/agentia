"""Lance les tests de tout le livre, un chapitre après l'autre.

Pourquoi ce script plutôt qu'un simple `pytest` à la racine ?

Chaque chapitre a son propre code : la partie 1 a ses dossiers
autonomes, et chaque chapitre de myTravel contient l'application
telle qu'elle est à la fin du chapitre. Mais Python ne garde qu'un
seul module nommé `agent` (ou `app`) par processus : le premier
importé gagne, et les tests des chapitres suivants testeraient alors
le mauvais fichier.

La seule façon honnête de tout lancer est donc de donner un processus
à chaque chapitre. C'est ce que fait ce script.

    python verifier.py            # tout le livre
    python verifier.py 3 4        # seulement les chapitres 3 et 4
"""

import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent


def dossiers_a_tester(filtres):
    """Renvoie les dossiers contenant des tests, dans l'ordre du livre.

    `filtres` est une liste de fragments : « 3 » retient le
    chapitre 3, « livre » retient l'outillage de fabrication.
    """
    dossiers = sorted(RACINE.glob("chapitre-*"))
    if (RACINE / "livre" / "tests").is_dir():
        dossiers.append(RACINE / "livre")

    # Les tests vivent dans tests/ (partie 1) ou mytravel/tests/
    # (l'application myTravel, chapitres 7 à 20).
    dossiers = [d for d in dossiers if (d / "tests").is_dir()
                or (d / "mytravel" / "tests").is_dir()]

    if not filtres:
        return dossiers
    return [d for d in dossiers if any(f in d.name for f in filtres)]


def lancer(dossier):
    """Lance pytest sur un dossier. Renvoie (succes, derniere_ligne)."""
    resultat = subprocess.run(
        [sys.executable, "-m", "pytest", str(dossier), "-q"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=RACINE,
    )
    lignes = [l for l in resultat.stdout.splitlines() if l.strip()]
    resume = lignes[-1] if lignes else "aucune sortie"
    # Code 5 = « aucun test n'a tourné ». Quand tout est ignoré (skipped),
    # c'est voulu : le chapitre CrewAI saute ses tests sous Python 3.14.
    ignore = resultat.returncode == 5 and "skipped" in resume
    return resultat.returncode == 0 or ignore, resume


def main(filtres):
    dossiers = dossiers_a_tester(filtres)
    if not dossiers:
        print("Aucun dossier de tests trouvé.")
        return 1

    echecs = []
    for dossier in dossiers:
        succes, resume = lancer(dossier)
        marque = "OK  " if succes else "ECHEC"
        print(f"{marque} {dossier.name:<32} {resume}")
        if not succes:
            echecs.append(dossier.name)

    print()
    if echecs:
        print(f"{len(echecs)} dossier(s) en échec : {', '.join(echecs)}")
        print("Relance le détail avec : pytest <dossier>/ -v")
        return 1

    print(f"Tout est vert : {len(dossiers)} dossiers.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

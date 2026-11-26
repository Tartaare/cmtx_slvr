"""Comparaison appariée des politiques de secours et mesure indépendante des directions reconstruites."""

import argparse
import json
import random
from pathlib import Path

import numpy as np

from .modele import Modele
from .reconstruction import reconstruire
from .resolution import Strategie, jouer, resoudre
from .secours import Repli, Secours
from .simulation import Observation, Scenario, nouvelle_grille
from .sources import SOURCES


def evaluer(principal: Modele, alternatif: Modele, parties: int, graine: int, budget: int) -> dict:
    if parties < 1 or budget < 1:
        raise ValueError("Le nombre de grilles et le budget doivent être positifs.")
    communs = [mot for mot in principal.jouables if alternatif.indices.get(mot, -1) >= 0]
    supplement = [mot for mot in alternatif.jouables if principal.indices.get(mot, -1) < 0]
    grilles = []
    for i in range(graine, graine + parties):
        tirage = random.Random(i)
        commun, externe = tirage.choice(communs), tirage.choice(supplement)
        sondes = tirage.sample(communs, 13)
        if commun in sondes:
            sondes.remove(commun)
        for lot, secret, scenario in (("commun", commun, Scenario.EXACT),
                                      ("etendu", externe, Scenario.EXACT),
                                      ("etendu_bruite", externe, Scenario.BRUIT)):
            # Seul le banc de mesure connaît le secret. Chaque politique reçoit le même oracle sans état.
            source = nouvelle_grille(alternatif, i, [secret], scenario=scenario)
            ouverture = principal.indice(sondes[0])
            politiques = {}
            for methode in (Strategie.PLAN, Strategie.ROBUSTE, *Repli):
                if isinstance(methode, Repli):
                    politique = Secours(principal, principal.lignes_jouables, alternatif,
                                        alternatif.lignes_jouables, 2, 17, methode)
                    resultat = jouer(politique, source, budget, 2, ouverture=ouverture)
                else:
                    resultat = resoudre(principal, source, principal.lignes_jouables, methode,
                                        budget, 2, 17, ouverture=ouverture)
                mots = [e.observation.mot for e in resultat.essais]
                if (len(mots) > budget or len(set(mots)) != len(mots) or mots[0] != sondes[0]
                        or (resultat.statut == "resolu") != (mots[-1] == secret)):
                    raise ValueError("Budget, ouverture ou confirmation incohérents dans le benchmark.")
                politiques[methode.value] = {"statut": resultat.statut, "mots": mots,
                                             "phases": [e.phase for e in resultat.essais if e.phase]}
            mesures = []
            vrai = alternatif.vecteurs[alternatif.indice(secret)].astype(float)
            observations: list[Observation] = [source(m) for m in sondes[:12]]
            scores = [(o.mot, o.temperature) for o in observations if o.temperature is not None]
            for n in (4, 12):
                for penalite in (0.0, 0.01):
                    v, diagnostic = reconstruire(alternatif, scores[:n], penalite)
                    cosinus = (float((v / diagnostic.norme) @ (vrai / np.linalg.norm(vrai)))
                               if diagnostic.norme else None)
                    if cosinus is not None and abs(cosinus) > 1 + 1e-12:
                        raise ValueError("Cosinus de reconstruction incohérent.")
                    mesures.append({"sondes": n, "penalite": penalite, "cosinus_secret": cosinus,
                                    "rang": diagnostic.rang, "residu_rms_c": diagnostic.residu_rms_c,
                                    "condition_sous_espace": diagnostic.condition_sous_espace})
            grilles.append({"graine": i, "lot": lot, "secret": secret, "politiques": politiques,
                            "reconstructions": mesures})
    return {"principal": principal.empreinte_preparation, "alternatif": alternatif.empreinte_preparation,
            "vocabulaire_commun": len(communs), "vocabulaire_supplementaire": len(supplement),
            "budget": budget, "decimales": 2, "grilles": grilles}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path(".modeles"))
    parser.add_argument("--parties", type=int, default=6, help="Grilles par scénario.")
    parser.add_argument("--graine", type=int, default=1700)
    parser.add_argument("--budget", type=int, default=8)
    parser.add_argument("--export", type=Path, required=True)
    args = parser.parse_args()
    principal, alternatif = (Modele(args.cache / nom, source=SOURCES[nom].empreinte)
                             for nom in ("reduit", "original"))
    rapport = evaluer(principal, alternatif, args.parties, args.graine, args.budget)
    with args.export.open("x", encoding="utf-8", newline="\n") as fichier:
        json.dump(rapport, fichier, ensure_ascii=False, allow_nan=False, indent=2)
        fichier.write("\n")


if __name__ == "__main__":
    main()

"""Commandes du moteur local, indépendantes de la CLI de jeu TypeScript."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .benchmark import exporter, mesurer, resumer
from .calibration import calibrer
from .evaluation_inference import evaluer_historiques, evaluer_simulations
from .inference import MARGE_CALIBRATION
from .modele import Modele, cle
from .preparation import preparer
from .resolution import REFERENCES, ROBUSTESSE, SELECTION, Strategie, jouer, resoudre
from .secours import Repli, Secours
from .selection import ouverture_optimisee
from .simulation import Observation, Scenario, nouvelle_grille
from .sources import SOURCES, acquerir


def lire_historique(fichier: Path) -> list[Observation]:
    observations = []
    for numero, ligne in enumerate(fichier.read_text(encoding="utf-8-sig").splitlines(), 1):
        try:
            valeurs = json.loads(ligne)
            observation = Observation(**valeurs)
            if not isinstance(observation.mot, str):
                raise ValueError("mot attendu")
        except (TypeError, ValueError) as erreur:
            raise ValueError(f"Observation invalide à la ligne {numero} de {fichier}.") from erreur
        observations.append(observation)
    return observations


def main() -> int:
    parser = argparse.ArgumentParser(description="Préparer les modèles ou jouer une grille hors ligne.")
    parser.add_argument("--cache", type=Path, default=Path(".modeles"))
    commandes = parser.add_subparsers(dest="action", required=True)
    preparation = commandes.add_parser("preparer", help="Acquérir, vérifier et normaliser un modèle.")
    preparation.add_argument("modele", choices=SOURCES)
    commandes.add_parser("comparer", help="Contrôler les empreintes et comparer les vocabulaires.")
    calibration = commandes.add_parser("calibrer", help="Comparer les modèles sur des parties réelles terminées.")
    calibration.add_argument("corpus", type=Path, help="Corpus JSON avec lots de calibration, validation et test.")
    calibration.add_argument("--export", type=Path, help="Écrire le rapport JSON dans un nouveau fichier UTF-8.")
    evaluation = commandes.add_parser("evaluer-inference", help="Mesurer le rang du secret sur les historiques de test.")
    origine = evaluation.add_mutually_exclusive_group(required=True)
    origine.add_argument("corpus", nargs="?", type=Path)
    origine.add_argument("--simulations", type=int, help="Nombre de grilles à sonder avec trois mots indépendants.")
    evaluation.add_argument("--graine", type=int)
    evaluation.add_argument("--scenario", type=Scenario, choices=list(Scenario))
    evaluation.add_argument("--modele", choices=SOURCES, default="reduit")
    evaluation.add_argument("--export", type=Path, help="Nouveau fichier JSON.")
    simulation = commandes.add_parser("simuler", help="Proposer des mots à une même grille locale.")
    simulation.add_argument("mots", nargs="+")
    resolution = commandes.add_parser("resoudre", help="Résoudre automatiquement une grille locale.")
    resolution.add_argument("--strategie", choices=[*Strategie, "secours"], default=Strategie.EXACTE)
    resolution.add_argument("--modele-source", choices=SOURCES, help="Modèle utilisé pour simuler la grille.")
    resolution.add_argument("--repli", choices=list(Repli), help="Classement après épuisement des deux inversions.")
    resolution.add_argument("--historique", type=Path, help="Observations JSONL de cette grille, au format simuler.")
    benchmark = commandes.add_parser("benchmark", help="Comparer les cinq stratégies sur des grilles appariées.")
    benchmark.add_argument("--parties", type=int, default=100)
    comparaison = benchmark.add_mutually_exclusive_group()
    comparaison.add_argument("--selection", action="store_true", help="Inclure les quatre stratégies du sprint 5.")
    comparaison.add_argument("--robustesse", action="store_true", help="Comparer les pertes et les vraisemblances.")
    benchmark.add_argument("--export", type=Path, help="Nouveau fichier CSV des résultats par partie.")
    for commande in (simulation, resolution, benchmark):
        commande.add_argument("--scenario", type=Scenario, choices=list(Scenario), default=Scenario.EXACT)
        commande.add_argument("--modele", choices=SOURCES, default="reduit")
        commande.add_argument("--graine", type=int, required=True)
        commande.add_argument("--solutions", type=Path, help="Fichier UTF-8, une solution admissible par ligne.")
        commande.add_argument("--decimales", type=int, default=2)
    for commande in (resolution, benchmark, evaluation):
        commande.add_argument("--marge-calibration", type=float, default=MARGE_CALIBRATION,
                              help="Plancher d’échelle du bruit en degrés issu de la calibration.")
    for commande in (resolution, benchmark):
        commande.add_argument("--ouverture", choices=("aleatoire", "entropie", "collisions"), default="aleatoire")
        commande.add_argument("--budget", type=int, default=20)
        commande.add_argument("--graine-choix", type=int, default=17, help="Graine du choix des propositions.")
    args = parser.parse_args()
    try:
        if args.action in ("calibrer", "evaluer-inference"):
            if args.action == "calibrer":
                modeles = {nom: Modele(args.cache / nom, verifier=True, source=s.empreinte)
                           for nom, s in SOURCES.items()}
                mesures_corpus = calibrer(args.corpus, modeles)
            else:
                modele = Modele(args.cache / args.modele, verifier=True, source=SOURCES[args.modele].empreinte)
                if args.simulations is not None:
                    mesures_corpus = evaluer_simulations(modele, args.simulations, args.graine or 0,
                                                         args.scenario or Scenario.BRUIT, args.marge_calibration)
                elif args.graine is not None or args.scenario is not None:
                    raise ValueError("--graine et --scenario concernent uniquement les simulations.")
                else:
                    mesures_corpus = evaluer_historiques(modele, args.corpus, args.marge_calibration)
            rapport = json.dumps(mesures_corpus, ensure_ascii=False, allow_nan=False, indent=2)
            if args.export:
                with args.export.open("x", encoding="utf-8", newline="\n") as sortie:
                    sortie.write(rapport + "\n")
            else:
                print(rapport)
            return 0
        if args.action == "comparer":
            reduit, original = (
                Modele(args.cache / nom, verifier=True, source=SOURCES[nom].empreinte)
                for nom in ("reduit", "original")
            )
            communs = len(reduit.indices.keys() & original.indices.keys())
            print(json.dumps({
                "formes_communes": communs, "propres_au_reduit": len(reduit.indices) - communs,
                "propres_a_original": len(original.indices) - communs,
                "formes_ambigues": {nom: sum(i < 0 for i in m.indices.values())
                                    for nom, m in zip(SOURCES, (reduit, original), strict=True)},
            }, indent=2))
            return 0
        dossier = args.cache / args.modele
        if args.action == "preparer":
            fichier = acquerir(args.modele, args.cache)
            if dossier.exists():
                Modele(dossier, verifier=True, source=SOURCES[args.modele].empreinte)
            else:
                preparer(fichier, dossier, SOURCES[args.modele])
            print((dossier / "rapport.json").read_text(encoding="utf-8"))
        else:
            solutions = args.solutions.read_text(encoding="utf-8-sig").splitlines() if args.solutions else None
            modele = Modele(dossier, source=SOURCES[args.modele].empreinte)
            adaptatif = args.action == "resoudre" and args.strategie == "secours"
            if args.action == "resoudre" and args.repli and not adaptatif:
                raise ValueError("--repli demande la stratégie secours.")
            modeles = {args.modele: modele}

            def charger(nom: str) -> Modele:
                if nom not in modeles:
                    modeles[nom] = Modele(args.cache / nom, source=SOURCES[nom].empreinte)
                return modeles[nom]

            source = charger(args.modele_source or args.modele) if args.action == "resoudre" else modele
            if adaptatif:
                alternatif = charger("original" if args.modele == "reduit" else "reduit")
                admises = source.solutions_admises(solutions) if solutions is not None else None

                def couvertes(m: Modele) -> NDArray[np.intp]:
                    if admises is None:
                        return m.lignes_jouables
                    return np.array([m.indices[mot] for mot in admises if m.indices.get(mot, -1) >= 0],
                                    dtype=np.intp)

                indices = couvertes(modele)
                secours = Secours(modele, indices, alternatif, couvertes(alternatif), args.decimales,
                                  args.graine_choix, Repli(args.repli or Repli.MELANGE), args.marge_calibration)
            historique = lire_historique(args.historique) if args.action == "resoudre" and args.historique else []
            ouverture = None
            if args.action != "simuler" and not historique and args.ouverture != "aleatoire":
                candidats = indices if adaptatif else modele.indices_solutions(solutions)
                if candidats.size:
                    ouverture = ouverture_optimisee(modele, candidats, args.decimales,
                                                    args.ouverture, args.cache / "ouvertures")
            if args.action == "benchmark":
                mesures = mesurer(modele, solutions, args.parties, args.budget,
                                 args.graine, args.graine_choix, args.decimales, ouverture=ouverture,
                                 strategies=ROBUSTESSE if args.robustesse else SELECTION if args.selection else REFERENCES,
                                 scenario=args.scenario, marge=args.marge_calibration)
                if args.export:
                    exporter(mesures, args.export)
                print(json.dumps(resumer(mesures), ensure_ascii=False, indent=2))
                return 0
            proposer = nouvelle_grille(source, args.graine, solutions, args.decimales, args.scenario)
            if args.action == "resoudre":
                for observation in historique:
                    if proposer(observation.mot) != Observation(cle(observation.mot), observation.statut,
                                                                observation.temperature):
                        raise ValueError(f"Historique incompatible avec la grille pour « {observation.mot} ».")
                if adaptatif:
                    resultat = jouer(secours, proposer, args.budget, args.decimales, historique, ouverture)
                else:
                    resultat = resoudre(modele, proposer, modele.indices_solutions(solutions), Strategie(args.strategie),
                                        args.budget, args.decimales, args.graine_choix, historique,
                                        ouverture=ouverture, marge=args.marge_calibration)
                sortie = asdict(resultat)
                for essai in sortie["essais"]:
                    for champ in ("estimation", "motif_bascule", "phase", "scores_inexploitables", "reconstruction"):
                        if essai[champ] is None:
                            del essai[champ]
                print(json.dumps(sortie, ensure_ascii=False, allow_nan=False, indent=2))
                return 0 if resultat.statut == "resolu" else 2
            for mot in args.mots:
                observation = proposer(mot)
                print(json.dumps(asdict(observation), ensure_ascii=False))
                if observation.statut == "victoire":
                    break
    except (OSError, ValueError, KeyError) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

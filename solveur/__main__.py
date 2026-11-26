"""Commandes du moteur local, indépendantes de la CLI de jeu TypeScript."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .benchmark import exporter, mesurer, resumer
from .modele import Modele, cle
from .preparation import preparer
from .resolution import Strategie, resoudre
from .simulation import Observation, nouvelle_grille
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
    simulation = commandes.add_parser("simuler", help="Proposer des mots à une même grille locale.")
    simulation.add_argument("mots", nargs="+")
    resolution = commandes.add_parser("resoudre", help="Résoudre automatiquement une grille locale.")
    resolution.add_argument("--strategie", choices=list(Strategie), default=Strategie.EXACTE)
    resolution.add_argument("--historique", type=Path, help="Observations JSONL de cette grille, au format simuler.")
    benchmark = commandes.add_parser("benchmark", help="Comparer les cinq stratégies sur des grilles appariées.")
    benchmark.add_argument("--parties", type=int, default=100)
    benchmark.add_argument("--export", type=Path, help="Nouveau fichier CSV des résultats par partie.")
    for commande in (simulation, resolution, benchmark):
        commande.add_argument("--modele", choices=SOURCES, default="reduit")
        commande.add_argument("--graine", type=int, required=True)
        commande.add_argument("--solutions", type=Path, help="Fichier UTF-8, une solution admissible par ligne.")
        commande.add_argument("--decimales", type=int, default=2)
    for commande in (resolution, benchmark):
        commande.add_argument("--budget", type=int, default=20)
        commande.add_argument("--graine-choix", type=int, default=17, help="Graine du choix des propositions.")
    args = parser.parse_args()
    try:
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
            if args.action == "benchmark":
                mesures = mesurer(modele, solutions, args.parties, args.budget,
                                 args.graine, args.graine_choix, args.decimales)
                if args.export:
                    exporter(mesures, args.export)
                print(json.dumps(resumer(mesures), ensure_ascii=False, indent=2))
                return 0
            proposer = nouvelle_grille(modele, args.graine, solutions, args.decimales)
            if args.action == "resoudre":
                indices = modele.indices_solutions(solutions)
                historique = lire_historique(args.historique) if args.historique else []
                for observation in historique:
                    if proposer(observation.mot) != Observation(cle(observation.mot), observation.statut,
                                                                observation.temperature):
                        raise ValueError(f"Historique incompatible avec la grille pour « {observation.mot} ».")
                resultat = resoudre(modele, proposer, indices, Strategie(args.strategie),
                                    args.budget, args.decimales, args.graine_choix, historique)
                print(json.dumps(asdict(resultat), ensure_ascii=False, indent=2))
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

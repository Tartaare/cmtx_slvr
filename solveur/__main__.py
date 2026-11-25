"""Commandes du moteur local, indépendantes de la CLI de jeu TypeScript."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .modele import Modele
from .preparation import preparer
from .simulation import nouvelle_grille
from .sources import SOURCES, acquerir


def main() -> int:
    parser = argparse.ArgumentParser(description="Préparer les modèles ou jouer une grille hors ligne.")
    parser.add_argument("--cache", type=Path, default=Path(".modeles"))
    commandes = parser.add_subparsers(dest="action", required=True)
    preparation = commandes.add_parser("preparer", help="Acquérir, vérifier et normaliser un modèle.")
    preparation.add_argument("modele", choices=SOURCES)
    commandes.add_parser("comparer", help="Contrôler les empreintes et comparer les vocabulaires.")
    simulation = commandes.add_parser("simuler", help="Proposer des mots à une même grille locale.")
    simulation.add_argument("mots", nargs="+")
    simulation.add_argument("--modele", choices=SOURCES, default="reduit")
    simulation.add_argument("--graine", type=int, required=True)
    simulation.add_argument("--solutions", type=Path, help="Fichier UTF-8, une solution admissible par ligne.")
    simulation.add_argument("--decimales", type=int, default=2)
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
            proposer = nouvelle_grille(modele, args.graine, solutions, args.decimales)
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

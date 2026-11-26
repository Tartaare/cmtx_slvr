"""Comparaison appariée sur les mêmes grilles simulées."""

import csv
import random
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from statistics import mean, median
from time import perf_counter
from typing import TypedDict

import numpy as np

from .modele import Modele
from .resolution import REFERENCES, Strategie, resoudre
from .simulation import nouvelle_grille


@dataclass(frozen=True)
class Mesure:
    grille: int
    graine_choix: int
    strategie: Strategie
    ouverture: str
    statut: str
    essais: int
    refus: int
    millisecondes: float
    budget: int
    decimales: int
    modele_sha256: str


def mesurer(modele: Modele, solutions: Sequence[str] | None, parties: int, budget: int,
            graine: int, graine_choix: int, decimales: int, *,
            strategies: Sequence[Strategie] = REFERENCES, ouverture: int | None = None) -> list[Mesure]:
    if parties < 1:
        raise ValueError("Il faut au moins une grille.")
    ouvertures = random.Random(graine_choix)
    indices = modele.indices_solutions(solutions)
    mesures = []
    for grille in range(graine, graine + parties):
        source = nouvelle_grille(modele, grille, solutions, decimales)
        choix = ouvertures.getrandbits(63)
        for strategie in strategies:
            debut = perf_counter()
            resultat = resoudre(modele, source, indices, strategie, budget, decimales, choix, ouverture=ouverture)
            duree = round((perf_counter() - debut) * 1000, 3)
            mesures.append(Mesure(grille, choix, strategie, resultat.essais[0].observation.mot,
                                  resultat.statut, len(resultat.essais),
                                  sum(e.observation.statut == "refus" for e in resultat.essais), duree,
                                  budget, decimales, modele.source_sha256))
    return mesures


class Resume(TypedDict):
    parties: int
    resolues: int
    echecs: int
    essais_consommes_moyens: float
    essais_consommes_medians: float
    percentiles_90_95_99_consommes: list[int]
    maximum_consomme: int
    resolues_en_au_plus: dict[int, int]
    refus: int
    ms_par_essai: float


def resumer(mesures: Sequence[Mesure]) -> dict[str, Resume]:
    bilan: dict[str, Resume] = {}
    for strategie in dict.fromkeys(m.strategie for m in mesures):
        groupe = [m for m in mesures if m.strategie == strategie]
        essais = [m.essais for m in groupe]
        succes = [m.essais for m in groupe if m.statut == "resolu"]
        bilan[strategie.value] = {
            "parties": len(groupe), "resolues": len(succes), "echecs": len(groupe) - len(succes),
            "essais_consommes_moyens": mean(essais), "essais_consommes_medians": median(essais),
            "percentiles_90_95_99_consommes": np.percentile(essais, [90, 95, 99], method="higher").tolist(),
            "maximum_consomme": max(essais),
            "resolues_en_au_plus": {n: sum(k <= n for k in succes) for n in (2, 3, 5, 10, 20)},
            "refus": sum(m.refus for m in groupe),
            "ms_par_essai": round(sum(m.millisecondes for m in groupe) / sum(essais), 3),
        }
    return bilan


def exporter(mesures: Sequence[Mesure], fichier: Path) -> None:
    with fichier.open("x", newline="", encoding="utf-8") as flux:
        csv_sortie = csv.DictWriter(flux, [f.name for f in fields(Mesure)], lineterminator="\n")
        csv_sortie.writeheader()
        csv_sortie.writerows(asdict(m) for m in mesures)

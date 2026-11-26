"""Source de scores locale. Le moteur ne reçoit que la fonction de proposition."""

import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal

from .modele import Modele, cle, mot_jouable


@dataclass(frozen=True)
class Observation:
    mot: str
    statut: Literal["score", "victoire", "refus"]
    temperature: float | None


def nouvelle_grille(
    modele: Modele, graine: int, solutions: Iterable[str] | None = None, decimales: int = 2,
) -> Callable[[str], Observation]:
    if not 0 <= decimales <= 6:
        raise ValueError("La précision doit être comprise entre 0 et 6 décimales.")
    secret = random.Random(graine).choice(modele.solutions_admises(solutions))

    def proposer(saisie: str) -> Observation:
        mot = cle(saisie)
        if not mot_jouable(mot) or modele.indices.get(mot, -1) < 0:
            return Observation(mot, "refus", None)
        if mot == secret:
            return Observation(mot, "victoire", 100.0)
        return Observation(mot, "score", round(100 * modele.cosinus(mot, secret), decimales))

    return proposer

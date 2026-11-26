"""Source de scores locale. Le moteur ne reçoit que la fonction de proposition."""

import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from .modele import Modele, cle, mot_jouable


class Scenario(StrEnum):
    EXACT = "exact"
    BRUIT = "bruit"
    ABERRANT = "aberrant"


@dataclass(frozen=True)
class Observation:
    mot: str
    statut: Literal["score", "victoire", "refus"]
    temperature: float | None


def nouvelle_grille(
    modele: Modele, graine: int, solutions: Iterable[str] | None = None, decimales: int = 2,
    scenario: Scenario = Scenario.EXACT,
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
        temperature = 100 * modele.cosinus(mot, secret)
        if scenario != Scenario.EXACT:
            bruit = random.Random(f"temperature:{graine}:{mot}")
            if scenario == Scenario.BRUIT:
                temperature += bruit.gauss(0, 1)
            else:
                temperature += bruit.gauss(0, 0.15)
                if bruit.random() < 0.15:
                    temperature += bruit.choice((-1, 1)) * bruit.uniform(8, 16)
            temperature = min(100, max(-100, temperature))
        return Observation(mot, "score", round(temperature, decimales))

    return proposer

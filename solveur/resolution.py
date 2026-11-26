"""Inversion de scores et stratégies de référence, sans accès au tirage de la grille."""

import math
import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from .modele import Modele, cle
from .selection import discriminant, fin_de_partie
from .simulation import Observation


class Strategie(StrEnum):
    EXACTE = "exacte"
    HASARD = "hasard"
    VOISIN = "voisin"
    COMPTAGE = "comptage"
    CEMANTBOT = "cemantbot"
    ENTROPIE = "entropie"
    COLLISIONS = "collisions"
    PLAN = "plan"
    DECORRELATION = "decorrelation"


REFERENCES = (Strategie.EXACTE, Strategie.HASARD, Strategie.VOISIN, Strategie.COMPTAGE, Strategie.CEMANTBOT)
INVERSION = {Strategie.EXACTE, Strategie.ENTROPIE, Strategie.COLLISIONS, Strategie.PLAN, Strategie.DECORRELATION}


@dataclass(frozen=True)
class Essai:
    observation: Observation
    candidats_exacts: int | None


@dataclass(frozen=True)
class Resultat:
    statut: Literal["resolu", "aucun_candidat", "budget_epuise"]
    essais: tuple[Essai, ...]


class Recherche:
    def __init__(self, modele: Modele, indices: NDArray[np.intp], strategie: Strategie,
                 decimales: int, generateur: random.Random) -> None:
        self.modele = modele
        self.strategie = strategie
        self.decimales = decimales
        self.generateur = generateur
        self.disponibles = np.zeros(len(modele.mots), dtype=bool)
        self.disponibles[indices] = True
        self.admis = self.disponibles.copy()
        self.hist: list[int] = []
        self.comptes: dict[int, int] = {}
        self.voisins: NDArray[np.float32] | None = None
        self.temperature_max = -math.inf

    def choisir(self, budget: int) -> int:
        disponibles = np.flatnonzero(self.disponibles)
        if self.hist:
            if self.strategie == Strategie.EXACTE:
                return int(disponibles[0])
            if self.strategie in INVERSION:
                if disponibles.size == 1 or budget == 1:
                    return int(disponibles[0])
                if self.strategie == Strategie.DECORRELATION:
                    cumul = np.zeros(disponibles.size)
                    for j in self.hist:
                        cumul += np.abs(self.modele.similarites(self.modele.mots[j])[disponibles])
                    return int(disponibles[np.argmin(cumul)])
                if self.strategie == Strategie.PLAN and disponibles.size <= 8:
                    return fin_de_partie(self.modele, disponibles, self.decimales, budget, self.hist)
                critere = "collisions" if self.strategie == Strategie.COLLISIONS else "entropie"
                return discriminant(self.modele, disponibles, self.hist, self.decimales, critere)
            if self.strategie == Strategie.VOISIN and self.voisins is not None:
                return int(disponibles[np.argmax(self.voisins[disponibles])])
            if self.comptes:
                maximum = max(self.comptes.values())
                meilleurs = [i for i, n in self.comptes.items() if n == maximum and self.disponibles[i]]
                if meilleurs:
                    if self.strategie == Strategie.COMPTAGE:
                        return meilleurs[0]
                    vecteurs = self.modele.vecteurs
                    return min(meilleurs, key=lambda i: float(np.mean(
                        [abs(vecteurs[i] @ vecteurs[j]) for j in self.hist]
                    )))
        return int(self.generateur.choice(disponibles))

    def observer(self, indice: int, obs: Observation) -> None:
        self.hist.append(indice)
        self.disponibles[indice] = False
        if obs.statut != "score" or obs.temperature is None or self.strategie == Strategie.HASARD:
            return
        if self.strategie in INVERSION:
            self.filtrer(obs.mot, obs.temperature)
        elif self.strategie == Strategie.VOISIN:
            if obs.temperature > self.temperature_max:
                self.temperature_max = obs.temperature
                self.voisins = self.modele.similarites(obs.mot)
        else:
            scores = self.modele.similarites(obs.mot)
            for ligne in np.flatnonzero(np.abs(scores - obs.temperature / 100) <= 1e-4):
                i = int(ligne)
                if i != indice and self.admis[i]:
                    self.comptes[i] = self.comptes.get(i, 0) + 1

    def filtrer(self, mot: str, temperature: float) -> None:
        candidats = np.flatnonzero(self.disponibles)
        if candidats.size > 256:
            scores = self.modele.similarites(mot)[candidats].astype(np.float64)
            # Deux produits float32 peuvent accumuler leurs erreurs dans des sens opposés.
            # Ce préfiltre large précède le calcul scalaire identique à celui de la source.
            marge = 4 * self.modele.vecteurs.shape[1] * float(np.finfo(np.float32).eps)
            rayon = 0.5 * 10 ** (-self.decimales) / 100 + marge
            candidats = candidats[np.abs(scores - temperature / 100) <= rayon]
        self.disponibles.fill(False)
        for i in candidats:
            cosinus = self.modele.cosinus(mot, self.modele.mots[i])
            self.disponibles[i] = round(100 * cosinus, self.decimales) == temperature


def resoudre(modele: Modele, source: Callable[[str], Observation], indices: NDArray[np.intp],
             strategie: Strategie, budget: int, decimales: int, graine_choix: int,
             historique: Iterable[Observation] = (), *, ouverture: int | None = None) -> Resultat:
    if budget < 1 or not 0 <= decimales <= 6:
        raise ValueError("Budget positif et précision de 0 à 6 décimales requis.")
    recherche = Recherche(modele, indices, strategie, decimales, random.Random(f"choix:{graine_choix}"))
    essais: list[Essai] = []

    deja_joues: set[str] = set()

    def enregistrer(proposition: str, obs: Observation) -> None:
        mot = cle(proposition)
        if cle(obs.mot) != mot or obs.statut not in ("score", "refus", "victoire"):
            raise ValueError("La réponse ne correspond pas au mot proposé ou au statut attendu.")
        if mot in deja_joues:
            raise ValueError(f"Proposition répétée : {mot}.")
        if obs.statut == "refus":
            if obs.temperature is not None:
                raise ValueError("Un refus doit être dépourvu de température.")
        elif (type(obs.temperature) not in (float, int) or not -100 <= obs.temperature <= 100
              or round(obs.temperature, decimales) != obs.temperature
              or (obs.statut == "victoire" and obs.temperature != 100)):
            raise ValueError("Température incohérente avec le statut ou la précision.")
        if obs.statut != "refus" or modele.indices.get(mot, -1) >= 0:
            recherche.observer(modele.indice(mot), obs)
        deja_joues.add(mot)
        restants = int(recherche.disponibles.sum()) if strategie in INVERSION else None
        essais.append(Essai(obs, restants if obs.statut != "victoire" else None))

    for obs in historique:
        if len(essais) >= budget or (essais and essais[-1].observation.statut == "victoire"):
            raise ValueError("Historique incohérent avec le budget ou la fin de partie.")
        enregistrer(obs.mot, obs)
    while not essais or essais[-1].observation.statut != "victoire":
        if not recherche.disponibles.any():
            return Resultat("aucun_candidat", tuple(essais))
        if len(essais) >= budget:
            return Resultat("budget_epuise", tuple(essais))
        restants = budget - len(essais)
        if not essais and ouverture is not None and (restants > 1 or recherche.admis[ouverture]):
            indice = ouverture
        else:
            indice = recherche.choisir(restants)
        mot = modele.mots[indice]
        enregistrer(mot, source(mot))
    return Resultat("resolu", tuple(essais))

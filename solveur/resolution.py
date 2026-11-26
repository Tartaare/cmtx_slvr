"""Inversion de scores et stratégies de référence, sans accès au tirage de la grille."""

import math
import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from .inference import Estimation, Inference, MARGE_CALIBRATION, Methode
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
    ROBUSTE = "robuste"
    ABSOLUE = "absolue"
    QUADRATIQUE = "quadratique"
    HUBER = "huber"
    GAUSSE = "gaussienne"
    LAPLACE = "laplace"
    STUDENT = "student"
    MELANGE = "melange"


REFERENCES = (Strategie.EXACTE, Strategie.HASARD, Strategie.VOISIN, Strategie.COMPTAGE, Strategie.CEMANTBOT)
SELECTION = (*REFERENCES, Strategie.ENTROPIE, Strategie.COLLISIONS, Strategie.PLAN, Strategie.DECORRELATION)
ROBUSTESSE = (Strategie.EXACTE, Strategie.CEMANTBOT, Strategie.COMPTAGE,
              *(Strategie(m.value) for m in Methode), Strategie.ROBUSTE)
INVERSION = {Strategie.EXACTE, Strategie.ENTROPIE, Strategie.COLLISIONS, Strategie.PLAN, Strategie.DECORRELATION}


@dataclass(frozen=True)
class Essai:
    observation: Observation
    candidats_exacts: int | None
    estimation: Estimation | None = None
    motif_bascule: Literal["aucun_candidat_exact"] | None = None


@dataclass(frozen=True)
class Resultat:
    statut: Literal["resolu", "aucun_candidat", "budget_epuise"]
    essais: tuple[Essai, ...]


class Recherche:
    def __init__(self, modele: Modele, indices: NDArray[np.intp], strategie: Strategie,
                 decimales: int, generateur: random.Random, marge: float = MARGE_CALIBRATION) -> None:
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
        self.marge = marge
        self.avant_bascule: list[tuple[str, float]] = []
        self.inference = (Inference(modele, indices, Methode(strategie.value), decimales, marge)
                          if strategie.value in Methode else None)

    @property
    def filtre_exact(self) -> bool:
        return self.strategie in INVERSION or (self.strategie == Strategie.ROBUSTE and self.inference is None)

    def choisir(self, budget: int) -> int:
        disponibles = np.flatnonzero(self.disponibles)
        if self.hist:
            if self.inference is not None and self.inference.observations:
                indices, valeurs = self.inference.classement(self.disponibles)
                return int(indices[np.argmax(valeurs)])
            if self.strategie in (Strategie.EXACTE, Strategie.ROBUSTE):
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
        if self.strategie == Strategie.ROBUSTE and self.inference is None:
            if obs.statut == "score" and obs.temperature is not None:
                self.avant_bascule.append((obs.mot, obs.temperature))
                self.filtrer(obs.mot, obs.temperature)
            if obs.statut != "victoire" and not self.disponibles.any():
                self.disponibles = self.admis.copy()
                self.disponibles[self.hist] = False
                self.inference = Inference(self.modele, np.flatnonzero(self.admis), Methode.MELANGE,
                                           self.decimales, self.marge)
                for mot, temp in self.avant_bascule:
                    self.inference.ajouter(mot, temp)
                self.avant_bascule.clear()
            return
        if obs.statut != "score" or obs.temperature is None or self.strategie == Strategie.HASARD:
            return
        if self.inference is not None:
            self.inference.ajouter(obs.mot, obs.temperature)
        elif self.strategie in INVERSION:
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
             historique: Iterable[Observation] = (), *, ouverture: int | None = None,
             marge: float = MARGE_CALIBRATION) -> Resultat:
    if budget < 1 or not 0 <= decimales <= 6:
        raise ValueError("Budget positif et précision de 0 à 6 décimales requis.")
    if not math.isfinite(marge) or not 0 <= marge <= 100:
        raise ValueError("La marge de calibration doit être comprise entre 0 et 100 °C.")
    recherche = Recherche(modele, indices, strategie, decimales, random.Random(f"choix:{graine_choix}"), marge)
    essais: list[Essai] = []

    deja_joues: set[str] = set()

    def enregistrer(proposition: str, obs: Observation) -> None:
        mot = cle(proposition)
        etait_exact = recherche.filtre_exact
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
        restants = int(recherche.disponibles.sum()) if recherche.filtre_exact and obs.statut != "victoire" else None
        estimation = (recherche.inference.estimation(recherche.disponibles)
                      if recherche.inference is not None and obs.statut != "victoire" else None)
        motif = "aucun_candidat_exact" if etait_exact and not recherche.filtre_exact else None
        essais.append(Essai(obs, restants, estimation, motif))

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

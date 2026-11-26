"""Résolution adaptative avec rejeu lexical des observations à chaque changement de modèle."""

import math
import random
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from .inference import MARGE_CALIBRATION
from .modele import Modele, cle
from .reconstruction import Diagnostic, plus_proche, reconstruire
from .resolution import Essai, Recherche, Strategie
from .simulation import Observation


class Repli(StrEnum):
    MELANGE = "melange"
    RECONSTRUCTION = "reconstruction"


class Secours:
    def __init__(self, principal: Modele, indices: NDArray[np.intp], alternatif: Modele,
                 indices_alternatifs: NDArray[np.intp], decimales: int, graine: int,
                 repli: Repli = Repli.MELANGE, marge: float = MARGE_CALIBRATION) -> None:
        if not math.isfinite(marge) or not 0 <= marge <= 100:
            raise ValueError("La marge de calibration doit être comprise entre 0 et 100 °C.")
        self.generateur = random.Random(f"choix:{graine}")
        self.alternatif = alternatif
        self.indices_alternatifs = indices_alternatifs
        self.repli = repli
        self.decimales = decimales
        self.marge = marge
        self.historique: list[Observation] = []
        self.scores: list[tuple[str, float]] = []
        self.inexploitables = 0
        self.direction: NDArray[np.float64] | None = None
        self.diagnostic: Diagnostic | None = None
        self.phase = "exact_principal" if indices.size else "exact_alternatif"
        self.recherche = (Recherche(principal, indices, Strategie.PLAN, decimales, self.generateur)
                          if indices.size else self._alternative(Strategie.PLAN))

    def _alternative(self, strategie: Strategie) -> Recherche:
        return Recherche(self.alternatif, self.indices_alternatifs, strategie, self.decimales,
                         self.generateur, self.marge)

    @property
    def epuisee(self) -> bool:
        return self.recherche.epuisee

    def prochain(self, budget: int, ouverture: int | None) -> str:
        recherche = self.recherche
        if self.direction is not None:
            i = plus_proche(recherche.modele, np.flatnonzero(recherche.disponibles), self.direction)
            return recherche.modele.mots[i]
        return recherche.prochain(budget, ouverture if self.phase == "exact_principal" else None)

    def _appliquer(self, obs: Observation) -> None:
        recherche = self.recherche
        i = recherche.modele.indices.get(cle(obs.mot), -1)
        if i < 0:
            self.inexploitables += int(obs.statut == "score")
            return
        if obs.statut == "score" and obs.temperature is not None:
            self.scores.append((obs.mot, obs.temperature))
        recherche.observer(i, obs)

    def _rejouer(self, phase: str, strategie: Strategie) -> None:
        self.phase = phase
        self.recherche = self._alternative(strategie)
        self.scores.clear()
        self.inexploitables = 0
        for obs in self.historique:
            self._appliquer(obs)

    def enregistrer(self, obs: Observation) -> Essai:
        self.historique.append(obs)
        if obs.statut == "victoire":
            return Essai(obs, None, phase=self.phase, scores_inexploitables=self.inexploitables)
        self._appliquer(obs)
        motifs: list[str] = []
        if self.phase == "exact_principal":
            mot = cle(obs.mot)
            sonde_absente = (obs.statut == "score" and self.recherche.modele.indices.get(mot, -1) < 0
                             and self.alternatif.indices.get(mot, -1) >= 0)
            if self.epuisee or sonde_absente:
                motifs.append("sonde_absente_du_principal" if sonde_absente else "principal_sans_candidat")
                self._rejouer("exact_alternatif", Strategie.PLAN)
        if self.phase == "exact_alternatif" and self.epuisee:
            motifs.append("alternatif_sans_candidat")
            # HASARD ne fait ici que retirer les mots joués. La direction classe les mots restants.
            strategie = Strategie.MELANGE if self.repli == Repli.MELANGE else Strategie.HASARD
            self._rejouer(self.repli.value, strategie)
        if self.phase == Repli.RECONSTRUCTION and self.scores and not self.epuisee:
            self.direction, self.diagnostic = reconstruire(self.alternatif, self.scores)
        recherche = self.recherche
        restants = int(recherche.disponibles.sum()) if recherche.filtre_exact else None
        estimation = recherche.inference.estimation(recherche.disponibles) if recherche.inference else None
        return Essai(obs, restants, estimation, "+".join(motifs) or None, self.phase,
                     self.inexploitables, self.diagnostic)

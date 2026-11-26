"""Classement par pertes cumulées ou vraisemblance des températures affichées."""

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from .modele import Modele


class Methode(StrEnum):
    ABSOLUE = "absolue"
    QUADRATIQUE = "quadratique"
    HUBER = "huber"
    GAUSSE = "gaussienne"
    LAPLACE = "laplace"
    STUDENT = "student"
    MELANGE = "melange"


PERTES = {Methode.ABSOLUE, Methode.QUADRATIQUE, Methode.HUBER}
# P95 du sprint 4 arrondi vers le haut pour les deux modèles livrés, en degrés.
MARGE_CALIBRATION = 0.0047
type Vecteur = NDArray[np.float64]


def log_queue_normale(z: Vecteur) -> Vecteur:
    """log(P(Z >= z)) pour z >= 0. La queue asymptotique évite le sous-flux."""
    resultat = np.empty_like(z)
    proche = z < 26
    resultat[proche] = np.fromiter((math.log(0.5 * math.erfc(x)) for x in z[proche] / math.sqrt(2)),
                                   dtype=np.float64, count=int(proche.sum()))
    loin = z[~proche]
    inv = 1 / loin**2
    resultat[~proche] = (-0.5 * loin**2 - np.log(loin) - 0.5 * math.log(2 * math.pi)
                         + np.log1p(-inv + 3 * inv**2 - 15 * inv**3))
    return resultat


def log_masse(methode: Methode, residus: Vecteur, rayon: float, echelle: float, borne: bool) -> Vecteur:
    """Masse dans la case d’arrondi. À ±100 °C, la case comprend la queue écrêtée."""
    a = (np.abs(residus) - rayon) / echelle
    b = (np.abs(residus) + rayon) / echelle
    if methode == Methode.MELANGE:
        return np.logaddexp(math.log(0.95) + log_masse(Methode.LAPLACE, residus, rayon, echelle, borne),
                            math.log(0.05) + log_masse(Methode.STUDENT, residus, rayon, max(5, 8*echelle), borne))
    if methode == Methode.STUDENT:  # Student à un degré de liberté (Cauchy).
        angle = np.arctan2(1.0, a) if borne else np.arctan2(2 * rayon / echelle, 1 + a*b)
        return np.log(angle / math.pi)
    if methode == Methode.LAPLACE:
        if borne:
            return np.where(a >= 0, -math.log(2) - a, np.log1p(-0.5 * np.exp(np.minimum(a, 0))))
        resultat = -math.log(2) - a + math.log(-math.expm1(-2 * rayon / echelle))
        centre = a < 0
        resultat[centre] = np.log(-0.5 * (np.expm1(a[centre]) + np.expm1(-b[centre])))
        return resultat
    if methode != Methode.GAUSSE:
        raise ValueError("La méthode demandée doit définir une vraisemblance.")
    queue = log_queue_normale(np.abs(a))
    if borne:
        return np.where(a >= 0, queue, np.log1p(-np.exp(queue)))
    autre = log_queue_normale(b)
    resultat = np.empty_like(a)
    cote = a >= 0
    resultat[cote] = queue[cote] + np.log(-np.expm1(autre[cote] - queue[cote]))
    resultat[~cote] = np.log(-np.expm1(np.logaddexp(queue[~cote], autre[~cote])))
    return resultat


@dataclass(frozen=True)
class Estimation:
    mot: str
    probabilite_estimee: float | None
    echelle_estimee_c: float | None
    observation_plus_ecartee: str
    ecart_hors_arrondi_c: float


class Inference:
    def __init__(self, modele: Modele, indices: NDArray[np.intp], methode: Methode,
                 decimales: int, marge: float = MARGE_CALIBRATION) -> None:
        if not math.isfinite(marge) or not 0 <= marge <= 100 or not 0 <= decimales <= 6:
            raise ValueError("Marge attendue de 0 à 100 °C et précision de 0 à 6 décimales.")
        self.modele = modele
        self.indices = np.unique(indices)
        self.methode = methode
        self.rayon = 0.5 * 10**-decimales
        base = max(self.rayon, marge)
        self.echelles = np.unique(np.maximum(base, [0, 0.25, 1, 4]))
        self.scores = np.zeros((1 if methode in PERTES else len(self.echelles), len(self.indices)))
        self.observations: list[tuple[str, float]] = []

    def ajouter(self, mot: str, temperature: float) -> None:
        predictions = self.modele.similarites(mot)[self.indices].astype(np.float64) * 100
        residus = temperature - predictions
        if self.methode in PERTES:
            ecart = np.maximum(0, np.abs(residus) - self.rayon)
            if self.methode == Methode.QUADRATIQUE:
                perte = ecart**2
            elif self.methode == Methode.HUBER:
                perte = np.where(ecart <= 1, ecart**2 / 2, ecart - 0.5)
            else:
                perte = ecart
            self.scores[0] -= perte
        else:
            for ligne, echelle in zip(self.scores, self.echelles, strict=True):
                ligne += log_masse(self.methode, residus, self.rayon, float(echelle), abs(temperature) == 100)
        self.observations.append((mot, temperature))

    def classement(self, disponibles: NDArray[np.bool_]) -> tuple[NDArray[np.intp], Vecteur]:
        masque = disponibles[self.indices]
        valeurs = np.logaddexp.reduce(self.scores[:, masque], axis=0)
        return self.indices[masque], valeurs

    def estimation(self, disponibles: NDArray[np.bool_]) -> Estimation | None:
        indices, valeurs = self.classement(disponibles)
        if not indices.size or not self.observations:
            return None
        pos = int(np.argmax(valeurs))
        mot = self.modele.mots[indices[pos]]
        p = echelle = None
        if self.methode not in PERTES:
            p = float(1 / np.exp(valeurs - valeurs[pos]).sum())
            masses = np.logaddexp.reduce(self.scores[:, disponibles[self.indices]], axis=1)
            poids = np.exp(masses - masses.max())
            echelle = float(poids @ self.echelles / poids.sum())
        ecarts = [(max(0.0, abs(temp - self.modele.cosinus(mot, m) * 100) - self.rayon), m)
                  for m, temp in self.observations]
        ecart, essai = max(ecarts)
        return Estimation(mot, p, echelle, essai, ecart)

"""Direction du secret estimée dans le sous-espace des sondes d'un seul modèle."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .modele import Modele


@dataclass(frozen=True)
class Diagnostic:
    observations: int
    dimensions: int
    rang: int
    condition_sous_espace: float
    residu_rms_c: float
    norme: float


def reconstruire(modele: Modele, scores: list[tuple[str, float]], penalite: float = 0.01
                 ) -> tuple[NDArray[np.float64], Diagnostic]:
    """SVD compacte. Une pénalité nulle donne la solution des moindres carrés de norme minimale."""
    if not scores or not np.isfinite(penalite) or penalite < 0:
        raise ValueError("Une observation au moins et une pénalité positive ou nulle sont requises.")
    sondes = modele.vecteurs[[modele.indice(mot) for mot, _ in scores]].astype(np.float64)
    cible = np.array([t / 100 for _, t in scores])
    gauche, valeurs, droite = np.linalg.svd(sondes, full_matrices=False)
    seuil = valeurs[0] * max(sondes.shape) * np.finfo(float).eps
    rang = int(np.count_nonzero(valeurs > seuil))
    s = valeurs[:rang]
    projection = gauche[:, :rang].T @ cible
    vecteur = droite[:rang].T @ ((s / (s*s + penalite)) * projection)
    erreur = 100 * (sondes @ vecteur - cible)
    return vecteur, Diagnostic(len(scores), sondes.shape[1], rang, float(s[0] / s[-1]),
                               float(np.sqrt(np.mean(erreur**2))), float(np.linalg.norm(vecteur)))


def plus_proche(modele: Modele, candidats: NDArray[np.intp], direction: NDArray[np.float64]) -> int:
    # Les lignes sont normalisées. Le produit scalaire suffit pour classer par cosinus.
    scores = modele.vecteurs @ direction.astype(np.float32)
    return int(candidats[np.argmax(scores[candidats])])

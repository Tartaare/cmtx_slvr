"""Vocabulaire indexé et similarités cosinus sur une matrice en lecture seule."""

import json
import re
import unicodedata
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .sources import empreinte


def cle(mot: str) -> str:
    return unicodedata.normalize("NFC", mot.strip().lower()).replace("’", "'")


def mot_jouable(mot: str) -> bool:
    return all(partie.isalpha() for partie in re.split("[-']", mot))


class Modele:
    def __init__(self, dossier: Path, *, verifier: bool = False, source: str | None = None) -> None:
        rapport = json.loads((dossier / "rapport.json").read_text(encoding="utf-8"))
        if rapport["format"] != 1 or rapport["precision"] != "<f4":
            raise ValueError("Format de modèle préparé inconnu.")
        if source is not None and rapport["source_sha256"] != source:
            raise ValueError("Le cache correspond à une autre version du modèle.")
        if verifier:
            for nom, champ in (("vecteurs.f32", "vecteurs_sha256"), ("mots.txt", "mots_sha256")):
                if empreinte(dossier / nom) != rapport[champ]:
                    raise ValueError(f"Empreinte incorrecte pour {dossier / nom}.")
        self.mots = tuple((dossier / "mots.txt").read_text(encoding="utf-8").splitlines())
        n, d = rapport["mots"], rapport["dimensions"]
        fichier = dossier / "vecteurs.f32"
        if len(self.mots) != n or min(n, d) < 1 or fichier.stat().st_size != 4 * n * d:
            raise ValueError("La matrice et le vocabulaire sont incohérents.")
        self.vecteurs: NDArray[np.float32] = np.memmap(fichier, dtype="<f4", mode="r", shape=(n, d))
        self.indices: dict[str, int] = {}
        for i, mot in enumerate(self.mots):
            forme = cle(mot)
            # Une collision reste ambiguë. Les deux vecteurs gardent leur ligne originale.
            self.indices[forme] = -1 if forme in self.indices else i

    def indice(self, mot: str) -> int:
        i = self.indices.get(cle(mot))
        if i is None:
            raise ValueError(f"Mot absent du modèle local : {mot}.")
        if i < 0:
            raise ValueError(f"Plusieurs formes du modèle correspondent à « {mot} ».")
        return i

    def cosinus(self, premier: str, second: str) -> float:
        a, b = self.indice(premier), self.indice(second)
        return float(np.clip(self.vecteurs[a] @ self.vecteurs[b], -1.0, 1.0))

    def similarites(self, mot: str, candidats: Sequence[int] | None = None) -> NDArray[np.float32]:
        """Calcule une colonne de scores. Les indices désignent les lignes du lexique."""
        requete = self.vecteurs[self.indice(mot)]
        matrice = self.vecteurs if candidats is None else self.vecteurs[list(candidats)]
        return np.clip(matrice @ requete, -1.0, 1.0)

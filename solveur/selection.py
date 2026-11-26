"""Choix de propositions dans un ensemble de solutions équiprobables."""

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from .modele import Modele


type Critere = Literal["entropie", "collisions"]
type Indices = NDArray[np.intp]
VICTOIRE = 2**30  # Hors de l’intervalle de température, même à six décimales.


def echantillon(indices: Indices, limite: int) -> Indices:
    if len(indices) <= limite:
        return indices
    # Tirage fixe indépendant du secret et des graines du benchmark.
    return np.sort(np.random.default_rng(5701).choice(indices, limite, replace=False))


@dataclass(frozen=True)
class Qualite:
    indice: int
    entropie_bits: float
    collision: float
    solution: bool
    groupes: int

    def ordre(self, critere: Critere) -> tuple[float, bool, int]:
        valeur = -self.entropie_bits if critere == "entropie" else self.collision
        return valeur, not self.solution, self.indice


def classes_scores(similarites: NDArray[np.float32], decimales: int) -> NDArray[np.int32]:
    return np.rint(np.clip(similarites, -1, 1).astype(np.float64) * (100 * 10**decimales)).astype(np.int32)


def evaluer(modele: Modele, candidats: Indices, propositions: Iterable[int],
            decimales: int) -> Iterable[Qualite]:
    # Les petits ensembles sont contigus. Sur le grand vocabulaire, les produits
    # ligne par ligne parcourent la matrice mappée sans en faire une copie entière.
    matrice = modele.vecteurs[candidats] if len(candidats) <= 4096 else None
    for i in propositions:
        i = int(i)
        if matrice is None:
            sims = np.vecdot(modele.vecteurs, modele.vecteurs[i])[candidats]
        else:
            sims = np.vecdot(matrice, modele.vecteurs[i])
        classes = classes_scores(sims, decimales)
        victoire = candidats == i
        classes[victoire] = VICTOIRE
        _, tailles = np.unique(classes, return_counts=True)
        n = len(candidats)
        p = np.sort(tailles).astype(np.float64) / n
        yield Qualite(i, -float(p @ np.log2(p)), float(p @ p), bool(np.any(victoire)), len(p))


def discriminant(modele: Modele, candidats: Indices, joues: list[int],
                decimales: int, critere: Critere) -> int:
    meilleur: Qualite | None = None

    def examiner(propositions: Indices) -> bool:
        nonlocal meilleur
        for choix in evaluer(modele, candidats, propositions, decimales):
            if meilleur is None or choix.ordre(critere) < meilleur.ordre(critere):
                meilleur = choix
            if choix.groupes == len(candidats):
                return True  # Partition parfaite. Les propositions candidates sont évaluées en premier.
        return False

    if not examiner(echantillon(candidats, 128)):
        sondes = modele.lignes_jouables
        if len(candidats) > 8:
            sondes = echantillon(sondes, 128)
        if len(candidats) > 8 or len(np.unique(modele.vecteurs[candidats], axis=0)) > 1:
            examiner(np.setdiff1d(sondes, np.union1d(candidats, joues)))
    assert meilleur is not None
    return meilleur.indice


def fin_de_partie(modele: Modele, candidats: Indices, decimales: int, budget: int, joues: list[int]) -> int:
    """Compare les arbres de propositions candidates et une sonde initiale, sur huit secrets au plus."""
    n = len(candidats)
    reponses = [[round(100 * modele.cosinus(modele.mots[i], modele.mots[j]), decimales)
                 for j in candidats] for i in candidats]

    @lru_cache(maxsize=None)
    def explorer(restants: tuple[int, ...], coups: int) -> tuple[int, int, int]:
        # Maximiser les victoires sous budget, puis minimiser la somme des essais consommés.
        meilleur = (-1, 0, 0)
        for i in restants:
            groupes: dict[float, list[int]] = {}
            for j in restants:
                if j != i:
                    groupes.setdefault(reponses[i][j], []).append(j)
            resolues, cout = 1, len(restants)
            if coups > 1:
                for groupe in groupes.values():
                    succes, moins_cout, _ = explorer(tuple(groupe), min(coups - 1, len(groupe)))
                    resolues += succes
                    cout -= moins_cout
            meilleur = max(meilleur, (resolues, -cout, -i))
        return meilleur

    succes, cout, moins_i = explorer(tuple(range(n)), min(budget, n))
    meilleur, indice = (succes, cout), int(candidats[-moins_i])
    # Une sonde extérieure coûte au moins deux essais pour chaque victoire.
    if budget == 1 or meilleur >= (n, -2 * n):
        return indice
    vecteurs = modele.vecteurs[candidats]
    if len(np.unique(vecteurs, axis=0)) == 1:
        return indice
    sondes = np.setdiff1d(modele.lignes_jouables, np.union1d(candidats, joues))
    for debut in range(0, len(sondes), 256):
        bloc = sondes[debut:debut + 256]
        scores = classes_scores(np.vecdot(modele.vecteurs[bloc, None, :], vecteurs), decimales)
        parfaites = np.all(np.diff(np.sort(scores, axis=1), axis=1) != 0, axis=1)
        if parfaites.any():
            return int(bloc[np.flatnonzero(parfaites)[0]])
        for sonde, ligne in zip(bloc, scores, strict=True):
            groupes: dict[int, list[int]] = {}
            for j, classe in enumerate(ligne):
                groupes.setdefault(int(classe), []).append(j)
            if len(groupes) == 1:
                continue
            succes, cout = 0, -n
            for groupe in groupes.values():
                s, c, _ = explorer(tuple(groupe), min(budget - 1, len(groupe)))
                succes += s
                cout += c
            if (succes, cout) > meilleur:
                meilleur, indice = (succes, cout), int(sonde)
    return indice


def ouverture_optimisee(modele: Modele, candidats: Indices, decimales: int, critere: Critere,
                       dossier: Path) -> int:
    if not 0 <= decimales <= 6 or not len(candidats):
        raise ValueError("La sélection exige des candidats et une précision de 0 à 6 décimales.")
    candidats = np.unique(candidats)
    signature = hashlib.sha256(candidats.astype("<i8", copy=False).tobytes()).hexdigest()
    cle = f"v2-{modele.empreinte_preparation}-{signature}-{decimales}"
    fichier = dossier / f"{cle}.json"
    if fichier.exists():
        try:
            cache = json.loads(fichier.read_text(encoding="utf-8"))
            if cache["cle"] == cle and isinstance(mot := cache[critere][0]["mot"], str):
                i = modele.indice(mot)
                if i in modele.lignes_jouables:
                    return i
        except (ValueError, KeyError, TypeError, IndexError):
            pass  # Un cache incomplet peut être recalculé à partir du modèle.
    propositions = np.union1d(echantillon(candidats, 128), echantillon(modele.lignes_jouables, 128))
    qualites = list(evaluer(modele, candidats, propositions, decimales))

    def classement(methode: Critere) -> list[dict[str, str | float | int | bool]]:
        return [{"mot": modele.mots[q.indice], "groupes": q.groupes, "solution": q.solution,
                 "entropie_bits": q.entropie_bits, "collision": q.collision}
                for q in sorted(qualites, key=lambda q: q.ordre(methode))[:5]]

    cache = {"cle": cle, "solutions": len(candidats), "propositions_evaluees": len(propositions),
             "entropie": classement("entropie"), "collisions": classement("collisions")}
    dossier.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=dossier, delete=False) as flux:
        temporaire = Path(flux.name)
    try:
        temporaire.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporaire, fichier)
    finally:
        temporaire.unlink(missing_ok=True)
    return min(qualites, key=lambda q: q.ordre(critere)).indice

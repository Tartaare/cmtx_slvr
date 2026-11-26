"""Préparer hors ligne la carte livrée au navigateur (python -m solveur.galaxie)."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from umap import UMAP

from .modele import Modele

GRAINE = 21


def voisins(points: NDArray, echantillon: NDArray, metrique: str) -> NDArray:
    index = NearestNeighbors(n_neighbors=11, metric=metrique).fit(points)
    indices = index.kneighbors(points[echantillon], return_distance=False)
    return np.array([ligne[ligne != i][:10] for i, ligne in zip(echantillon, indices)])


def preparer(dossier: Path, sortie: Path) -> None:
    modele = Modele(dossier, verifier=True)
    mots = modele.jouables
    vecteurs = modele.vecteurs[modele.lignes_jouables]
    print(f"{len(mots)} mots × {vecteurs.shape[1]} dimensions", flush=True)
    projection = UMAP(n_components=3, metric="cosine", n_neighbors=20, min_dist=0.12,
                      random_state=GRAINE, n_jobs=1).fit_transform(vecteurs)
    pca = PCA(n_components=3, svd_solver="full").fit_transform(vecteurs)
    indices = np.random.default_rng(GRAINE).choice(len(mots), size=min(512, len(mots)), replace=False)
    reference = voisins(vecteurs, indices, "cosine")
    for methode, points in (("UMAP", projection), ("PCA", pca)):
        proches = voisins(points, indices, "euclidean")
        rappel = np.mean([len(set(a) & set(b)) / 10 for a, b in zip(reference, proches)])
        print(f"{methode} rappel@10 sur {len(indices)} mots : {rappel:.4f}")
    # Aligner les axes pour cadrer la plus grande étendue horizontalement.
    xyz = PCA(n_components=3, svd_solver="full").fit_transform(projection)
    xyz -= (xyz.max(axis=0) + xyz.min(axis=0)) / 2
    positions = np.rint(xyz / abs(xyz).max() * 10000).astype(int)
    groupes = MiniBatchKMeans(n_clusters=16, batch_size=2048, random_state=GRAINE,
                              n_init=3).fit(vecteurs)
    centres = [xyz[groupes.labels_ == i].mean(axis=0) for i in range(16)]
    ordre = np.argsort([np.arctan2(y, x) for x, y, _ in centres])
    rang = np.argsort(ordre)
    reperes = []
    for i in ordre:
        membres = np.flatnonzero(groupes.labels_ == i)
        reperes.append(int(membres[np.argmax(vecteurs[membres] @ groupes.cluster_centers_[i])]))
    lignes = [[mot, *position, int(rang[g])] for mot, position, g in
              zip(mots, positions.tolist(), groupes.labels_)]
    donnees = dict(format=1, modele=modele.empreinte_preparation, dimensions=vecteurs.shape[1],
                   methode="UMAP", reperes=reperes, mots=lignes)
    contenu = json.dumps(donnees, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    temporaire = sortie.with_suffix(".tmp")
    temporaire.write_bytes(contenu)
    temporaire.replace(sortie)
    print(f"{sortie} · SHA-256 {hashlib.sha256(contenu).hexdigest()}")
    for mot in ("chien", "piano", "rivière"):
        if mot in modele.indices:
            i = mots.index(mot)
            proches = np.argsort(np.linalg.norm(xyz - xyz[i], axis=1))[1:6]
            print(mot, [mots[j] for j in proches])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modele", type=Path, default=Path(".modeles/reduit"))
    parser.add_argument("--sortie", type=Path, default=Path("interface/atlas.json"))
    args = parser.parse_args()
    preparer(args.modele, args.sortie)

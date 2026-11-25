"""Conversion en flux du Word2Vec binaire vers une matrice contiguë sur disque."""

import hashlib
import json
import mmap
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from .sources import Source, empreinte


def preparer(fichier: Path, destination: Path, source: Source) -> None:
    """La destination devient visible seulement après conversion intégrale."""
    if destination.exists():
        raise FileExistsError(f"Le modèle préparé existe déjà dans {destination}.")
    with fichier.open("rb") as flux, mmap.mmap(flux.fileno(), 0, access=mmap.ACCESS_READ) as donnees:
        en_tete = donnees.readline().split()
        if len(en_tete) != 2 or not all(champ.isdigit() for champ in en_tete):
            raise ValueError("En-tête Word2Vec invalide (vérifier les pointeurs Git LFS).")
        lignes, dimensions = map(int, en_tete)
        largeur = dimensions * 4
        if min(lignes, dimensions) < 1 or lignes * (largeur + 2) > len(donnees):
            raise ValueError("Dimensions invalides ou fichier Word2Vec tronqué.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as temporaire:
            dossier = Path(temporaire) / "modele"
            dossier.mkdir()
            mots: set[str] = set()
            signatures: set[bytes] = set()
            bilan: Counter[str] = Counter()
            position = donnees.tell()
            with (dossier / "vecteurs.f32").open("wb") as sortie, (
                dossier / "mots.txt"
            ).open("w", encoding="utf-8", newline="\n") as lexique:
                for ligne in range(lignes):
                    while donnees[position:position + 1] in (b"\n", b"\r"):
                        position += 1
                    espace = donnees.find(b" ", position, position + 65536)
                    fin = espace + 1 + largeur
                    if espace <= position or fin > len(donnees):
                        raise ValueError(f"Entrée Word2Vec tronquée à la ligne {ligne + 1}.")
                    brut = donnees[position:espace]
                    vecteur = np.frombuffer(donnees[espace + 1:fin], dtype="<f4")
                    position = fin
                    try:
                        mot = brut.decode("utf-8")
                    except UnicodeDecodeError:
                        bilan["utf8_invalide"] += 1
                        continue
                    if not mot.isprintable() or any(c.isspace() for c in mot):
                        bilan["mot_invalide"] += 1
                        continue
                    if mot in mots:
                        bilan["mot_duplique"] += 1
                        continue
                    norme = np.linalg.norm(vecteur.astype(np.float64))
                    if not np.isfinite(norme) or norme == 0:
                        bilan["vecteur_invalide"] += 1
                        continue
                    unitaire = (vecteur / norme).astype("<f4").tobytes()
                    signature = hashlib.blake2b(unitaire, digest_size=16).digest()
                    if signature in signatures:
                        bilan["vecteur_identique_conserve"] += 1
                    signatures.add(signature)
                    mots.add(mot)
                    sortie.write(unitaire)
                    lexique.write(mot + "\n")
            if donnees[position:].strip(b"\r\n") or not mots:
                raise ValueError("Fin de modèle incohérente ou aucun vecteur valide.")
            rapport = {
                "format": 1, "source": source.url, "attribution": source.attribution,
                "source_sha256": empreinte(fichier), "dimensions": dimensions,
                "entrees": lignes, "mots": len(mots), "precision": "<f4",
                "anomalies": dict(bilan), "calibration": "non mesurée",
                "vecteurs_sha256": empreinte(dossier / "vecteurs.f32"),
                "mots_sha256": empreinte(dossier / "mots.txt"),
            }
            (dossier / "rapport.json").write_text(
                json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            dossier.rename(destination)

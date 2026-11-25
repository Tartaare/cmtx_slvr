"""Sources des vecteurs. Les originaux restent séparés du cache normalisé."""

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen


@dataclass(frozen=True)
class Source:
    url: str
    algorithme: str
    empreinte: str
    attribution: str


SOURCES = {
    "reduit": Source(
        "https://media.githubusercontent.com/media/Amodio/cemantbot/refs/heads/main/"
        "models/frWac_no_postag_phrase_500_cbow_cut10_stripped.bin",
        "sha256", "a6c1be2d04c7072bfbf9b053b937648f95fc57a2a85183a6364a7f6f3ee92587",
        "Jean-Philippe Fauconnier, French Word Embeddings (CC BY 3.0), sélection Amodio/Cemantbot",
    ),
    "original": Source(
        "https://embeddings.net/embeddings/frWac_no_postag_phrase_500_cbow_cut10.bin",
        "md5", "14da334ef867fec69a086cd6b4805609",
        "Jean-Philippe Fauconnier, French Word Embeddings (CC BY 3.0)",
    ),
}


def empreinte(fichier: Path, algorithme: str = "sha256") -> str:
    with fichier.open("rb") as flux:
        return hashlib.file_digest(flux, algorithme).hexdigest()


def verifier(fichier: Path, source: Source) -> None:
    if empreinte(fichier, source.algorithme) != source.empreinte:
        raise ValueError(f"Empreinte {source.algorithme} incorrecte pour {fichier}.")


def acquerir(nom: str, cache: Path) -> Path:
    source = SOURCES[nom]
    cache.mkdir(parents=True, exist_ok=True)
    cible = cache / f"{nom}.bin"
    if cible.exists():
        verifier(cible, source)
        return cible
    with tempfile.TemporaryDirectory(dir=cache) as dossier:
        copie = Path(dossier) / "source.bin"
        with urlopen(source.url, timeout=120) as entree, copie.open("wb") as sortie:
            shutil.copyfileobj(entree, sortie, length=1024 * 1024)
        verifier(copie, source)
        os.replace(copie, cible)
    return cible

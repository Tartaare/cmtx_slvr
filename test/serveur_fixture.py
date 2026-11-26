"""Petit lexique déterministe utilisé par le test navigateur, y compris après redémarrage."""
import sys
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

from solveur.modele import Modele
from solveur.serveur import servir
from test.test_secours import preparer_modele


def lancer(base: Path) -> None:
    cache = base.parent
    mots = ["hirsute", "mer", "balane"]
    vecteurs = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    if not base.exists():
        preparer_modele(cache, "reduit", mots, vecteurs)
        preparer_modele(cache, "original", mots + ["chignin-bergeron"], vecteurs + [[1, 1, 0]])

    @lru_cache(maxsize=2)
    def charger(dossier: Path, nom: str) -> Modele:
        return Modele(dossier / nom, verifier=True)

    def consulter(*arguments: str) -> str | dict:
        if arguments == ("--grille",):
            return "1234"
        assert arguments == ("--observation", "1234", "hirsute")
        return {"mot": "hirsute", "statut": "victoire", "temperature": 100}

    with patch("solveur.atelier.charger", charger), patch("solveur.serveur.consulter_jeu", consulter):
        servir(cache, base, 0)


if __name__ == "__main__":
    lancer(Path(sys.argv[1]))

import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from solveur.modele import Modele
from solveur.preparation import preparer
from solveur.simulation import nouvelle_grille
from solveur.sources import Source, empreinte, verifier


class FondationsTest(unittest.TestCase):
    def setUp(self) -> None:
        temporaire = tempfile.TemporaryDirectory()
        self.addCleanup(temporaire.cleanup)
        racine = Path(temporaire.name)
        self.fichier = racine / "controle.bin"
        self.cache = racine / "prepare"
        self.references = {"été": (3, 4), "gel": (-4, -3), "alias": (3, 4), "l'or": (4, -3)}
        entrees = [(m.encode(), v) for m, v in self.references.items()]
        entrees += [(b"nul", (0, 0)), (b"inf", (math.inf, 0)), (b"gel", (1, 0)), (b"\xff", (1, 2))]
        with self.fichier.open("wb") as flux:
            flux.write(f"{len(entrees)} 2\n".encode())
            for mot, valeurs in entrees:
                flux.write(mot + b" " + struct.pack("<ff", *valeurs) + b"\n")
        self.source = Source("local", empreinte(self.fichier), "Vecteurs de contrôle")
        preparer(self.fichier, self.cache, self.source)

    def test_cosinus_et_integrite(self) -> None:
        modele = Modele(self.cache, verifier=True)
        np.testing.assert_allclose(np.linalg.norm(modele.vecteurs, axis=1), 1.0)
        for mot, u in self.references.items():
            attendus = [sum(a*b for a, b in zip(u, v)) / (math.hypot(*u) * math.hypot(*v))
                        for v in self.references.values()]
            np.testing.assert_allclose(modele.similarites(mot), attendus, atol=1e-7)
            np.testing.assert_allclose(modele.similarites(mot, [2, 0]), [attendus[2], attendus[0]], atol=1e-7)
            for autre, attendu in zip(modele.mots, attendus, strict=True):
                self.assertAlmostEqual(modele.cosinus(mot, autre), attendu, places=6)
                self.assertEqual(modele.cosinus(mot, autre), modele.cosinus(autre, mot))
        bilan = json.loads((self.cache / "rapport.json").read_text(encoding="utf-8"))
        self.assertEqual(bilan["anomalies"], {
            "vecteur_invalide": 2, "utf8_invalide": 1, "mot_duplique": 1,
            "vecteur_identique_conserve": 1,
        })
        self.assertEqual(modele.indice(" L’OR "), 3)
        with self.assertRaisesRegex(ValueError, "absent"):
            modele.indice("ete")

    def test_grille_et_confirmation(self) -> None:
        modele = Modele(self.cache)
        proposer = nouvelle_grille(modele, 17, ["été"])
        self.assertEqual(proposer("gel").temperature, -96.0)
        self.assertEqual(proposer("alias").temperature, 100.0)
        self.assertEqual(proposer("alias").statut, "score")
        self.assertEqual(proposer("introuvable").statut, "refus")
        self.assertEqual(proposer("E\u0301TÉ").statut, "victoire")
        grille_a, grille_b = nouvelle_grille(modele, 35), nouvelle_grille(modele, 35)
        self.assertEqual([grille_a(m) for m in modele.mots], [grille_b(m) for m in modele.mots])
        with self.assertRaisesRegex(ValueError, "vide"):
            nouvelle_grille(modele, 1, [])

    def test_corruption_et_publication_atomique(self) -> None:
        tronque = self.cache.parent / "tronque"
        self.fichier.write_bytes(self.fichier.read_bytes()[:-6])
        with self.assertRaisesRegex(ValueError, "Empreinte"):
            verifier(self.fichier, self.source)
        with self.assertRaises(ValueError):
            preparer(self.fichier, tronque, self.source)
        self.assertFalse(tronque.exists())
        (self.cache / "mots.txt").write_text("invalide\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Empreinte"):
            Modele(self.cache, verifier=True)

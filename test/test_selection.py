import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from solveur.modele import Modele
from solveur.preparation import preparer
from solveur.resolution import Strategie, resoudre
from solveur.selection import classes_scores, discriminant, evaluer, fin_de_partie, ouverture_optimisee
from solveur.simulation import nouvelle_grille
from solveur.sources import Source, empreinte


class SelectionTest(unittest.TestCase):
    def setUp(self) -> None:
        temporaire = tempfile.TemporaryDirectory()
        self.addCleanup(temporaire.cleanup)
        self.racine = Path(temporaire.name)
        self.mots = ["azur", "beige", "cyan", "doré"]
        vocabulaire = [*self.mots, "neutre", "sonde", "double"]
        vecteurs = [*np.eye(5), (1, 2, 3, 4, 0), (1, 0, 0, 0, 0)]
        fichier = self.racine / "source.bin"
        with fichier.open("wb") as flux:
            flux.write(b"7 5\n")
            for mot, vecteur in zip(vocabulaire, vecteurs, strict=True):
                flux.write(mot.encode() + b" " + struct.pack("<5f", *vecteur) + b"\n")
        preparer(fichier, self.racine / "modele", Source("local", empreinte(fichier), "test"))
        self.modele = Modele(self.racine / "modele")
        self.addCleanup(delattr, self, "modele")
        self.candidats = self.modele.indices_solutions(self.mots)
        self.sonde = self.modele.indice("sonde")

    def test_partitions_quantification_et_victoire(self) -> None:
        candidat, sonde = evaluer(self.modele, self.candidats, [0, self.sonde], 2)
        self.assertAlmostEqual(candidat.entropie_bits, 2 - 0.75 * math.log2(3))
        self.assertEqual(candidat.collision, 10 / 16)
        self.assertEqual((sonde.groupes, sonde.entropie_bits, sonde.collision), (4, 2.0, 0.25))
        doublons = self.modele.indices_solutions(["azur", "double"])
        self.assertEqual(next(iter(evaluer(self.modele, doublons, [0], 2))).groupes, 2)
        for d in (0, 2, 6):
            q = self.modele.vecteurs[self.sonde]
            codes = classes_scores(np.vecdot(self.modele.vecteurs, q), d).tolist()
            attendus = [round(round(100 * self.modele.cosinus("sonde", m), d) * 10**d) for m in self.modele.mots]
            self.assertEqual(codes, attendus)

    def test_sonde_exterieure_budget_et_confirmation(self) -> None:
        for strategie in (Strategie.ENTROPIE, Strategie.COLLISIONS, Strategie.PLAN):
            for secret in self.mots:
                source = nouvelle_grille(self.modele, 0, [secret])
                historique = [source("neutre")]
                r = resoudre(self.modele, source, self.candidats, strategie, 3, 2, 0, historique)
                self.assertEqual([e.observation.mot for e in r.essais], ["neutre", "sonde", secret])
                self.assertEqual(r.statut, "resolu")
                dernier = resoudre(self.modele, source, self.candidats, strategie, 2, 2, 0, historique)
                self.assertIn(dernier.essais[-1].observation.mot, self.mots)
        self.assertNotEqual(discriminant(self.modele, self.candidats, [self.sonde], 2, "entropie"), self.sonde)
        self.assertNotEqual(fin_de_partie(self.modele, self.candidats, 2, 2, [self.sonde]), self.sonde)

    def test_cache_depend_du_vocabulaire_et_de_la_precision(self) -> None:
        cache = self.racine / "ouvertures"
        for critere in ("entropie", "collisions"):
            i = ouverture_optimisee(self.modele, self.candidats, 2, critere, cache)
            self.assertEqual(i, self.sonde)
        fichier, = cache.glob("*.json")
        self.assertEqual(json.loads(fichier.read_text(encoding="utf-8"))["entropie"][0]["mot"], "sonde")
        fichier.write_text("{", encoding="utf-8")
        self.assertEqual(ouverture_optimisee(self.modele, self.candidats, 2, "entropie", cache), self.sonde)
        ouverture_optimisee(self.modele, self.candidats[::-1], 2, "entropie", cache)
        ouverture_optimisee(self.modele, self.candidats[:2], 2, "entropie", cache)
        ouverture_optimisee(self.modele, self.candidats, 0, "entropie", cache)
        self.assertEqual(len(list(cache.glob("*.json"))), 3)

import csv
import random
import tempfile
import unittest
from pathlib import Path

import numpy as np

from solveur.benchmark import exporter, mesurer, resumer
from solveur.modele import Modele
from solveur.preparation import preparer
from solveur.resolution import REFERENCES, Recherche, Strategie, resoudre
from solveur.simulation import Observation, nouvelle_grille
from solveur.sources import Source, empreinte


class ResolutionTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.racine = Path(temp.name)
        binaire = self.racine / "source.bin"
        vecteurs = np.random.default_rng(541).normal(size=(320, 32)).astype("<f4")
        vecteurs[1] = vecteurs[0]
        vecteurs[2] = -vecteurs[0]
        with binaire.open("wb") as flux:
            flux.write(b"320 32\n")
            for i, vecteur in enumerate(vecteurs):
                mot = chr(97 + i // 26) + chr(97 + i % 26)
                flux.write(mot.encode() + b" " + vecteur.tobytes() + b"\n")
        dossier = self.racine / "modele"
        preparer(binaire, dossier, Source("local", empreinte(binaire), "test"))
        self.modele = Modele(dossier)
        self.addCleanup(delattr, self, "modele")
        self.indices = np.arange(len(vecteurs), dtype=np.intp)

    def test_inversion_equivaut_aux_intervalles_du_simulateur(self) -> None:
        for decimales in (0, 2, 6):
            for secret in ("aa", "fx", "mh"):
                source = nouvelle_grille(self.modele, 12, [secret], decimales)
                recherche = Recherche(self.modele, self.indices, Strategie.EXACTE, decimales, random.Random(8))
                attendus = set(self.modele.jouables)
                for mot in ("ac", "ca", "bd"):
                    observation = source(mot)
                    recherche.observer(self.modele.indice(mot), observation)
                    attendus = {c for c in attendus if c != mot and
                                round(100 * self.modele.cosinus(mot, c), decimales) == observation.temperature}
                    obtenus = {self.modele.mots[i] for i in np.flatnonzero(recherche.disponibles)}
                    self.assertEqual(obtenus, attendus)
                    self.assertIn(secret, obtenus)

    def test_confirmation_budget_historique_et_absence_de_candidats(self) -> None:
        source = nouvelle_grille(self.modele, 1, ["aa"])
        historique = [source("inconnu"), source("ac"), source("ab")]
        self.assertEqual([o.temperature for o in historique], [None, -100.0, 100.0])
        resultat = resoudre(self.modele, source, self.indices, Strategie.EXACTE, 3, 2, 7, historique)
        self.assertEqual(resultat.statut, "budget_epuise")
        self.assertEqual(resultat.essais[-1].candidats_exacts, 1)
        resultat = resoudre(self.modele, source, self.indices, Strategie.EXACTE, 4, 2, 7, historique)
        self.assertEqual(resultat.essais[-1].observation, Observation("aa", "victoire", 100.0))
        self.assertEqual(resultat.statut, "resolu")
        impossible = resoudre(self.modele, source, np.array([0]), Strategie.EXACTE, 4, 2, 7,
                              [Observation("ac", "score", 25.0)])
        self.assertEqual(impossible.statut, "aucun_candidat")
        with self.assertRaisesRegex(ValueError, "répétée"):
            resoudre(self.modele, source, self.indices, Strategie.EXACTE, 4, 2, 7, historique[:1] * 2)
        with self.assertRaisesRegex(ValueError, "réponse"):
            resoudre(self.modele, lambda _: source("inconnu"), self.indices, Strategie.EXACTE, 3, 2, 7)

    def test_comparaison_appariee_et_export(self) -> None:
        mesures = mesurer(self.modele, None, 8, 4, 0, 23, 2)
        copie = mesurer(self.modele, None, 8, 4, 0, 23, 2)
        self.assertEqual([(m.ouverture, m.essais, m.statut) for m in mesures],
                         [(m.ouverture, m.essais, m.statut) for m in copie])
        for graine in range(8):
            groupe = [m for m in mesures if m.grille == graine]
            self.assertEqual({m.strategie for m in groupe}, set(REFERENCES))
            self.assertEqual(len({m.ouverture for m in groupe}), 1)
            for m in groupe:
                self.assertLessEqual(m.essais, 4)
        bilan = resumer(mesures)
        self.assertEqual(bilan["exacte"]["resolues"], 8)
        self.assertEqual(bilan["hasard"]["parties"], 8)
        self.assertGreater(bilan["hasard"]["echecs"], 0)
        fichier = self.racine / "resultats.csv"
        exporter(mesures, fichier)
        with fichier.open(encoding="utf-8", newline="") as flux:
            self.assertEqual(len(list(csv.DictReader(flux))), 40)

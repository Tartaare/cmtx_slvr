import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from solveur.benchmark import mesurer, resumer
from solveur.evaluation_inference import evaluer_historiques, evaluer_simulations
from solveur.inference import Inference, Methode, PERTES, log_masse
from solveur.modele import Modele
from solveur.preparation import preparer
from solveur.resolution import Strategie, resoudre
from solveur.simulation import Observation, Scenario, nouvelle_grille
from solveur.sources import Source, empreinte


class InferenceTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dossier = Path(temp.name)
        fichier = self.dossier / "m.bin"
        vecteurs = {"secret": (1, 0), "leurre": (0, 1), "nord": (0, 1), "est": (1, 0),
                    "diagonal": (3, 4), "inverse": (-1, 0)}
        with fichier.open("wb") as f:
            f.write(b"6 2\n")
            for mot, v in vecteurs.items():
                f.write(mot.encode() + b" " + struct.pack("<ff", *v) + b"\n")
        preparer(fichier, self.dossier / "m", Source("test", empreinte(fichier), "contrôle"))
        self.modele = Modele(self.dossier / "m")
        self.addCleanup(delattr, self, "modele")
        self.indices = self.modele.indices_solutions(["secret", "leurre"])

    def test_masses_arrondies_avec_queues_ecretees(self) -> None:
        for methode in set(Methode) - PERTES:
            for moyenne in (-100.0, 0.0, 99.75):
                delta = np.arange(-100, 101) - moyenne
                logs = log_masse(methode, delta, 0.5, 0.7, False)
                logs[[0, -1]] = log_masse(methode, delta[[0, -1]], 0.5, 0.7, True)
                self.assertAlmostEqual(float(np.exp(logs).sum()), 1.0, places=11)
            extremes = log_masse(methode, np.array([0., 99., -199.]), 0.0000005, 0.0047, False)
            self.assertTrue(np.isfinite(extremes).all())
        p = log_masse(Methode.GAUSSE, np.array([0., 1.]), .5, 1., False)
        self.assertAlmostEqual(math.exp(p[0]), math.erf(.5 / math.sqrt(2)))
        self.assertAlmostEqual(math.exp(p[1]), (math.erf(1.5/math.sqrt(2)) - math.erf(.5/math.sqrt(2))) / 2)

    def test_bascule_reintegre_le_secret_et_rejoue_chaque_score(self) -> None:
        source = nouvelle_grille(self.modele, 1, ["secret"])
        historique = [Observation("nord", "score", 100.0), Observation("est", "score", 99.0),
                      source("diagonal"), source("inverse")]
        exact = resoudre(self.modele, source, self.indices, Strategie.EXACTE, 5, 2, 9, historique)
        self.assertEqual(exact.statut, "aucun_candidat")
        robuste = resoudre(self.modele, source, self.indices, Strategie.ROBUSTE, 5, 2, 9, historique)
        self.assertEqual(robuste.essais[0].candidats_exacts, 1)
        self.assertEqual(robuste.essais[1].motif_bascule, "aucun_candidat_exact")
        self.assertIsNotNone(robuste.essais[1].estimation)
        dernier = robuste.essais[3].estimation
        self.assertEqual((dernier.mot, dernier.observation_plus_ecartee), ("secret", "nord"))
        self.assertEqual(robuste.statut, "resolu")
        direct = resoudre(self.modele, source, self.indices, Strategie.MELANGE, 4, 2, 9, historique)
        self.assertEqual(direct.statut, "budget_epuise")
        self.assertEqual(direct.essais[-1].estimation, dernier)
        self.assertGreater(dernier.probabilite_estimee, .5)

    def test_refus_scenarios_et_pertes(self) -> None:
        for scenario in Scenario:
            grille = nouvelle_grille(self.modele, 15, ["secret"], 2, scenario)
            initial = grille("est")
            self.assertEqual(grille("absent").statut, "refus")
            self.assertEqual(grille("secret").statut, "victoire")
            self.assertEqual(grille("EST"), initial)
        masque = np.ones(len(self.modele.mots), dtype=bool)
        for methode in Methode:
            moteur = Inference(self.modele, self.indices, methode, 2)
            for mot, temp in [("est", 99.99), ("inverse", -99.0), ("diagonal", 60.0)]:
                moteur.ajouter(mot, temp)
            estimation = moteur.estimation(masque)
            self.assertEqual(estimation.mot, "secret")
            self.assertEqual(estimation.probabilite_estimee is None, methode in PERTES)

    def test_evaluation_du_test_seul_et_mot_absent(self) -> None:
        corpus = self.dossier / "parties.json"
        corpus.write_text(json.dumps([{"grille": str(i), "secret": s, "lot": lot, "source": "test",
                                       "observations": [["est", 100], ["absent", 0]]}
                                      for i, (lot, s) in enumerate([("calibration", "inverse"),
                                                                    ("validation", "leurre"), ("test", "secret")])]),
                          encoding="utf-8")
        lignes = evaluer_historiques(self.modele, corpus)["resultats"]
        self.assertTrue(all(l["grille"] == "2" for l in lignes))
        self.assertEqual(len(lignes), 2 * len(Methode))
        self.assertTrue(all(l["rang_secret"] == 1 for l in lignes if l["statut"] == "evalue"))
        self.assertTrue(all("rang_secret" not in l for l in lignes if l["mot"] == "absent"))

    def test_comparaison_appariee_et_previsions_hors_budget(self) -> None:
        strategies = (Strategie.EXACTE, Strategie.MELANGE, Strategie.ROBUSTE)
        mesures = mesurer(self.modele, None, 4, 1, 15, 17, 2, strategies=strategies, scenario=Scenario.BRUIT)
        for graine in range(15, 19):
            self.assertEqual(len({m.ouverture for m in mesures if m.grille == graine}), 1)
        self.assertIsNone(resumer(mesures)["melange"]["brier_top1"])
        rapport = evaluer_simulations(self.modele, 4, 15, Scenario.ABERRANT)
        self.assertEqual(rapport, evaluer_simulations(self.modele, 4, 15, Scenario.ABERRANT))
        for ligne in rapport["resultats"]:
            self.assertGreaterEqual(ligne["rang_secret"], 1)
            if "probabilite_estimee_secret" in ligne:
                self.assertLessEqual(ligne["probabilite_estimee_secret"], ligne["probabilite_estimee_premier"])

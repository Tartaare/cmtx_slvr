import json
import struct
import tempfile
import unittest
from pathlib import Path

from solveur.calibration import Prediction, Releve, calibrer, centiemes, lire_corpus, synthese
from solveur.modele import Modele
from solveur.preparation import preparer
from solveur.sources import Source, empreinte


class CalibrationTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.racine = Path(temp.name)
        self.corpus = self.racine / "parties.json"
        self.parties = [
            {"grille": "1", "secret": "hiver", "lot": "calibration", "source": "contrôle",
             "observations": [["froid", -60.0]]},
            {"grille": "2", "secret": "fruit", "lot": "validation", "source": "contrôle",
             "observations": [["poire", 60.0]]},
            {"grille": "3", "secret": "mer", "lot": "test", "source": "contrôle",
             "observations": [["poire", 80.0], ["inconnu", 13.0]]},
        ]
        self.corpus.write_text(json.dumps(self.parties), encoding="utf-8")

    def modele(self, nom: str, signe: int) -> Modele:
        vecteurs = {"hiver": (1, 0), "froid": (-3, 4), "fruit": (1, 0),
                    "poire": (3 * signe, 4), "mer": (0, 1)}
        fichier = self.racine / f"{nom}.bin"
        with fichier.open("wb") as flux:
            flux.write(b"5 2\n")
            for mot, valeurs in vecteurs.items():
                flux.write(mot.encode() + b" " + struct.pack("<ff", *valeurs) + b"\n")
        preparer(fichier, self.racine / nom, Source("test", empreinte(fichier), "contrôle"))
        return Modele(self.racine / nom)

    def test_choix_independant_du_test_et_couverture(self) -> None:
        modeles = {"alterne": self.modele("alterne", -1), "principal": self.modele("principal", 1)}
        rapport = calibrer(self.corpus, modeles)
        self.assertEqual(rapport["modele_selectionne_sur_validation"], "principal")
        principal = rapport["modeles"]["principal"]
        test = principal["lots"]["test"]
        self.assertEqual((test["observations"], test["comparables"], test["arrondis_exacts"]), (2, 1, 1))
        self.assertEqual(test["fraction_exacte_toutes_observations"], 0.5)
        self.assertEqual(test["mots_absents"], ["inconnu"])
        self.parties[2]["observations"] = [["inconnu", 40.0]]
        self.corpus.write_text(json.dumps(self.parties), encoding="utf-8")
        suite = calibrer(self.corpus, modeles)
        self.assertEqual(suite["modele_selectionne_sur_validation"], "principal")
        self.assertEqual(suite["modeles"]["principal"]["marge_p95_calibration_c"],
                         principal["marge_p95_calibration_c"])
        self.assertEqual(suite["modeles"]["principal"]["lots"]["test"]["comparables"], 0)

    def test_separation_et_validation_des_mesures(self) -> None:
        for changement in ({"secret": " HIVER "}, {"grille": "1"}, {"lot": "calibration"},
                           {"observations": [["mer", 100]]}, {"observations": [["été", 5], ["ÉTÉ", 5]]},
                           {"observations": [["mot", float("nan")]]}, {"observations": [["mot", 9.001]]}):
            with self.subTest(changement=changement):
                parties = [*self.parties[:2], self.parties[2] | changement]
                self.corpus.write_text(json.dumps(parties), encoding="utf-8")
                with self.assertRaises(ValueError):
                    lire_corpus(self.corpus)

    def test_erreurs_en_degres_et_tolerances_en_centiemes(self) -> None:
        def prediction(mot: str, prediction: float, observation: float) -> Prediction:
            r = Releve("1", "secret", "test", "contrôle", mot, observation)
            return Prediction(r, prediction, prediction)

        valeurs = [prediction("froid", -12.3451, -12.35), prediction("chaud", 20.0, 21.0)]
        bilan = synthese(valeurs, 0.005)
        self.assertEqual(centiemes(-12.3451), -1235)
        self.assertAlmostEqual(bilan["mae_c"], (0.0049 + 1) / 2)
        self.assertAlmostEqual(bilan["mse_c2"], (0.0049**2 + 1) / 2)
        self.assertEqual(bilan["fraction_dans_marge_calibration"], 0.5)
        self.assertEqual(bilan["fractions_compatibles_affichees"]["1.0"], 1)
        self.assertEqual(bilan["troncatures_exactes"], 0)
        self.assertAlmostEqual(bilan["spearman"], 1)

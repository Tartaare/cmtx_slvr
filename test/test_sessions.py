import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solveur.atelier import Atelier
from solveur.sessions import Conflit, Sessions
from test.test_secours import preparer_modele


class SessionsTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.racine = Path(temp.name)
        petit = preparer_modele(self.racine, "reduit", ["hirsute", "mer"], [[1, 0], [0, 1]])
        grand = preparer_modele(self.racine, "original", ["île", "hirsute", "mer"],
                                [[1, 1], [1, 0], [0, 1]])
        self.addCleanup(delattr, petit, "vecteurs")
        self.addCleanup(delattr, grand, "vecteurs")
        chargeur = patch("solveur.atelier.charger", side_effect=lambda _, nom: {"reduit": petit, "original": grand}[nom])
        self.addCleanup(chargeur.stop)
        chargeur.start()
        self.fichier = self.racine / "parties.sqlite"
        self.sessions = Sessions(self.fichier, Atelier(self.racine))

    def test_redemarrage_bascule_et_confirmation(self) -> None:
        s = self.sessions.creer({"source": "assiste", "grille": "234", "budget": 2})
        self.assertEqual(s["prochain"], "hirsute")
        i = s["id"]
        obs = [{"mot": "hirsute", "statut": "score", "temperature": 70.71}]
        s = self.sessions.modifier(i, 0, "essai", obs)
        self.assertEqual(s["vue"]["phase"], "exact_alternatif")
        self.assertEqual(s["prochain"], "île")
        self.sessions.modifier(i, 1, "pause", None)
        reprise = Sessions(self.fichier, Atelier(self.racine))
        s = reprise.modifier(i, 2, "reprendre", None)
        self.assertEqual((s["prochain"], len(s["essais"])), ("île", 1))
        with self.assertRaises(Conflit):
            reprise.modifier(i, 1, "essai", obs)
        s = reprise.modifier(i, 3, "essai", [{"mot": "île", "statut": "victoire", "temperature": 100}])
        self.assertEqual((s["statut"], s["prochain"]), ("resolu", None))
        self.assertEqual(len(reprise.liste()), 1)

    def test_import_atomique_et_budget(self) -> None:
        config = {"source": "assiste", "grille": "60", "budget": 2}
        o = {"mot": "hirsute", "statut": "score", "temperature": 17.12}
        with self.assertRaisesRegex(ValueError, "répétée"):
            self.sessions.creer(config, [o, o])
        self.assertFalse(self.sessions.liste())
        s = self.sessions.creer(config, [o])
        self.assertEqual(s["vue"]["phase"], "melange")
        with self.assertRaises(ValueError):
            self.sessions.modifier(s["id"], 0, "essai", [dict(o, mot="mer", temperature=120)])
        self.assertEqual(self.sessions.lire(s["id"]), s)
        s = self.sessions.modifier(s["id"], 0, "essai", [dict(o, mot="mer")])
        self.assertEqual(s["statut"], "budget_epuise")
        self.assertIsNone(s["prochain"])

    def test_simulation_interruption_et_nouvelle_partie(self) -> None:
        s = self.sessions.creer({"modele_source": "original", "graine": 1})
        while s["statut"] == "active":
            s = self.sessions.modifier(s["id"], s["revision"], "essai", None)
        self.assertEqual(s["statut"], "resolu")
        autre = self.sessions.creer({})
        self.sessions.modifier(autre["id"], 0, "interrompre", None)
        self.assertEqual(len(self.sessions.liste()), 2)
        self.assertEqual(self.sessions.lire(s["id"]), s)

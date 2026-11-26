import tempfile
import unittest
from pathlib import Path

import numpy as np

from solveur.modele import Modele
from solveur.preparation import preparer
from solveur.reconstruction import reconstruire
from solveur.resolution import jouer
from solveur.secours import Repli, Secours
from solveur.simulation import Observation, nouvelle_grille
from solveur.sources import Source, empreinte


def preparer_modele(dossier: Path, nom: str, mots: list[str], lignes: list[list[int]]) -> Modele:
    binaire = dossier / (nom + ".bin")
    with binaire.open("wb") as flux:
        flux.write(f"{len(mots)} {len(lignes[0])}\n".encode())
        for mot, v in zip(mots, lignes, strict=True):
            flux.write(mot.encode() + b" " + np.array(v, dtype="<f4").tobytes() + b"\n")
    preparer(binaire, dossier / nom, Source("local", empreinte(binaire), "test"))
    return Modele(dossier / nom)


class SecoursTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        racine = Path(temp.name)
        self.p = preparer_modele(racine, "petit", ["a", "b"], [[1, 0], [0, 1]])
        self.a = preparer_modele(racine, "autre", ["c", "b", "double", "a"],
                                 [[1, 1, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]])
        self.addCleanup(delattr, self, "p")
        self.addCleanup(delattr, self, "a")

    def politique(self, repli: Repli = Repli.MELANGE) -> Secours:
        return Secours(self.p, self.p.lignes_jouables, self.a, self.a.lignes_jouables, 2, 7, repli)

    def test_rejeu_lexical_et_confirmation(self) -> None:
        source = nouvelle_grille(self.a, 1, ["double"])
        historique = [source("inconnu"), source("b"), source("c")]
        resultat = jouer(self.politique(), source, 4, 2, historique)
        self.assertEqual(resultat.essais[1].motif_bascule, "principal_sans_candidat")
        self.assertEqual(resultat.essais[2].observation, Observation("c", "score", 100.0))
        self.assertEqual(resultat.essais[2].candidats_exacts, 1)
        self.assertEqual(resultat.essais[-1].observation, source("double"))
        self.assertEqual(resultat.statut, "resolu")
        self.assertEqual(jouer(self.politique(), source, 3, 2, historique).statut, "budget_epuise")
        with self.assertRaisesRegex(ValueError, "répétée"):
            jouer(self.politique(), source, 4, 2, [source("c"), source("C")])

    def test_scores_absents_et_modeles_incompatibles(self) -> None:
        source = nouvelle_grille(self.a, 0, ["a"])
        trace = jouer(self.politique(), source, 2, 2, [Observation("tiers", "score", 12), source("c")])
        self.assertEqual(trace.essais[0].scores_inexploitables, 1)
        self.assertEqual(trace.essais[1].motif_bascule, "sonde_absente_du_principal")
        self.assertEqual(trace.essais[1].scores_inexploitables, 1)
        for repli in Repli:
            def incompatible(mot: str) -> Observation:
                return Observation(mot, "score", 17.0)

            resultat = jouer(self.politique(repli), incompatible, 3, 2)
            self.assertEqual(resultat.statut, "budget_epuise")
            premier = resultat.essais[0]
            self.assertEqual(premier.phase, repli)
            self.assertEqual(premier.motif_bascule, "principal_sans_candidat+alternatif_sans_candidat")
            self.assertEqual(len({e.observation.mot for e in resultat.essais}), 3)
            dernier = resultat.essais[-1]
            if repli == Repli.RECONSTRUCTION:
                self.assertEqual(dernier.reconstruction.observations, 3)
            else:
                self.assertIsNotNone(dernier.estimation)

    def test_svd_rang_deficient_et_direction(self) -> None:
        source = nouvelle_grille(self.a, 1, ["c"], 6)
        scores = [(mot, source(mot).temperature) for mot in ("a", "b", "double")]
        vecteur, diagnostic = reconstruire(self.a, scores, 0)
        self.assertEqual((diagnostic.rang, diagnostic.dimensions), (2, 3))
        self.assertLess(diagnostic.residu_rms_c, 0.00001)
        np.testing.assert_allclose(vecteur, self.a.vecteurs[self.a.indice("c")], atol=1e-6)
        v, d = reconstruire(self.a, [("c", 50), ("double", 40)], 0.01)
        self.assertEqual(d.rang, 1)
        self.assertLess(np.linalg.norm(v), 0.45)

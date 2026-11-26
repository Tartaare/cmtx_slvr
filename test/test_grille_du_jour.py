from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from typing import Iterator
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from solveur.serveur import creer_serveur


@contextmanager
def atelier(base: Path) -> Iterator[str]:
    with creer_serveur(base.parent, base, 0) as serveur:
        service = Thread(target=serveur.serve_forever)
        service.start()
        try:
            yield f"http://127.0.0.1:{serveur.server_port}"
        finally:
            serveur.shutdown()
            service.join()


def lire(url: str) -> str:
    with urlopen(url, timeout=5) as reponse:
        return reponse.read().decode()


class GrilleDuJourTest(TestCase):
    def test_cache_partage_persistant_et_expiration(self) -> None:
        endpoint = "/api/grille-du-jour"
        premier = {"grille": "1730", "expiration": 200}
        suivant = {"grille": "1731", "expiration": 90_200}
        with TemporaryDirectory() as dossier, patch("solveur.serveur.time", return_value=100) as horloge, patch(
            "solveur.serveur.consulter_jeu", side_effect=[ValueError("Site indisponible"), premier, suivant]
        ) as consulter:
            base = Path(dossier) / "parties.sqlite3"
            with atelier(base) as url:
                self.assertIn('data-grille="" data-expiration=""', lire(url + "/"))
                for chemin in ("/jour", "/atelier"):
                    with urlopen(url + chemin, timeout=5) as ancienne_adresse:
                        self.assertEqual(ancienne_adresse.geturl(), url + "/")
                with self.assertRaises(HTTPError) as erreur:
                    lire(url + endpoint)
                erreur.exception.close()
                with ThreadPoolExecutor(max_workers=2) as demandes:
                    lectures = list(demandes.map(lire, [url + endpoint] * 2))
                self.assertEqual([json.loads(reponse) for reponse in lectures], [premier, premier])
                self.assertEqual(consulter.call_count, 2)
            with atelier(base) as url:
                self.assertIn('data-grille="1730" data-expiration="200"', lire(url + "/"))
                self.assertEqual(json.loads(lire(url + endpoint)), premier)
                self.assertEqual(consulter.call_count, 2)
                horloge.return_value = 200
                self.assertIn('data-grille="" data-expiration=""', lire(url + "/"))
                self.assertEqual(json.loads(lire(url + endpoint)), suivant)
                self.assertIn('data-grille="1731"', lire(url + "/"))
                self.assertEqual(consulter.call_count, 3)

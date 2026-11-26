"""Serveur HTTP de l'atelier sur l'interface de boucle locale."""
import gzip
import hashlib
import json
import re
import sqlite3
import subprocess
import traceback
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from functools import lru_cache
from pathlib import Path
from threading import Lock
from time import time
from urllib.parse import urlsplit

import numpy as np

from .atelier import Atelier, Objet
from .sessions import Conflit, Sessions

RACINE = Path(__file__).resolve().parents[1]
FICHIERS = {
    "/": (RACINE / "interface/index.html", "text/html"),
    "/style.css": (RACINE / "interface/style.css", "text/css"),
    "/logo-cemantix-transparent.png": (RACINE / "logo-cemantix-transparent.png", "image/png"),
    "/atlas.json": (RACINE / "interface/atlas.json", "application/json"),
    **{f"/{nom}.js": (RACINE / f"dist/interface/{nom}.js", "text/javascript")
       for nom in ("arcs", "galaxie", "lentille", "projection", "scene")},
    "/app.js": (RACINE / "dist/interface/app.js", "text/javascript"),
    "/rendu.js": (RACINE / "dist/interface/rendu.js", "text/javascript"),
}


@lru_cache(maxsize=2)
def lire_atlas(fichier: Path, revision: int, compresse: bool) -> tuple[bytes, str]:
    """La date de modification invalide les deux représentations du cache local."""
    contenu = fichier.read_bytes()
    if compresse:
        contenu = gzip.compress(contenu, compresslevel=5, mtime=0)
    return contenu, '"' + hashlib.sha256(contenu).hexdigest() + '"'


def consulter_jeu(*arguments: str) -> str | Objet:
    try:
        resultat = subprocess.run(["node", "--disable-warning=ExperimentalWarning", "--experimental-strip-types",
                                   "cli.ts", *arguments], cwd=RACINE, capture_output=True,
                                  encoding="utf-8", timeout=90)
    except subprocess.TimeoutExpired as erreur:
        raise ValueError("Cémantix n’a pas répondu à temps. Réessayez.") from erreur
    if resultat.returncode:
        raise ValueError(resultat.stderr.strip() or "Impossible de consulter Cémantix.")
    return json.loads(resultat.stdout)


def creer_serveur(cache: Path, base: Path, port: int) -> ThreadingHTTPServer:
    sessions = Sessions(base, Atelier(cache))
    mutations = Lock()
    consultation_grille = Lock()

    def grille_du_jour() -> tuple[str, int]:
        with consultation_grille:
            conservee = sessions.grille_du_jour(time())
            if conservee:
                return conservee
            resultat = consulter_jeu("--grille", "--expiration")
            grille = resultat.get("grille") if isinstance(resultat, dict) else None
            expiration = resultat.get("expiration") if isinstance(resultat, dict) else None
            if not isinstance(grille, str) or not re.fullmatch(r"[0-9]+", grille):
                raise ValueError("Numéro de grille illisible.")
            maintenant = time()
            if type(expiration) is not int or not maintenant < expiration <= maintenant + 25 * 3_600:
                raise ValueError("La grille a changé pendant la consultation. Réessayez.")
            sessions.conserver_grille_du_jour(grille, expiration)
            return grille, expiration

    class Requete(BaseHTTPRequestHandler):
        def repondre(self, statut: int, contenu: bytes, type_mime: str, *, etag: str = "", compresse: bool = False) -> None:
            self.send_response(statut)
            if not type_mime.startswith("image/"):
                type_mime += "; charset=utf-8"
            self.send_header("Content-Type", type_mime)
            self.send_header("Content-Length", str(len(contenu)))
            self.send_header("Cache-Control", "no-cache" if etag else "no-store")
            if etag:
                self.send_header("ETag", etag)
                self.send_header("Vary", "Accept-Encoding")
            if compresse:
                self.send_header("Content-Encoding", "gzip")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; object-src 'none'; "
                             "base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(contenu)

        def json(self, statut: int, contenu: object) -> None:
            self.repondre(statut, json.dumps(contenu, allow_nan=False).encode(), "application/json")

        def traiter(self) -> None:
            ecriture = self.command != "GET"
            port_local = self.server.server_address[1]
            host = self.headers.get("Host")
            if host not in (f"127.0.0.1:{port_local}", f"localhost:{port_local}"):
                self.json(403, {"erreur": "Adresse locale requise."})
                return
            chemin = urlsplit(self.path).path
            try:
                if not ecriture and chemin in ("/atelier", "/jour"):
                    self.send_response(308)
                    self.send_header("Location", "/")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                if not ecriture and chemin in FICHIERS:
                    fichier, mime = FICHIERS[chemin]
                    if chemin == "/atlas.json":
                        avec_gzip = "gzip" in {s.strip() for s in self.headers.get("Accept-Encoding", "").lower().split(",")}
                        contenu, etag = lire_atlas(fichier, fichier.stat().st_mtime_ns, avec_gzip)
                        if self.headers.get("If-None-Match") == etag:
                            self.send_response(304)
                            self.send_header("ETag", etag)
                            self.send_header("Vary", "Accept-Encoding")
                            self.end_headers()
                        else:
                            self.repondre(200, contenu, mime, etag=etag, compresse=avec_gzip)
                        return
                    contenu = fichier.read_bytes()
                    if chemin == "/" and (conservee := sessions.grille_du_jour(time())):
                        grille, expiration = conservee
                        attributs = f'data-grille="{escape(grille)}" data-expiration="{int(expiration)}"'
                        contenu = contenu.replace(b'data-grille="" data-expiration=""', attributs.encode(), 1)
                    self.repondre(200, contenu, mime)
                    return
                if not ecriture and chemin == "/api/grille-du-jour":
                    grille, expiration = grille_du_jour()
                    self.json(200, {"grille": grille, "expiration": expiration})
                    return
                identifiant = re.fullmatch(r"/api/parties/([a-f0-9]{32})", chemin)
                if not identifiant and (chemin != "/api/parties" or self.command == "DELETE"):
                    self.json(404, {"erreur": "Ressource inconnue."})
                    return
                if not ecriture:
                    self.json(200, sessions.lire(identifiant[1]) if identifiant else sessions.liste())
                    return
                if self.headers.get("Origin") not in (None, "http://" + host):
                    self.json(403, {"erreur": "Origine de la requête refusée."})
                    return
                if self.headers.get_content_type() != "application/json":
                    self.json(415, {"erreur": "Le corps doit être au format JSON."})
                    return
                taille = int(self.headers.get("Content-Length", "0"))
                if not 0 < taille <= 262144:
                    self.json(413, {"erreur": "Le corps doit contenir de 1 à 262144 octets."})
                    return
                donnees: Objet = json.loads(self.rfile.read(taille))
                if not isinstance(donnees, dict):
                    raise ValueError("Un objet JSON est attendu.")
                if self.command == "DELETE" and identifiant:
                    with mutations:
                        sessions.supprimer(identifiant[1], donnees.get("revision"))
                    self.json(200, {})
                    return
                with mutations:
                    if identifiant:
                        if donnees.get("action") == "essai":
                            partie = sessions.lire(identifiant[1])
                            if partie["config"]["source"] == "jour":
                                if donnees.get("revision") != partie["revision"]:
                                    raise Conflit("Cette partie a changé. Rechargez-la avant de continuer.")
                                if partie["statut"] != "active" or not partie["prochain"]:
                                    raise ValueError("La partie ne peut plus jouer cet essai.")
                                donnees["observations"] = [consulter_jeu("--observation", partie["config"]["grille"],
                                                                         partie["prochain"])]
                        resultat = sessions.modifier(identifiant[1], donnees.get("revision"), donnees.get("action"),
                                                     donnees.get("observations"))
                    elif donnees.get("initial") is True and (existantes := sessions.liste()):
                        resultat = sessions.lire(existantes[0]["id"])
                    else:
                        config = donnees.get("config", {})
                        if isinstance(config, dict) and config.get("source") == "jour":
                            config["grille"] = grille_du_jour()[0]
                            donnees.pop("observations", None)
                        resultat = sessions.creer(config, donnees.get("observations"))
                self.json(200 if identifiant else 201, resultat)
            except Conflit as erreur:
                self.json(409, {"erreur": str(erreur)})
            except KeyError:
                self.json(404, {"erreur": "Partie introuvable."})
            except (ValueError, TypeError, RecursionError) as erreur:
                self.json(400, {"erreur": str(erreur)})
            except (OSError, sqlite3.Error) as erreur:
                self.json(500, {"erreur": f"Lecture ou sauvegarde impossible. {erreur}"})
            except Exception:
                traceback.print_exc()
                self.json(500, {"erreur": "Le moteur local a rencontré une erreur. Consultez le terminal de l’atelier."})

        do_GET = traiter
        do_POST = traiter
        do_DELETE = traiter

    return ThreadingHTTPServer(("127.0.0.1", port), Requete)


def servir(cache: Path, base: Path, port: int) -> None:
    if not hasattr(np, "vecdot"):
        raise ValueError(f"NumPy {np.__version__} ne fournit pas vecdot. Installez les dépendances "
                         "avec « python -m pip install -r requirements.txt » dans l’environnement de l’atelier.")
    if not all(f.is_file() for route, (f, _) in FICHIERS.items() if route != "/atlas.json"):
        raise ValueError("Compilez l’interface avec « npm run build » avant de lancer l’application.")
    if not 0 <= port <= 65535:
        raise ValueError("Port hors limites.")
    with creer_serveur(cache, base, port) as serveur:
        print(f"Atelier Cémantix · http://127.0.0.1:{serveur.server_port}/", flush=True)
        try:
            serveur.serve_forever()
        except KeyboardInterrupt:
            pass

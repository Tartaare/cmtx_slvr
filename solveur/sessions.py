"""Journal SQLite local, publications atomiques et contrôle des modifications concurrentes."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .atelier import Atelier, Configuration, Objet
from .resolution import Recherche
from .secours import Secours


class Conflit(ValueError):
    pass


class Sessions:
    def __init__(self, fichier: Path, atelier: Atelier) -> None:
        fichier.parent.mkdir(parents=True, exist_ok=True)
        self.fichier = fichier
        self.atelier = atelier
        self.active: dict[tuple[str, int], Recherche | Secours] = {}
        with closing(sqlite3.connect(fichier)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS parties (
                id TEXT PRIMARY KEY, creation TEXT NOT NULL, revision INTEGER NOT NULL, etat TEXT NOT NULL
            )""")

    def liste(self) -> list[Objet]:
        with closing(sqlite3.connect(self.fichier)) as db:
            return [{"id": i, "creation": date, "statut": statut, "config": json.loads(config)}
                    for i, date, statut, config in db.execute("""
                        SELECT id, creation, json_extract(etat,'$.statut'), json_extract(etat,'$.config')
                        FROM parties ORDER BY creation DESC""")]

    def lire(self, identifiant: str) -> Objet:
        with closing(sqlite3.connect(self.fichier)) as db:
            ligne = db.execute("SELECT revision, creation, etat FROM parties WHERE id=?", (identifiant,)).fetchone()
        if ligne is None:
            raise KeyError("Partie introuvable.")
        revision, date, etat = ligne
        return dict(json.loads(etat), id=identifiant, revision=revision, creation=date)

    def creer(self, donnees: Objet, observations: list[Objet] | None = None) -> Objet:
        etat = self.atelier.creer(Configuration(**donnees))
        if observations is not None:
            self.atelier.avancer(etat, observations)
        identifiant = uuid4().hex
        date = datetime.now(timezone.utc).isoformat()
        with closing(sqlite3.connect(self.fichier)) as db, db:
            db.execute("INSERT INTO parties VALUES(?,?,0,?)", (identifiant, date, json.dumps(etat, allow_nan=False)))
        return dict(etat, id=identifiant, revision=0, creation=date)

    def modifier(self, identifiant: str, revision: int, action: str, entrees: list[Objet] | None) -> Objet:
        etat = self.lire(identifiant)
        conflit = "Cette partie a changé. Rechargez-la avant de continuer."
        if type(revision) is not int or revision != etat.pop("revision"):
            raise Conflit(conflit)
        date = etat.pop("creation")
        etat.pop("id")
        statut = etat["statut"]
        politique = self.active.pop((identifiant, revision), None)
        if action == "essai":
            politique = self.atelier.avancer(etat, entrees, politique)
        elif action == "pause" and statut == "active":
            etat["statut"] = "pause"
        elif action == "reprendre" and statut == "pause":
            etat["statut"] = "active"
        elif action == "interrompre" and statut in ("pause", "active"):
            etat["statut"] = "interrompue"
        else:
            raise ValueError("Cette action est indisponible dans l’état actuel de la partie.")
        with closing(sqlite3.connect(self.fichier)) as db, db:
            resultat = db.execute("UPDATE parties SET revision=revision+1, etat=? WHERE id=? AND revision=?",
                                  (json.dumps(etat, allow_nan=False), identifiant, revision))
            if resultat.rowcount != 1:
                raise Conflit(conflit)
        # Une seule politique chaude. Un changement de session ou un échec impose le rejeu du journal.
        self.active.clear()
        if politique is not None and etat["statut"] in ("active", "pause"):
            self.active[identifiant, revision + 1] = politique
        return dict(etat, id=identifiant, revision=revision + 1, creation=date)

"""Une session de résolution pas à pas. Seules les observations sont transmises à la politique."""
import math
import random
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from .modele import Modele, cle, mot_jouable
from .resolution import Essai, Recherche, Strategie, valider_observation
from .secours import Secours
from .simulation import Observation, Scenario, nouvelle_grille
from .sources import SOURCES

type Objet = dict[str, Any]


@dataclass(frozen=True)
class Configuration:
    source: str = "simulation"
    modele: str = "reduit"
    strategie: str = "secours"
    modele_source: str = "reduit"
    scenario: str = "exact"
    graine: int = 42
    budget: int = 20
    grille: str = ""

    def __post_init__(self) -> None:
        if (self.source not in ("simulation", "assiste") or self.modele not in SOURCES
                or self.modele_source not in SOURCES or self.strategie not in ("secours", "plan", "robuste")
                or self.scenario not in Scenario):
            raise ValueError("Source, modèle, scénario ou stratégie inconnus.")
        if type(self.budget) is not int or not 1 <= self.budget <= 200:
            raise ValueError("Le budget doit être compris entre 1 et 200 essais.")
        if type(self.graine) is not int or abs(self.graine) > 2**31 - 1:
            raise ValueError("La graine doit être un entier signé sur 32 bits.")
        if not isinstance(self.grille, str) or len(self.grille) > 80 or (self.source == "assiste" and not self.grille.strip()):
            raise ValueError("Indiquez la grille de la partie assistée (80 caractères maximum).")


@lru_cache(maxsize=4)
def charger(cache: Path, nom: str) -> Modele:
    try:
        return Modele(cache / nom, source=SOURCES[nom].empreinte)
    except FileNotFoundError as erreur:
        raise ValueError(f"Préparez le modèle avec « python -m solveur preparer {nom} ».") from erreur


def vue(politique: Recherche | Secours, config: Configuration, historique: list[Objet]) -> Objet:
    r = politique.recherche if isinstance(politique, Secours) else politique
    phase = politique.phase if isinstance(politique, Secours) else (
        "melange" if r.inference is not None else "exact_principal")
    modele = "original" if isinstance(politique, Secours) and phase != "exact_principal" else config.modele
    indices = np.flatnonzero(r.disponibles)
    n = len(indices)
    entropie = math.log2(n) if n else None
    probabilites = np.full(min(n, 6), 1 / n if n else 0)
    top = indices[:6]
    if n and r.inference is not None and r.inference.observations:
        indices, logs = r.inference.classement(r.disponibles)
        p = np.exp(logs - logs.max())
        p /= p.sum()
        non_nuls = p[p > 0]
        entropie = float(-non_nuls @ np.log2(non_nuls))
        places = np.argsort(-p, kind="stable")[:6]
        top, probabilites = indices[places], p[places]
    candidats = []
    for i, proba in zip(top, probabilites, strict=True):
        mot = r.modele.mots[i]
        ecarts = [100 * r.modele.cosinus(mot, o["mot"]) - o["temperature"] for o in historique
                  if o["statut"] == "score" and r.modele.indices.get(cle(o["mot"]), -1) >= 0]
        candidats.append({"mot": mot, "p": float(proba),
                          "rms": float(np.sqrt(np.mean(np.square(ecarts)))) if ecarts else None})
    return {"phase": phase, "modele": modele, "nombre": n, "entropie": entropie, "candidats": candidats}


class Atelier:
    def __init__(self, cache: Path) -> None:
        self.cache = cache

    def politique(self, config: Configuration, etendu: bool) -> Recherche | Secours:
        m = charger(self.cache, config.modele)
        if etendu:
            a = charger(self.cache, "original")
            return Secours(m, m.lignes_jouables, a, a.lignes_jouables, 2, 17)
        strategie = Strategie.ROBUSTE if config.strategie == "secours" else Strategie(config.strategie)
        return Recherche(m, m.lignes_jouables, strategie, 2, random.Random("choix:17"))

    @staticmethod
    def integrer(politique: Recherche | Secours, obs: Observation) -> Essai:
        if (isinstance(politique, Recherche) and obs.statut == "score"
                and politique.modele.indices.get(cle(obs.mot), -1) < 0):
            return Essai(obs, int(politique.disponibles.sum()) if politique.filtre_exact else None)
        return politique.enregistrer(obs)

    def creer(self, config: Configuration) -> Objet:
        debut = perf_counter()
        etendu = (config.strategie == "secours" and config.modele == "reduit"
                  and (self.cache / "original" / "rapport.json").is_file())
        politique = self.politique(config, etendu)
        modeles = {config.modele}
        if etendu:
            modeles.add("original")
        if config.source == "simulation":
            modeles.add(config.modele_source)
        empreintes = {nom: charger(self.cache, nom).empreinte_preparation for nom in sorted(modeles)}
        principal = charger(self.cache, config.modele)
        # Ouverture gagnante du benchmark d'entropie sur le lexique réduit à deux décimales.
        ouverture = principal.indices.get("hirsute", -1)
        mot = politique.prochain(config.budget, ouverture if ouverture >= 0 else None)
        return {"config": asdict(config), "etendu": etendu, "empreintes": empreintes, "statut": "active",
                "essais": [], "prochain": mot, "vue": vue(politique, config, []),
                "nombre_initial": len(principal.lignes_jouables), "initial_ms": round(1000 * (perf_counter() - debut), 2)}

    def avancer(self, etat: Objet, entrees: list[Objet] | None = None,
                politique: Recherche | Secours | None = None) -> Recherche | Secours:
        if etat["statut"] != "active":
            raise ValueError("Cette partie n’est pas active.")
        config = Configuration(**etat["config"])
        debut = perf_counter()
        for nom, signature in etat["empreintes"].items():
            if charger(self.cache, nom).empreinte_preparation != signature:
                raise ValueError("La version du modèle a changé depuis le début de la partie.")
        historique = [e["observation"] for e in etat["essais"]]
        if politique is None:
            politique = self.politique(config, etat["etendu"])
            for o in historique:
                self.integrer(politique, Observation(**o))
        joues = {cle(o["mot"]) for o in historique}
        if config.source == "simulation":
            if entrees is not None:
                raise ValueError("Les scores de cette partie proviennent du simulateur.")
            source = nouvelle_grille(charger(self.cache, config.modele_source), config.graine,
                                     scenario=Scenario(config.scenario))
            entrees = [asdict(source(etat["prochain"]))]
        if not isinstance(entrees, list) or not 1 <= len(entrees) <= config.budget - len(historique):
            raise ValueError("Fournissez des observations dans la limite du budget restant.")
        for donnees in entrees:
            if etat["statut"] != "active":
                raise ValueError("Des observations suivent la fin de la partie.")
            obs = Observation(**donnees)
            if not isinstance(obs.mot, str) or len(obs.mot) > 128 or not mot_jouable(cle(obs.mot)):
                raise ValueError("Le mot proposé doit être une forme jouable.")
            mot = valider_observation(obs.mot, obs, 2, joues)
            avant = etat["vue"]
            prediction = None
            m = charger(self.cache, avant["modele"])
            if historique and avant["candidats"] and m.indices.get(mot, -1) >= 0:
                prediction = round(100 * m.cosinus(avant["candidats"][0]["mot"], mot), 2)
            if obs.statut == "victoire":
                motif = None
                etat["statut"] = "resolu"
                apres = dict(avant, nombre=1, entropie=0.0, candidats=[{"mot": mot, "p": 1.0, "rms": None}])
            else:
                essai = self.integrer(politique, obs)
                motif = essai.motif_bascule
                historique.append(asdict(obs))
                apres = vue(politique, config, historique)
                if politique.epuisee:
                    etat["statut"] = "aucun_candidat"
                elif len(historique) == config.budget:
                    etat["statut"] = "budget_epuise"
            recommandation = etat["prochain"]
            etat["prochain"] = (politique.prochain(config.budget - len(historique), None)
                                if etat["statut"] == "active" else None)
            precedents = [c["mot"] for c in avant["candidats"]]
            for c in apres["candidats"]:
                c["rang_avant"] = precedents.index(c["mot"]) + 1 if c["mot"] in precedents else None
            etat["vue"] = apres
            inexploitable = (obs.statut == "score"
                             and charger(self.cache, apres["modele"]).indices.get(mot, -1) < 0)
            etat["essais"].append({"observation": asdict(obs), "prediction": prediction, "motif": motif,
                                   "inexploitable": inexploitable,
                                   "recommande": recommandation, "phase": avant["phase"], "apres": apres["phase"],
                                   "nombre": apres["nombre"], "entropie": apres["entropie"],
                                   "ms": round(1000 * (perf_counter() - debut), 2)})
            joues.add(mot)
            debut = perf_counter()
        return politique

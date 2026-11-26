"""Calibration hors ligne sur des températures relevées après la fin des grilles."""

import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .modele import Modele, cle, mot_jouable


LOTS = ("calibration", "validation", "test")
type Json = str | int | float | bool | None | list[Json] | dict[str, Json]


@dataclass(frozen=True)
class Releve:
    grille: str
    secret: str
    lot: str
    source: str
    mot: str
    observe: float


def lire_corpus(fichier: Path) -> tuple[list[Releve], str]:
    texte = fichier.read_text(encoding="utf-8-sig")
    parties = json.loads(texte)
    if not isinstance(parties, list):
        raise ValueError("Le corpus doit contenir une liste de parties terminées.")
    releves: list[Releve] = []
    grilles: set[str] = set()
    lots_secrets: dict[str, str] = {}
    for numero, partie in enumerate(parties, 1):
        if not isinstance(partie, dict) or not all(isinstance(partie.get(k), str) and partie[k].strip()
                                                  for k in ("grille", "secret", "lot", "source")):
            raise ValueError(f"Partie {numero} : grille, secret, lot et source sont requis.")
        grille, secret = cle(partie["grille"]), cle(partie["secret"])
        lot, source = partie["lot"], partie["source"].strip()
        observations = partie.get("observations")
        if lot not in LOTS or not mot_jouable(secret) or not isinstance(observations, list) or not observations:
            raise ValueError(f"Grille {grille} : lot, secret ou observations invalides.")
        if grille in grilles or lots_secrets.setdefault(secret, lot) != lot:
            raise ValueError(f"Grille répétée ou secret partagé entre plusieurs lots : {grille}.")
        grilles.add(grille)
        mots: set[str] = set()
        for paire in observations:
            if not isinstance(paire, list) or len(paire) != 2 or not isinstance(paire[0], str):
                raise ValueError(f"Grille {grille} : une paire [mot, température] est attendue.")
            mot, temperature = cle(paire[0]), paire[1]
            if not mot_jouable(mot) or mot in mots or mot == secret:
                raise ValueError(f"Grille {grille} : proposition invalide, répétée ou gagnante : {mot}.")
            if (type(temperature) not in (int, float) or not -100 <= temperature <= 100
                    or round(temperature, 2) != temperature):
                raise ValueError(f"Grille {grille} : température invalide pour {mot}.")
            mots.add(mot)
            releves.append(Releve(grille, secret, lot, source, mot, float(temperature)))
    if set(lots_secrets.values()) != set(LOTS):
        raise ValueError("Chaque lot doit contenir au moins une partie.")
    return releves, hashlib.sha256(texte.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Prediction:
    releve: Releve
    brut: float | None
    float64: float | None
    absents: tuple[str, ...] = ()
    ambigus: tuple[str, ...] = ()


def predire(modele: Modele, r: Releve) -> Prediction:
    indices = []
    absents: list[str] = []
    ambigus: list[str] = []
    for mot in (r.secret, r.mot):
        i = modele.indices.get(mot)
        if i is None:
            absents.append(mot)
        elif i < 0:
            ambigus.append(mot)
        else:
            indices.append(i)
    if absents or ambigus:
        return Prediction(r, None, None, tuple(absents), tuple(ambigus))
    a, b = (modele.vecteurs[i].astype(np.float64) for i in indices)
    controle = 100 * float(np.clip(a @ b, -1, 1))
    return Prediction(r, 100 * modele.cosinus(r.mot, r.secret), controle)


def centiemes(temperature: float) -> int:
    # Le premier arrondi est celui du simulateur, y compris aux demi-centièmes.
    return round(100 * round(temperature, 2))


def synthese(lignes: list[Prediction], marge: float | None) -> dict[str, Json]:
    paires = [(p.brut, p.releve.observe) for p in lignes if p.brut is not None]
    uniques = {m for p in lignes for m in (p.releve.secret, p.releve.mot)}
    manquants = {m for p in lignes for m in p.absents}
    bilan: dict[str, Json] = {
        "grilles": len({p.releve.grille for p in lignes}), "observations": len(lignes),
        "comparables": len(paires), "mots_distincts": len(uniques), "mots_absents": sorted(manquants),
        "fraction_mots_absents": len(manquants) / len(uniques),
        "mots_ambigus": sorted({m for p in lignes for m in p.ambigus}),
        "observations_non_comparables": len(lignes) - len(paires),
        "arrondis_exacts": 0, "fraction_exacte_toutes_observations": 0.0,
    }
    if not paires:
        return bilan
    predits, observes = zip(*paires, strict=True)
    ecarts = np.subtract(predits, observes)
    absolus = np.abs(ecarts)
    affiches = [abs(centiemes(x) - centiemes(y)) for x, y in paires]
    correlation_possible = len(set(predits)) > 1 and len(set(observes)) > 1
    bilan.update({
        "biais_moyen_c": float(np.mean(ecarts)), "mae_c": float(np.mean(absolus)),
        "mse_c2": float(np.mean(ecarts**2)), "rmse_c": float(np.sqrt(np.mean(ecarts**2))),
        "mediane_absolue_c": float(np.median(absolus)), "max_absolu_c": float(np.max(absolus)),
        "p95_absolu_c": float(np.percentile(absolus, 95)), "p99_absolu_c": float(np.percentile(absolus, 99)),
        "pearson": statistics.correlation(predits, observes) if correlation_possible else None,
        "spearman": statistics.correlation(predits, observes, method="ranked") if correlation_possible else None,
        "arrondis_exacts": affiches.count(0),
        "fraction_exacte_toutes_observations": affiches.count(0) / len(lignes),
        "arrondis_exacts_float64": sum(centiemes(p.float64) == centiemes(p.releve.observe)
                                       for p in lignes if p.float64 is not None),
        "troncatures_exactes": sum(math.trunc(x * 100) == centiemes(y) for x, y in paires),
        "fractions_compatibles_affichees": {str(t / 100): sum(e <= t for e in affiches) / len(paires)
                                           for t in (0, 1, 5, 10, 100)},
        "fraction_dans_marge_calibration": float(np.mean(absolus <= marge)) if marge is not None else None,
    })
    return bilan


def calibrer(fichier: Path, modeles: dict[str, Modele]) -> dict[str, Json]:
    releves, empreinte = lire_corpus(fichier)
    rapports: dict[str, Json] = {}
    priorites: dict[str, tuple[int, int, float, int]] = {}
    for nom, modele in modeles.items():
        predictions = [predire(modele, r) for r in releves]
        par_lot = {lot: [p for p in predictions if p.releve.lot == lot] for lot in LOTS}
        erreurs = [abs(p.brut - p.releve.observe) for p in par_lot["calibration"] if p.brut is not None]
        marge = float(np.percentile(erreurs, 95)) if erreurs else None
        validation = [(centiemes(p.brut), centiemes(p.releve.observe)) for p in par_lot["validation"]
                      if p.brut is not None]
        if erreurs and validation:
            priorites[nom] = (sum(a == b for a, b in validation), len(validation),
                              -statistics.mean(abs(a - b) for a, b in validation), -len(modele.mots))
        rapports[nom] = {
            "modele_sha256": modele.source_sha256, "marge_p95_calibration_c": marge,
            "lots": {lot: synthese(lignes, marge) for lot, lignes in par_lot.items()},
            "details": [{"grille": p.releve.grille, "mot": p.releve.mot, "brut_c": p.brut,
                         "affiche_c": None if p.brut is None else round(p.brut, 2),
                         "observe_c": p.releve.observe, "absents": list(p.absents),
                         "ambigus": list(p.ambigus)} for p in predictions],
        }
    retenu = max(priorites, key=priorites.__getitem__) if priorites else None
    return {
        "corpus_sha256_utf8_lf": empreinte, "modele_selectionne_sur_validation": retenu,
        "parties": {r.grille: {"lot": r.lot, "secret": r.secret, "source": r.source} for r in releves},
        "modeles": rapports,
    }

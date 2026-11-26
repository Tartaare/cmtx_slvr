"""Évaluation du rang sur les parties terminées et des sondes simulées communes."""

import random
from collections import defaultdict
from pathlib import Path

import numpy as np

from .calibration import Json, Releve, lire_corpus
from .inference import Inference, MARGE_CALIBRATION, Methode, PERTES
from .modele import Modele
from .simulation import Scenario, nouvelle_grille


def evaluer_historiques(modele: Modele, fichier: Path, marge: float = MARGE_CALIBRATION) -> dict[str, Json]:
    releves, empreinte = lire_corpus(fichier)
    parties: dict[str, list[Releve]] = defaultdict(list)
    for releve in releves:
        if releve.lot == "test":
            parties[releve.grille].append(releve)
    return {"corpus_sha256_utf8_lf": empreinte, "modele_sha256": modele.source_sha256,
            "lot": "test", "marge_calibration_c": marge, "resultats": evaluer_parties(modele, parties, marge)}


def evaluer_simulations(modele: Modele, nombre: int, graine: int, scenario: Scenario,
                        marge: float = MARGE_CALIBRATION) -> dict[str, Json]:
    if nombre < 1:
        raise ValueError("Il faut au moins une grille pour évaluer les rangs.")
    parties: dict[str, list[Releve]] = {}
    for grille in range(graine, graine + nombre):
        # Seul l’évaluateur possède l’étiquette. Les sondes sont tirées indépendamment.
        secret = random.Random(grille).choice(modele.jouables)
        source = nouvelle_grille(modele, grille, [secret], 2, scenario)
        sondes = random.Random(f"sondes:{grille}").sample(modele.jouables, min(3, len(modele.jouables)))
        historique = []
        for mot in sondes:
            obs = source(mot)
            if obs.statut == "victoire":
                break
            if obs.temperature is not None:
                historique.append(Releve(str(grille), secret, "simulation", scenario.value, mot, obs.temperature))
        parties[str(grille)] = historique
    return {"modele_sha256": modele.source_sha256, "scenario": scenario.value, "grilles": nombre,
            "premiere_graine": graine, "marge_calibration_c": marge,
            "resultats": evaluer_parties(modele, parties, marge)}


def evaluer_parties(modele: Modele, parties: dict[str, list[Releve]], marge: float) -> list[Json]:
    indices = modele.indices_solutions()
    resultats: list[Json] = []
    for grille, historique in parties.items():
        if not historique:
            continue
        for methode in Methode:
            inference = Inference(modele, indices, methode, 2, marge)
            disponibles = np.zeros(len(modele.mots), dtype=bool)
            disponibles[indices] = True
            secret = modele.indices.get(historique[0].secret, -1)
            for numero, r in enumerate(historique, 1):
                ligne: dict[str, Json] = {"grille": grille, "methode": methode.value, "essai": numero,
                                          "mot": r.mot, "observe_c": r.observe}
                resultats.append(ligne)
                i = modele.indices.get(r.mot, -1)
                if i < 0:
                    ligne["statut"] = "proposition_absente_ou_ambigue"
                    continue
                disponibles[i] = False
                inference.ajouter(r.mot, r.observe)
                candidats, valeurs = inference.classement(disponibles)
                position = np.flatnonzero(candidats == secret)
                if not position.size:
                    ligne["statut"] = "secret_hors_candidats"
                    continue
                pos = int(position[0])
                vrai = valeurs[pos]
                premier = int(np.argmax(valeurs))
                ligne.update({
                    "statut": "evalue", "scores_utilises": len(inference.observations),
                    "rang_secret": 1 + int(np.sum(valeurs > vrai)) + int(np.sum(valeurs[:pos] == vrai)),
                    "premier": modele.mots[candidats[premier]],
                })
                if methode not in PERTES:
                    poids = np.exp(valeurs - valeurs[premier])
                    total = poids.sum()
                    probas = poids / total
                    erreur = probas.copy()
                    erreur[pos] -= 1
                    ligne.update({
                        "probabilite_estimee_premier": float(probas[premier]),
                        "probabilite_estimee_secret": float(probas[pos]),
                        "perte_log": float((valeurs[premier] - vrai) + np.log(total)),
                        "brier_multiclasse": float(erreur @ erreur),
                    })
    return resultats

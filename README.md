# Cémantix en ligne de commande

La CLI TypeScript lit le score d’un essai sur la grille du jour. Le moteur Python résout des grilles simulées hors ligne à partir des températures de chaque proposition.

## Simuler une grille locale

Depuis la racine du dépôt, avec Python 3.12 et un environnement virtuel activé, installez NumPy et préparez le modèle réduit une fois.

```sh
python -m pip install -r requirements.txt
python -m solveur preparer reduit
python -m solveur simuler --graine 42 rivière maison poule
```

Cette graine et cette version du modèle donnent respectivement 20,68 °C, −2,97 °C et 6,07 °C. Relancez avec la même graine pour essayer d’autres mots sur la même grille. La commande émet une observation JSON par proposition et s’arrête au mot exact. Le statut distingue un score, un refus du simulateur et une victoire.

Le tirage utilise les formes jouables et non ambiguës du modèle actif. Pour restreindre les secrets tout en conservant les autres mots comme propositions, passez `--solutions mots.txt` (UTF-8, un mot par ligne). La simulation arrondit le cosinus multiplié par 100 à deux décimales par défaut. Une première comparaison sur quatre grilles réelles est disponible dans le [rapport de calibration](benchmarks/calibration/sprint-4.json).

## Résoudre une grille

```sh
python -m solveur resoudre --graine 42 --budget 20
```

Sur cette grille, avec les paramètres par défaut, « drone » obtient 0,49 °C et laisse 40 candidats. « aider » obtient −8,84 °C et laisse un seul candidat. Le troisième essai, « balane », confirme la victoire. Le tirage du secret et le choix du premier mot utilisent des graines distinctes.

Le résultat JSON contient les observations dans l’ordre. Le champ `candidats_exacts` compte les mots encore compatibles après un essai en stratégie exacte. La commande renvoie 0 pour une victoire confirmée, 2 pour un budget épuisé ou une liste de candidats vide, et 1 pour une erreur de données ou de lecture.

Pour continuer une grille commencée, ajoutez `--historique observations.jsonl` avec une observation UTF-8 par ligne au format de `simuler`. Conservez la même graine de grille, le modèle, la précision et le vocabulaire. Les observations importées sont vérifiées contre cette grille et consomment une partie du budget.

## Reproduire le benchmark de référence

```sh
python -m solveur benchmark --graine 0 --graine-choix 17 --parties 200 --budget 20 --export reproduction.csv
```

Chaque stratégie reçoit la même grille, le même premier mot et le même budget. Le rapport JSON compte les succès à différents seuils d’essais. Les moyennes et percentiles d’essais consommés incluent les échecs. Le CSV conserve une ligne par grille et par stratégie, avec les graines, l’ouverture, l’empreinte du modèle et le temps de résolution. Utilisez un nouveau nom de fichier à chaque export. [Résultats du sprint 3](benchmarks/sprint-3-exact.csv)

## Préparer et comparer les modèles

```sh
python -m solveur preparer original
python -m solveur comparer
```

Prévoyez environ 5 Go libres pour les deux originaux et leurs matrices préparées. La première acquisition utilise HTTPS. Les appels suivants lisent le cache local `.modeles/`. Vous pouvez aussi y placer les binaires sous les noms `reduit.bin` et `original.bin` avant la préparation. La commande vérifie le SHA-256 attendu. Les archives ZIP GitHub peuvent contenir un pointeur Git LFS à la place du modèle réduit.

Chaque modèle préparé contient son lexique ordonné, sa matrice normalisée en float32 et son `rapport.json` (empreintes, provenance, dimensions et anomalies). La comparaison vérifie les fichiers préparés et compte les formes communes après harmonisation de la casse, des apostrophes et de l’Unicode. Les accents restent significatifs.

Les vecteurs originaux sont de Jean-Philippe Fauconnier, *French Word Embeddings*, sous CC BY 3.0. Le modèle réduit provient de la sélection réalisée par Amodio pour Cemantbot. La préparation locale normalise les vecteurs. Les binaires restent dans le cache exclu de Git. [Modèles et attribution](https://fauconnier.github.io/) · [Licence CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) · [Source du modèle réduit](https://github.com/Amodio/cemantbot)

## Calibrer les scores réels

Après avoir préparé les deux modèles, lancez la comparaison depuis la racine du dépôt.

```sh
python -m solveur calibrer benchmarks/calibration/parties.json --export calibration-locale.json
```

Le rapport donne, pour chaque observation, la température relevée, le score brut calculé et la température arrondie. Les erreurs et la marge empirique sont en °C, à l’exception de la MSE en °C². Les taux de compatibilité aux tolérances indiquées portent sur les paires calculables. La fraction exacte sur toutes les observations inclut les mots absents ou ambigus dans le dénominateur. Sans option d’export, le JSON est écrit dans le terminal.

Pour ajouter une partie terminée, utilisez le format du corpus livré. Renseignez une source vérifiable, un identifiant de grille, le secret confirmé, le lot et les couples mot–température. Affectez les lots avant d’examiner les prédictions. Chaque grille apparaît une fois et toutes les parties partageant un secret appartiennent au même lot. Retirez la proposition gagnante, dont la température de 100 °C est imposée par le jeu. Le corpus est lu uniquement par la commande de calibration. [Corpus et sources](benchmarks/calibration/parties.json)

## Jouer sur la grille du jour

Installez Node.js 22.16 ou supérieur et disposez de Microsoft Edge sous Windows ou de Google Chrome sous macOS et Linux. Depuis le dossier du projet, installez les dépendances une fois avec `npm ci`, puis lancez un essai.

```sh
npm start -- rivière
```

Résultat observé sur la grille nº 1729 :

```text
Grille n°1729 · rivière · 4,52 °C · hors classement
```

La commande ouvre le site dans un navigateur en arrière-plan, soumet le mot et lit le résultat affiché. La dernière colonne indique la progression en ‰ lorsque le jeu classe le mot. Chaque lancement utilise une session temporaire indépendante.

Un mot refusé ou un site inaccessible produit un message sur la sortie d’erreur et un code de sortie de 1. Un essai réussi renvoie 0.

Pour utiliser une autre installation de Chromium, définissez la variable d’environnement `CEMANTIX_BROWSER` avec le chemin complet de son exécutable.

## Vérifier le projet

- `npm run build` vérifie les types en mode strict. Node exécute directement les fichiers TypeScript.
- `npm test` vérifie la saisie et le parcours du formulaire dans un navigateur local, hors ligne.
- `python -m unittest discover -s test -p "test_*.py" -v` vérifie la préparation, le calcul cosinus, la conservation du vrai candidat, le budget, les historiques et la comparaison des stratégies sur des modèles de contrôle.

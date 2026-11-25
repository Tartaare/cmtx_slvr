# Cémantix en ligne de commande

La CLI TypeScript lit le score d’un essai sur la grille du jour. Le moteur Python permet de préparer les modèles français et de proposer des mots sur une grille simulée hors ligne.

## Simuler une grille locale

Depuis la racine du dépôt, avec Python 3.12 et un environnement virtuel activé, installez NumPy et préparez le modèle réduit une fois.

```sh
python -m pip install -r requirements.txt
python -m solveur preparer reduit
python -m solveur simuler --graine 42 rivière maison poule
```

Cette graine et cette version du modèle donnent respectivement 20,68 °C, −2,97 °C et 6,07 °C. Relancez avec la même graine pour essayer d’autres mots sur la même grille. La commande émet une observation JSON par proposition et s’arrête au mot exact. Le statut distingue un score, un refus du simulateur et une victoire.

Le tirage utilise les formes jouables et non ambiguës du modèle actif. Pour restreindre les secrets tout en conservant les autres mots comme propositions, passez `--solutions mots.txt` (UTF-8, un mot par ligne). La simulation arrondit le cosinus multiplié par 100 à deux décimales par défaut. La correspondance avec les températures réelles sera mesurée lors de la calibration.

## Préparer et comparer les modèles

```sh
python -m solveur preparer original
python -m solveur comparer
```

Prévoyez environ 5 Go libres pour les deux originaux et leurs matrices préparées. La première acquisition utilise HTTPS. Les appels suivants lisent le cache local `.modeles/`. Vous pouvez aussi y placer les binaires sous les noms `reduit.bin` et `original.bin` avant la préparation. La commande vérifie le SHA-256 attendu. Les archives ZIP GitHub peuvent contenir un pointeur Git LFS à la place du modèle réduit.

Chaque modèle préparé contient son lexique ordonné, sa matrice normalisée en float32 et son `rapport.json` (empreintes, provenance, dimensions et anomalies). La comparaison vérifie les fichiers préparés et compte les formes communes après harmonisation de la casse, des apostrophes et de l’Unicode. Les accents restent significatifs.

Les vecteurs originaux sont de Jean-Philippe Fauconnier, *French Word Embeddings*, sous CC BY 3.0. Le modèle réduit provient de la sélection réalisée par Amodio pour Cemantbot. La préparation locale normalise les vecteurs. Les binaires restent dans le cache exclu de Git. [Modèles et attribution](https://fauconnier.github.io/) · [Licence CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) · [Source du modèle réduit](https://github.com/Amodio/cemantbot)

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
- `python -m unittest discover -s test -p "test_*.py" -v` vérifie le calcul cosinus, la préparation des vecteurs et la reproductibilité du simulateur sur un petit modèle créé pendant le test.

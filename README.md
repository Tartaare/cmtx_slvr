# Atelier Cémantix

L’application locale recommande un mot, interprète sa température et change de modèle lorsque les observations l’exigent. Le navigateur et la CLI Python utilisent le même moteur de résolution.

## Ouvrir l’application

Depuis la racine du projet, avec Python 3.12, Node.js 22.16 ou supérieur et les modèles préparés sous le compte qui lancera le serveur, exécutez les commandes suivantes.

```sh
python -m pip install -r requirements.txt
python -m solveur preparer reduit
python -m solveur preparer original
npm ci
npm run build
python -m solveur application
```

Ouvrez [l’atelier local](http://127.0.0.1:8765/). La première visite prépare une simulation de graine 42. **Jouer un essai** demande un seul score. **Mode automatique** enchaîne les essais simulés tant que l’atelier reste ouvert. Le mode adaptatif commence avec « hirsute », l’ouverture sélectionnée par entropie sur le modèle réduit. Il essaie ensuite de départager les candidats exacts, étend la recherche au modèle original si nécessaire, puis reclasse les mots par probabilité si les températures divergent encore. Si seul le modèle réduit est préparé, la partie utilise son repli probabiliste local. La rubrique **Diagnostic** indique la couverture effective.

Pour une grille réelle, choisissez **Nouvelle partie**, puis **Grille réelle · saisie ou import** et indiquez son identifiant. Reportez la température, un refus ou la victoire à chaque essai. Un score de 100 °C et une victoire sont deux réponses distinctes. À la création, vous pouvez importer un fichier JSONL au format de la commande `simuler`. Chaque ligne consomme un essai. Pour changer de grille, créez une nouvelle partie.

Le journal enregistre la recommandation, le mot effectivement joué, le modèle de recherche, la phase et le temps de calcul. Lorsqu’une hypothèse précédente existe, le journal donne aussi son score prédit et l’écart avec le score reçu. Le graphique permet de suivre les candidats, l’entropie, les écarts et les temps. Les probabilités du classement reposent sur le modèle et les observations disponibles.

Les parties sont conservées dans `.sessions/parties.sqlite3`. **Mes parties** permet de les retrouver après fermeture du navigateur ou redémarrage du serveur. **Repartir avec ces réglages** crée une nouvelle partie. L’export JSON conserve la configuration, les empreintes des modèles, les observations et les diagnostics. Utilisez `python -m solveur application --port 8766 --base mes-parties.sqlite3` pour choisir une autre adresse locale et une autre base. Arrêtez le serveur avec Ctrl+C dans son terminal.

Pour retirer une partie de l’historique, ouvrez **Mes parties**, cliquez sur **Supprimer** dans sa ligne, puis sur **Supprimer la partie**. La confirmation efface définitivement la partie et son journal local.

Après une mise à jour de l’application, relancez `python -m solveur application` et rechargez l’onglet pour utiliser le serveur et l’interface de la même version.

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

### Choisir des mots qui départagent les candidats

```sh
python -m solveur resoudre --graine 42 --strategie plan --ouverture entropie
```

Sur cette grille et le modèle réduit, « hirsute » donne 24,17 °C et laisse sept candidats. « frileux » donne −5,39 °C et isole « balane ». Le troisième essai confirme le mot.

`--ouverture` choisit le premier mot. La valeur par défaut est `aleatoire`. Les options `entropie` et `collisions` évaluent une présélection reproductible sur tout le vocabulaire des solutions. Le premier calcul conserve les cinq meilleurs mots de chaque classement dans `.modeles/ouvertures/`. Une modification du modèle préparé, du vocabulaire des solutions ou de la précision produit un cache distinct.

`--strategie` choisit les mots suivants. `entropie` maximise l’information attendue du prochain score. `collisions` minimise la probabilité que deux tirages indépendants donnent la même réponse. `decorrelation` choisit le candidat le moins corrélé aux essais précédents. `plan` utilise l’entropie au-delà de huit candidats, puis compare les suites d’essais en tenant compte du budget. Il peut jouer un mot extérieur aux solutions pour les départager. Au dernier essai, il tente une solution. Les calculs supposent des candidats équiprobables et un modèle exact.

### Résoudre malgré des températures divergentes

```sh
python -m solveur resoudre --strategie robuste --scenario aberrant --graine 42 --budget 10
```

Le mode `robuste` commence par l’inversion exacte. Sur cette grille, les scores de « drone » puis de « contact » épuisent les candidats compatibles. La trace indique `motif_bascule: aucun_candidat_exact`. Le solveur réintègre les solutions encore inédites, recalcule leur classement avec les deux observations et trouve « balane » au quatrième essai.

Le champ `estimation` donne le candidat en tête, sa probabilité estimée, l’échelle de bruit estimée en degrés et le mot dont la température s’écarte le plus de celle prédite pour ce candidat. Cet écart mesure la distance à l’intervalle d’arrondi. Le budget inclut toujours l’essai de confirmation.

Les scénarios `exact`, `bruit` et `aberrant` modifient la source de simulation. Pour une même graine de grille et un même mot, la température est reproductible, quel que soit l’ordre des essais. `--strategie student` et `--strategie melange` activent le classement probabiliste dès la première observation. Le mode exact reste sélectionné par défaut.

### Chercher au-delà du vocabulaire réduit

```sh
python -m solveur preparer original
python -m solveur resoudre --strategie secours --modele-source original --graine 27 --budget 8
```

Sur cette grille locale, « drone » laisse 40 candidats dans le réduit. Le score obtenu pour « entretenir » les élimine tous. En rejouant les deux températures dans le modèle original, le solveur isole « chignin-bergeron » et confirme ce mot au troisième essai.

`--modele-source` désigne le modèle du simulateur. `--modele` désigne celui dans lequel le solveur commence sa recherche (réduit par défaut). Le mode `secours` demande les deux modèles préparés. Il passe au second si le premier épuise ses candidats ou si le second reconnaît une sonde acceptée que le premier ne peut pas interpréter. Les refus et les observations importées comptent dans le même budget. Avec `--solutions`, seules les solutions de la liste sont admissibles dans chaque modèle.

Dans la trace JSON, `phase` indique la méthode active après l’observation, `motif_bascule` explique un changement et `scores_inexploitables` compte les scores dont la sonde manque ou est ambiguë dans le modèle actif. Lorsque les deux recherches exactes échouent, le repli par défaut reclasse les candidats du second modèle avec le mélange probabiliste. L’option expérimentale `--repli reconstruction` les classe selon une direction estimée par SVD avec régularisation de Tikhonov. Sa trace donne le rang, la dimension, le conditionnement des directions observées et la racine de l’erreur quadratique moyenne en °C.

Pour reproduire la comparaison sur les mots communs, les mots propres à l’original et les températures bruitées, utilisez un nouveau fichier de sortie.

```sh
python -m solveur.evaluation_secours --graine 1700 --parties 6 --budget 8 --export reproduction-secours.json
```

## Reproduire le benchmark de référence

```sh
python -m solveur benchmark --graine 0 --graine-choix 17 --parties 200 --budget 20 --export reproduction.csv
```

Chaque stratégie reçoit la même grille, le même premier mot et le même budget. Le rapport JSON compte les succès à différents seuils d’essais. Les moyennes et percentiles d’essais consommés incluent les échecs. Le CSV conserve une ligne par grille et par stratégie, avec les graines, l’ouverture, l’empreinte du modèle et le temps de résolution. Utilisez un nouveau nom de fichier à chaque export. [Résultats du sprint 3](benchmarks/sprint-3-exact.csv)

Pour inclure les quatre stratégies du sprint 5, ajoutez `--selection`. Rejouez la même commande avec `--ouverture aleatoire`, `--ouverture entropie` et `--ouverture collisions` pour comparer les premiers mots. Le temps du CSV commence après la préparation de l’ouverture commune. Pour reproduire le contrôle complémentaire, utilisez `--graine 200 --parties 1000` et comparez les lignes `exacte` avec ouverture aléatoire aux lignes `plan` avec ouverture par entropie. [Contrôle sur 1 000 grilles](benchmarks/sprint-5-controle.csv)

### Mesurer la robustesse et le rang du vrai mot

```sh
python -m solveur benchmark --robustesse --scenario aberrant --graine 1200 --parties 50 --budget 10 --export robustesse.csv
python -m solveur evaluer-inference benchmarks/calibration/parties.json --export rangs-reels.json
python -m solveur evaluer-inference --simulations 32 --scenario aberrant --graine 1250 --export rangs-simules.json
```

Le benchmark compare onze stratégies. Son score de Brier binaire évalue la probabilité annoncée pour le candidat en tête lorsque ce mot a effectivement été joué au tour suivant. La commande `evaluer-inference` compare les méthodes sur des observations communes. Elle fournit le rang du secret après chaque score exploitable et, pour les méthodes probabilistes, la perte logarithmique et le score de Brier multiclasse. Sur un corpus de parties terminées, elle utilise uniquement le lot de test. [Comparaisons et protocole](app-progress.md)

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

Dans l’atelier, ouvrez **Nouvelle partie**, choisissez **Grille du jour · résolution automatique**, réglez le budget puis cliquez sur **Résoudre la grille du jour**. Gardez l’onglet ouvert pour suivre les mots et les températures. **Arrêter l’automatique** suspend les prochains essais et laisse finir celui en cours. Pour continuer plus tard, ouvrez la session dans **Mes parties** et cliquez sur **Mode automatique**.

Pour résoudre automatiquement la grille officielle, démarrez l’atelier avec `python -m solveur application` sur son port par défaut (8765), puis exécutez cette commande dans un deuxième terminal.

```sh
npm start -- --resoudre 20
```

Le nombre fixe le budget maximal (1 à 200, 20 par défaut). Chaque essai apparaît dans le terminal et la partie est consultable dans **Mes parties**. Le code de sortie vaut 0 pour une victoire confirmée, 2 si la recherche se termine sans victoire et 1 en cas d’erreur.

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

- `npm run build` vérifie les types en mode strict et compile l’interface dans `dist/interface/`.
- Après le build, `npm run test:atelier` contrôle le parcours web dans Edge ou Chrome, le redémarrage du serveur, la reprise du budget, l’import et la confirmation. Ce test utilise un lexique isolé et une base temporaire. Définissez `CEMANTIX_PYTHON` si Python 3.12 avec NumPy est installé hors du PATH.
- `npm test` vérifie la saisie et le parcours du formulaire dans un navigateur local, hors ligne.
- `python -m unittest discover -s test -p "test_*.py" -v` vérifie la préparation, le calcul cosinus, la conservation du vrai candidat, le budget, les historiques et la comparaison des stratégies sur des modèles de contrôle.

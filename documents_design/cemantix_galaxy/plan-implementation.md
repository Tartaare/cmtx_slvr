# Sprint 21 · Galaxie sémantique

**Parcours.** L’atelier présente le dictionnaire complet. Une recherche, un clic ou un geste passe en exploration libre. Le solveur continue sa partie. « Reprendre le suivi » recadre la caméra sur le dernier essai. Le journal, les scores et les commandes restent disponibles en lecture textuelle.

| Lot | Critères | Livraison | Vérification |
| --- | --- | --- | --- |
| US-028 · Dictionnaire | D01–D03 | Atlas précalculé, une ligne par mot, 16 familles | Identifiants, empreinte, coordonnées et voisinages contrôlés |
| US-029 · Exploration | V01–V02, U01–U02 | Scène WebGL native, recherche, rotation, déplacement, zoom et retour global | Trois échelles inspectées dans Edge. Suivi suspendu au choix d’un mot et réactivé sur un essai réel |
| US-030 · Résolution | U03–U05 | Trajectoire ordonnée, meilleur score, victoire confirmée, journal complet et mode textuel | Simulation, grille assistée, archives, perte de connexion et grille du jour sur source de contrôle |
| US-031 · Performance | P01–P04 | Rendu groupé, résolution interne adaptative, animation à la demande | Protocole et résultats dans la section performance |

## Données et choix de projection

Le lexique préparé contient **55 402 mots uniques en 500 dimensions**. Le test d’intégrité reconstitue le fichier des mots dans l’ordre d’origine et retrouve son SHA-256 `8fb690c1c296a3c4345dd77e7dc67bf0f881de6d90f38e286f14b582ec8ba3b8`. Les trois coordonnées de chaque ligne sont finies. La ligne constitue l’identifiant dans cette version du lexique.

Sur 512 mots tirés avec la graine 21, on recherche les dix voisins exacts parmi tout le dictionnaire, d’abord par distance cosinus dans les embeddings, puis par distance euclidienne en 3D. Le rappel moyen atteint **14,39 % avec UMAP** et **0,47 % avec la PCA**. L’atlas retient UMAP. Le regroupement MiniBatchKMeans porte sur les vecteurs d’origine. Le navigateur charge seulement le résultat de ces deux calculs.

| Mot repère | Cinq voisins en 3D, du plus proche au plus éloigné |
| --- | --- |
| piano | concertiste, claveciniste, quatuor, chambriste, pleyel |
| rivière | piton, gour, watergang, éboulis, fleuve |
| chien | refuge, fugueur, fourrière, adoptant, implaçable |

Le voisinage musical reste reconnaissable. « Piton » près de « rivière » et « implaçable » près de « chien » illustrent la distorsion locale. Les traits de la scène représentent l’ordre des essais. Chaque température affichée provient de la partie.

Deux générations indépendantes ont produit le même fichier de 1 799 103 octets, de SHA-256 `16537da2e501500c17d350b52d63f06de91519e1053316e33956623264782fc5`. La recette contrôle également cette stabilité au rechargement de la partie.

## Captures de recette

| [Vue globale](vue-globale.png) | [Vue régionale](vue-regionale.png) | [Vue immersive](vue-immersive.png) |
| --- | --- | --- |
| Dictionnaire entier, quelques repères de familles | Carrés individualisés pendant le zoom | Sélection de « piano » et libellés de proximité |

## Contrôles fonctionnels

- **Sessions.** Le parcours Edge vérifie la création, la reprise après redémarrage, l’import JSONL, le passage au modèle étendu et la suppression avec confirmation. La grille officielle est testée sur une source de contrôle locale.
- **Suivi.** La simulation de graine 42 propose « hirsute » et confirme « balane » en trois essais. En exploration libre, une caméra centrée sur « piano » garde cette sélection pendant le premier essai. La reprise du suivi retrouve « hirsute ».
- **Rafale.** La grille archivée 202 fournit huit observations dans une seule réponse du moteur. Le journal retrouve les huit mots dans l’ordre, dont « maladie » à −0,92 °C. « Merveilleux » reste le meilleur à 61,65 °C et la caméra cible le dernier essai, « somptueux ». La confirmation de « magique » ajoute la neuvième ligne.
- **Accessibilité.** La recherche accepte Entrée, les flèches font tourner la vue, Maj + flèches la déplace, + et − règlent le zoom et Début restaure le cadrage global. La préférence de réduction du mouvement supprime l’interpolation. Le journal conserve les valeurs et les refus, y compris pour les mots absents de la carte.
- **États de jeu.** Le score de 100 °C et la confirmation de victoire sont traités séparément. Chaque nouvelle partie efface la sélection et la trajectoire précédentes. Le premier chargement et la coupure du moteur donnent un retour textuel.

## Performance et reproduction

`npm run test:galaxie` utilise Edge ou Chrome, les modèles locaux et une base temporaire. La mesure de navigation exclut le chargement. Le navigateur fait tourner la caméra à chaque rappel d’animation. Le script relève les intervalles entre rappels, la taille interne du canvas et, si disponible, le tas JavaScript du processus de rendu. Cinq paires de résolutions de la même simulation comparent le parcours automatique avec WebGL et en lecture textuelle.

**Poste du 26 novembre 2026.** Windows, Ryzen 7 7800X3D, GeForce RTX 4070 Ti SUPER, Edge 158.0.4370.33, ANGLE/Direct3D 11, 55 402 particules. La première ouverture de la version livrée a pris 1,85 s jusqu’à l’affichage de la scène et du premier mot du solveur.

| Critère | Conditions | Résultat |
| --- | --- | --- |
| P01 · Bureau | Version livrée, 60 s, fenêtre 1 920 × 1 080, scène 1 670 × 518 | **144 images/s**, p95 **7 ms** |
| P02 · Disposition mobile | Version livrée, 60 s, écran tactile émulé 375 × 812, DPR 2, processeur ralenti 4×, scène 563 × 644 | **143,9 images/s**, p95 **7 ms**. Mesure obtenue avec le GPU du PC. Validation matérielle sur téléphone ou GPU intégré encore ouverte. |
| P03 · Endurance | Première intégration, avant l’ajustement du contraste et des annotations, 15 min de rotation et 15 résolutions | **144 images/s** sur la première et la dernière minute. Le tas JS passe de 21 à 10 Mio, avec des relevés intermédiaires de 9 à 10 Mio. La mémoire GPU n’a pas été mesurée. |
| P04 · Débit du solveur | Version livrée, cinq paires alternées, graine 42, du déclenchement de l’automatique à la confirmation | Médiane **754 ms avec la scène**, **753 ms en mode textuel**, soit **+0,13 %** de durée. Les deux parcours incluent la cadence automatique de l’atelier. |

La première passe P04 incluait les délais de pilotage des clics par Playwright et donnait +6,96 %. La passe finale chronomètre depuis la page, entre les mêmes événements de jeu. Le seuil de 5 % porte ici sur cette durée de résolution de bout en bout.

**Rechargement.** Le serveur transmet 802 412 octets en gzip, puis répond HTTP 304 lorsque l’atlas conservé par le navigateur est à jour. Seize ouvertures consécutives de la prévisualisation ont affiché les 55 402 mots. Le test de régression interrompt les lectures, vérifie la proposition de relance et rétablit la scène. Le build strict, les quatre tests Node, les 26 tests Python, le parcours Edge de l’atelier et la recette courte passent.

[Mesures de la version livrée](mesures-controle.json) · [Relevés de la passe d’endurance](mesures.json)

[Spécification](galaxie-semantique-spec-ui-ux.md) · [Référence visuelle](galaxy_exemple1.png) · [Générateur](../../solveur/galaxie.py) · [Recette exécutable](../../test/recette-galaxie.ts)

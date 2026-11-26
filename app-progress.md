# Avancement

## Sprint 21 — Galaxie sémantique

US-028 à US-031 livrent la carte interactive du dictionnaire réduit. Les 55 402 mots proviennent du modèle préparé en 500 dimensions. Deux générations reproduisent la même projection UMAP, le même ordre de mots et les mêmes 16 familles. La scène WebGL se charge depuis un atlas local de 1,8 Mo.

L’atelier permet de rechercher un mot, de se déplacer dans la carte et de reprendre le suivi de la résolution en cours. Le journal restitue chaque essai, son résultat et les mots du modèle étendu situés hors carte. La réouverture d’une partie propose la vue globale. Le choix d’une nouvelle session efface la sélection précédente.

Le build TypeScript, les quatre tests Node, les 26 tests Python et le parcours Edge passent. La recette sur modèles complets vérifie la simulation de graine 42, le rejeu des huit scores de la grille 202, le mode sans WebGL et la navigation en disposition mobile. Les captures et mesures de performance sont réunies dans le [suivi d’implémentation](documents_design/cemantix_galaxy/plan-implementation.md).

## Sprint 20 — Base de la refonte

US-027 réduit l’interface à un fond noir et au logo en haut à gauche. Les anciens éléments restent inertes dans un modèle HTML et les scripts métier sont conservés pour les prochaines étapes. Les commandes de l’atelier ne sont donc temporairement plus accessibles depuis le navigateur.


## Sprint 19 — Interface compacte

US-026 retire les panneaux redondants et rassemble les commandes dans une fenêtre accessible depuis la navigation. Le tableau de bord affiche les derniers essais et le budget.

## Sprint 18 — Typographie et en-tête

US-025 applique Roboto Mono aux textes et commandes, avec un secours local, et retire le titre et la phrase d’introduction visibles de l’atelier. Le titre reste accessible ; celui des archives reste visible. La police est chargée depuis Google Fonts lorsqu’une connexion est disponible. Le build TypeScript passe ; les tests dépendent de l’accès au répertoire utilisateur et d’un environnement Python disponible.

## Sprint 16 — Analyse de la référence UI/UX

US-024 documente la composition en trois colonnes, la typographie, le réseau de mots et les indicateurs de la référence. Le suivi contient 19 critères à cocher lors de l’intégration. Trois choix restent ouverts pour la conception de l’atelier : la signification des liens et des pistes, la mesure de progression et les destinations de navigation. Le build, les trois tests Node, les 26 tests Python et le parcours navigateur passent. [Suivi de la refonte](documents_design/suivi-refonte.md)

## Sprint 15 — Logo de l’atelier

US-023 affiche le logo fourni dans le lien d’accueil, sur un fond vert profond. Le serveur local livre le PNG avec le type `image/png`. Le parcours Edge vérifie le chargement du logo et l’affichage à 375 pixels. Le build, les 26 tests Python et les trois tests Node passent.

## Sprint 14 — Connexion au moteur local

US-022 détecte au démarrage les installations de NumPy dépourvues de `vecdot`. Une exception interne du moteur renvoie désormais un diagnostic HTTP. Lors d’une coupure réseau, l’atelier retente une lecture une fois et invite à recharger la partie si la coupure persiste. Chaque action de jeu reste soumise une seule fois. Le parcours navigateur simule les coupures persistantes et transitoires. Le build, les 26 tests Python avec NumPy 2.3.5, les trois tests Node et le parcours navigateur passent.

## Sprint 13 — Accès aux modèles sous Windows

US-021 rétablit l’accès en lecture aux fichiers préparés des modèles réduit et original pour le compte Windows de l’atelier. Les fichiers avaient été préparés sous un autre compte. La création avec le modèle réduit et son secours original, le premier essai et la création avec le modèle original ont été vérifiés sous le compte de l’atelier sur une base temporaire. Le build, les 26 tests Python, les trois tests Node et le parcours Edge passent.

## Sprint 12 — Réponse du serveur lors d’une suppression

US-020 remplace l’erreur de lecture JSON par une demande de redémarrage lorsque le serveur en cours d’exécution répond HTTP 501 à la suppression. Le dialogue reste ouvert pour permettre une nouvelle tentative. Le test Edge reproduit la réponse HTML de l’ancien serveur et vérifie que la partie existe encore avant la nouvelle tentative. Le build, les 26 tests Python et les trois tests Node passent.

## Sprint 11 — Suppression dans Mes parties

US-019 ajoute une suppression individuelle avec confirmation. La partie et son journal sont effacés de la base locale. La révision affichée protège les modifications effectuées depuis un autre onglet. L’atelier vide invite à ouvrir une autre partie ou à en démarrer une.

Le parcours Edge vérifie l’annulation, le rejet d’une ancienne révision, la suppression de la partie ouverte, l’historique vide sur un écran de 375 pixels et la persistance après redémarrage du serveur. Le build, les 26 tests Python et les trois tests Node passent.

## Sprint 10 — Grille officielle depuis l’atelier

US-018 permet de lancer la résolution depuis Nouvelle partie et de suivre chaque résultat dans le journal. La grille 1730 a été confirmée en trois essais depuis le navigateur avec un budget de cinq. Le test navigateur couvre aussi le lancement sur écran étroit, la confirmation et le décompte du budget avec une source de contrôle.

## Sprint 9 — Résolution automatique de la grille du jour

US-017 relie les recommandations de l’atelier au formulaire officiel. La grille nº 1730 a été résolue en trois essais le 26 novembre 2026. Le test de régression distingue deux mots affichés à 100 °C par leur rang (999 ou 1000 ‰). Le build, les 26 tests Python, les trois tests Node et le parcours navigateur de l’atelier passent.

## Sprint 8 — Atelier de résolution local

US-014 à US-016 sont livrées. Le navigateur permet de jouer une simulation pas à pas ou automatiquement, de saisir les résultats d’une grille identifiée et de reprendre un historique JSONL. La recommandation, le budget, les candidats, leur probabilité estimée et la raison des bascules sont visibles pendant la partie. Une base SQLite locale conserve les observations et les configurations. Les modifications concurrentes sont contrôlées par révision.

**Contrôles sur les modèles complets.** La stratégie adaptative ouvre avec « hirsute ». Sur la simulation réduite de graine 42, « frileux » isole « balane », confirmé au troisième essai. Sur la graine 27 du modèle original, le score de « catastrophe » épuise les candidats du réduit et « chignin-bergeron » est confirmé au troisième essai dans l’original. Avec le scénario bruité sur cette même grille, le mélange probabiliste prend le relais au deuxième essai et confirme le mot au septième. Ces trois parcours vérifient l’intégration. Les comparaisons appariées de stratégies restent celles des sprints 5 à 7.

**Reprise et non-régression.** Le test de bout en bout ferme le processus serveur après un essai, le relance sur la même base et vérifie le prochain mot et le budget dans Edge. Il termine ensuite la simulation, importe un score dans une seconde grille, déclenche le secours et enregistre une victoire sur écran de 375 pixels. Le build TypeScript, les 26 tests Python, les deux tests Node du formulaire et le test navigateur de l’atelier passent.

Le prochain jalon est la validation finale comparative. Le fonctionnement sur la grille réelle reste assisté par la saisie du joueur.

## Sprint 7 — Mots absents du modèle réduit

US-012 et US-013 sont livrées. Le mode `secours` utilise la sélection discriminante du sprint 5 dans le modèle principal. En cas d’incompatibilité, il réinterprète les observations par mot dans le modèle alternatif. L’original de Fauconnier ajoute 371 303 formes jouables non ambiguës aux 55 402 mots du réduit selon le filtre du simulateur. Les candidats exacts restent prioritaires tant que les scores en laissent au moins un. La victoire exige une confirmation explicite de la source.

**Protocole.** Pour chaque graine de 1700 à 1705, le banc tire un mot commun et un mot propre à l’original. Il simule ce dernier avec des scores exacts puis avec un bruit gaussien d’écart-type 1 °C. Les quatre politiques reçoivent la même ouverture par grille, deux décimales et huit essais, confirmation comprise. Le banc connaît les secrets pour contrôler les résultats. Le solveur reçoit uniquement les observations. Deux exécutions ont reproduit toutes les suites de propositions et tous les statuts. [Résultats individuels et empreintes](benchmarks/sprint-7-secours.json)

| Politique | Mots communs, scores exacts | Mots hors réduit, scores exacts | Mêmes mots, scores bruités |
|---|---:|---:|---:|
| Plan, réduit seul | 6/6 | 0/6 | 0/6 |
| Robuste, réduit seul | 6/6 | 0/6 | 0/6 |
| Secours, repli probabiliste | 6/6 | 6/6 | 5/6 |
| Secours, repli par reconstruction | 6/6 | 6/6 | 0/6 |

Les six mots communs ont été confirmés dans le modèle principal. Les six mots propres à l’original ont été confirmés en trois essais chacun avec les scores exacts. Avec du bruit, les six grilles ont épuisé l’inversion exacte des deux modèles. Le mélange probabiliste a alors consommé 7,33 essais en moyenne, échec inclus. Il devient le repli par défaut du mode `secours`. La reconstruction reste accessible pour comparaison. L’échantillon porte sur des simulations et ne mesure pas le taux de réussite sur la grille quotidienne.

**Reconstruction.** Sur les six secrets hors réduit bruités, le cosinus moyen entre direction estimée et vrai vecteur passe de 0,168 avec quatre sondes à 0,254 avec douze sondes indépendantes du secret. La pseudo-inverse et Tikhonov (pénalité 0,01) donnent les mêmes moyennes à trois décimales. Cette mesure utilise des sondes dédiées, indépendamment du budget de résolution. Avec douze directions indépendantes en dimension 500, il reste 488 dimensions indéterminées. Une contrainte de norme unitaire laisse plusieurs solutions. Une régression robuste fondée sur les seuls résidus d’ajustement manque aussi d’information quand un système sous-déterminé peut interpoler des scores bruités. Le mélange évalue ces écarts sur des candidats du lexique.

Le build TypeScript, les deux tests Node et les vingt-deux tests Python passent. Les contrôles couvrent deux espaces de dimensions et d’indexation différentes, un mot absent des deux lexiques, un score inexploitable, les restrictions de vocabulaire, les vecteurs identiques et le dernier essai. Le prochain jalon est le sprint 8 consacré à l’application.

## Sprint 6 — Robustesse aux écarts de température

US-010 et US-011 sont livrées. Le mode `robuste` passe de l’inversion exacte au mélange probabiliste lorsque l’intersection des observations est vide. Il restaure les candidats admissibles encore inédits et rejoue tous les scores, y compris les négatifs. Les refus consomment un essai et excluent le mot joué. La trace indique le score le moins compatible avec le candidat alors en tête.

**Protocole.** Les graines 1200 à 1249 donnent les mêmes 50 secrets dans chaque scénario. Les onze stratégies partagent l’ouverture de chaque grille, le vocabulaire réduit, la précision de deux décimales et le budget de dix essais. Le solveur reçoit uniquement les réponses de la source. Le scénario « bruit » ajoute un bruit gaussien d’écart-type 1 °C. Le scénario « aberrant » utilise un bruit gaussien d’écart-type 0,15 °C et ajoute, avec une probabilité de 15 % par mot, un écart de signe aléatoire compris entre 8 et 16 °C. Le simulateur écrête et arrondit le résultat avant de le transmettre.

| Stratégie | Exactes résolues / 50 | Bruitées résolues / 50 | Avec valeurs aberrantes résolues / 50 | Essais moyens avec valeurs aberrantes |
|---|---:|---:|---:|---:|
| Inversion exacte | 50 | 0 | 0 | 1,98 |
| Cemantbot reproduit | 50 | 1 | 6 | 9,62 |
| Comptage simple | 50 | 0 | 4 | 9,74 |
| Perte absolue | 50 | 50 | 43 | 6,42 |
| Perte quadratique | 50 | 50 | 29 | 6,82 |
| Perte de Huber | 50 | 50 | 38 | 6,54 |
| Gaussienne | 50 | 50 | 33 | 5,98 |
| Laplace | 50 | 50 | 42 | 5,86 |
| Student à un degré de liberté | 50 | 50 | 50 | 5,04 |
| Mélange probabiliste | 50 | 50 | 49 | 4,98 |
| Exact puis mélange (`robuste`) | 50 | 50 | 49 | 5,28 |

Les moyennes incluent tous les essais consommés, y compris les arrêts sans candidat et les budgets épuisés. En scénario exact, le mode robuste et l’inversion exacte consomment tous deux 2,98 essais en moyenne. [Grilles exactes](benchmarks/sprint-6-exact.csv) · [Bruit gaussien](benchmarks/sprint-6-bruit.csv) · [Valeurs aberrantes](benchmarks/sprint-6-aberrant.csv)

Les pertes cumulent la distance à la case d’arrondi, avec un seuil de 1 °C pour Huber. Les méthodes bayésiennes calculent la masse de probabilité de la case, y compris les queues écrêtées à ±100 °C. Le modèle part d’un a priori uniforme sur les solutions et sur les échelles distinctes obtenues à partir du plancher, de 0,25, de 1 et de 4 °C. Le plancher vaut le maximum du demi-pas d’arrondi et de la marge de calibration (0,0047 °C par défaut, configurable). Chaque observation actualise en logarithmes le poids conjoint du candidat et de l’échelle. Le mélange utilise 95 % de Laplace et 5 % de Cauchy plus large. Ces poids sont des hypothèses de travail.

**Contrôle des probabilités.** Sur 32 autres graines (1250 à 1281), les méthodes reçoivent les mêmes trois sondes par grille en scénario aberrant. Après trois scores, le mélange classe le vrai mot premier sur 20 grilles (62,5 %), avec une confiance moyenne de 28,0 % dans son premier candidat et un score de Brier binaire de 0,316. Il sous-estime donc sa fréquence de réussite sur cet échantillon. Les probabilités affichées restent des estimations. [Rangs et probabilités par sonde](benchmarks/sprint-6-rangs.json)

**Historiques réels.** Sur les deux grilles réservées au test du sprint 4, le mélange classe « creux » deuxième puis premier, et « prestigieux » vingt-et-unième puis premier. Les sept méthodes classent le secret premier au deuxième score exploitable sur les deux grilles. Les deux mots absents du modèle réduit sont signalés. Ces historiques partiels mesurent le classement après des observations connues et ne fournissent pas le nombre d’essais d’une résolution autonome. [Résultats par observation](benchmarks/sprint-6-historiques.json)

Le build TypeScript, les deux tests Node et les dix-sept tests Python passent. Les régressions vérifient la normalisation des lois aux bornes, la réintégration du secret, le rejeu complet des observations, les budgets et les métriques sur des prévisions évaluables. Le sprint 7 portera sur les mots absents du modèle réduit et les stratégies de secours.

## Sprint 5 — Sélection des propositions

US-008 et US-009 sont livrées. Le moteur classe les propositions selon les températures qu’elles produiraient sur les candidats restants. Une victoire possède sa propre classe, même si un autre mot atteint 100 °C. À partition équivalente, le moteur préfère un candidat qui peut gagner immédiatement. Une sonde déjà jouée est exclue.

Le classement des ouvertures utilise une présélection déterministe d’au plus 128 mots jouables et 128 solutions, dédoublonnée. Sur le modèle réduit complet, ces listes coïncident. Les 128 propositions ont chacune été évaluées sur les 55 402 secrets possibles. « hirsute » arrive en tête pour l’entropie (12,068 bits, 5 916 réponses distinctes). « coquettement » arrive en tête pour les collisions (probabilité 0,0002713). Le calcul commun a pris environ 0,70 s sur cette machine avec le modèle déjà ouvert, contre environ 0,007 s pour relire le classement en cache.

Après l’ouverture, les stratégies informationnelles évaluent jusqu’à 128 candidats et 128 sondes supplémentaires quand l’ensemble est grand. La recherche s’arrête dès qu’une proposition distingue tous les candidats. À huit candidats ou moins, le mode plan compare les arbres qui essaient successivement des solutions et, si elle peut améliorer le résultat, une sonde extérieure suivie de cet arbre. Il maximise d’abord les victoires dans le budget, puis minimise les essais consommés. Les tests vérifient notamment une grille à quatre candidats où seule une sonde extérieure garantit la résolution en deux coups.

**Comparaison sur les graines 0 à 199.** Même simulateur exact, modèle réduit, précision de deux décimales, graine des choix 17, budget de 20 et un thread OpenBLAS. Chaque colonne donne la moyenne des essais consommés par grille, échecs inclus. Les neuf stratégies reçoivent le même premier mot dans chaque colonne. Le protocole aléatoire reproduit les ouvertures, statuts et nombres d’essais des cinq références du sprint 3.

| Stratégie | Ouverture aléatoire | hirsute | coquettement |
|---|---:|---:|---:|
| Inversion exacte | 2,890 | 2,885 | 2,900 |
| Entropie | 2,895 | 2,875 | 2,900 |
| Collisions | 2,895 | 2,875 | 2,900 |
| Plan | 2,895 | 2,875 | 2,900 |
| Faible corrélation | 2,930 | 2,910 | 2,900 |
| Cemantbot | 3,000 | 2,995 | 3,015 |
| Comptage | 2,955 | 2,940 | 2,975 |
| Voisin du mot le plus chaud | 20,000 | 19,985 | 20,000 |
| Hasard | 20,000 | 20,000 | 20,000 |

Les sept stratégies fondées sur les scores compatibles ont résolu toutes les grilles de chaque colonne. Le voisin a résolu une grille avec « hirsute », et le hasard a épuisé tous ses budgets. Avec « hirsute », l’inversion exacte prend 7,02 ms par grille en moyenne et le plan 7,19 ms, hors préparation commune. [Ouvertures aléatoires](benchmarks/sprint-5-aleatoire.csv) · [Ouverture par entropie](benchmarks/sprint-5-entropie.csv) · [Ouverture par collisions](benchmarks/sprint-5-collisions.csv)

**Contrôle complémentaire, graines 200 à 1199.** L’inversion exacte avec ouverture aléatoire et le plan avec « hirsute » résolvent chacun 1 000 grilles sur 1 000. Le plan passe de 2,920 à 2,889 essais en moyenne pour la comparaison des deux configurations. Il économise un essai sur 83 grilles, en consomme un de plus sur 52 et fait jeu égal sur 865. Il termine au plus en trois coups sur cet échantillon, contre quatre pour la référence. Le gain cumulé de 31 essais concerne le modèle exact et la combinaison ouverture–stratégie. La commande par défaut conserve le protocole de référence. [Résultats appariés](benchmarks/sprint-5-controle.csv)

Le build TypeScript, les deux tests Node et les douze tests Python passent. Le sprint 6 portera sur le classement des candidats quand les scores observés divergent du modèle.

## Sprint 4 — Calibration sur des parties terminées

US-006 et US-007 sont livrées. Le corpus contient **38 températures observées sur 4 grilles**, de −14,66 à 61,65 °C. Les secrets sont confirmés par la ligne de victoire de chaque capture. Les 13 listes françaises de voisins de Cemantbot donnent des rangs utiles à son propre benchmark mais aucune température. La capture fournie dans son dossier `images` contient 16 essais chiffrés avant la victoire et fait partie du test. Son numéro de grille est illisible ou absent de la capture, d’où un identifiant textuel stable. [Corpus et sources par partie](benchmarks/calibration/parties.json)

Sur les grilles 202 et 749, les relevés retiennent les cinq premiers essais, le dernier avant la victoire, les extrêmes et la température la plus proche de 25 °C, après dédoublonnage. La grille 922 et la capture Cemantbot fournissent tous leurs essais avant la victoire. La séparation des lots est fixée dans le corpus et contrôlée à l’import. Le secret de test n’intervient ni dans l’estimation de la marge ni dans le choix du modèle.

| Lot | Températures observées | Modèle réduit, scores exacts au centième | Modèle original, scores exacts au centième |
|---|---:|---:|---:|
| Calibration · magique | 8 | 8 | 8 |
| Validation · renvoi | 9 | 9 | 9 |
| Test · creux et prestigieux | 21 | 19 | 21 |

**Choix du modèle.** La sélection sur validation privilégie le nombre de températures exactes, puis la couverture, l’erreur absolue moyenne entre scores affichés et enfin le modèle le plus petit. Les deux modèles reproduisent les neuf températures de validation. Le réduit reste la référence pour les mots qu’il couvre. Le test montre l’intérêt du modèle original pour « avant-garde » et « avant-gardiste », absents du réduit. [Rapport, empreintes et écarts individuels](benchmarks/calibration/sprint-4.json)

**Précision.** Sur le test, l’erreur absolue moyenne avant arrondi vaut 0,00315 °C pour le réduit et 0,00316 °C pour l’original. L’arrondi au centième reproduit toutes les températures calculables. La troncature en reproduit 9 sur 21 pour l’original. Le contrôle du produit scalaire en float64 donne les mêmes températures arrondies que le moteur sur ce corpus. Aucune correction de biais n’est appliquée.

**Marge et portée.** Le P95 des écarts bruts du réduit, estimé sur huit observations de calibration, vaut 0,00470 °C. Seuls 17 des 19 scores calculables du test se situent dans cette marge, alors que les 19 arrondis sont exacts. Employer ce P95 comme seuil d’élimination rejetterait donc deux observations valides. L’inversion exacte est cohérente avec les scores couverts de ces quatre grilles. La compatibilité avec une nouvelle grille reste à vérifier au fil des observations.

Le build TypeScript, les deux tests Node et les neuf tests Python passent. Deux exécutions indépendantes de la commande ont produit un JSON identique octet par octet. Le sprint 5 portera sur la sélection des propositions avec le même protocole de benchmark que le sprint 3.

## Sprint 3 — Résolution automatique et premier benchmark

US-004 et US-005 sont livrées. L’inversion exacte conserve les candidats dont la température reproduit toutes les observations à la précision de la grille. Le filtrage matriciel inclut une marge pour les erreurs numériques, puis recalcule les scores retenus avec la même opération scalaire et le même arrondi que le simulateur. Les scores négatifs, les refus et la confirmation finale sont couverts.

**Protocole.** Modèle réduit, vocabulaire jouable complet, températures à deux décimales, graines de grille 0 à 199, graine des ouvertures 17 et budget de 20 propositions. Les cinq stratégies partagent le premier mot de chaque grille. Les autres propositions dépendent de leurs observations. Python 3.12, NumPy 2.3.5, `OPENBLAS_NUM_THREADS=1`. Deux exécutions ont reproduit les 1 000 résultats individuels pour l’ouverture, le statut et le nombre d’essais. [Résultats bruts](benchmarks/sprint-3-exact.csv)

| Stratégie | Résolues sur 200 | Résolues en 2 essais ou moins | Essais consommés en moyenne | Maximum consommé |
|---|---:|---:|---:|---:|
| Inversion exacte | 200 | 22 | 2,890 | 3 |
| Cemantbot, stratégie Python reproduite | 200 | 1 | 3,000 | 4 |
| Comptage des correspondances | 200 | 12 | 2,955 | 4 |
| Voisin du mot le plus chaud | 0 | 0 | 20,000 | 20 |
| Hasard sans répétition | 0 | 0 | 20,000 | 20 |

La référence Cemantbot suit le script autonome fourni (SHA-256 `ac0e960651d218c0c877db0927dba8724ba268c017fded4ad694b1b59ed62695`). Elle compte les écarts de cosinus inférieurs ou égaux à 0,0001, puis départage les candidats ayant le maximum de correspondances par la plus faible moyenne des cosinus absolus avec les mots déjà proposés. Le comptage simple conserve le premier ex æquo rencontré. L’inversion exacte choisit le premier candidat compatible dans l’ordre du modèle après l’ouverture.

Sur cet échantillon, l’inversion exacte et Cemantbot ont la même médiane de trois essais. Le gain moyen observé est de 0,11 essai par grille. La validation en conditions réelles dépend du sprint 4, qui mesurera les écarts entre températures simulées et observées sur des parties terminées.

Le build TypeScript, les deux tests Node et les six tests Python passent. Un contrôle via la CLI a également validé la reprise de la grille 42, le rejet d’un historique incompatible et l’arrêt au budget. Les tests d’inversion comparent les candidats restants à un calcul exhaustif après chaque observation, avec des précisions de zéro, deux et six décimales.

## Sprint 2 — Modèles vectoriels et simulateur hors ligne

US-002 et US-003 sont livrées. La préparation vérifie le binaire source, conserve les originaux et publie un cache après conversion complète. Le moteur charge la matrice normalisée en mémoire mappée. Le simulateur expose une fonction de proposition, avec un tirage reproductible et un vocabulaire de solutions configurable séparément.

| Contrôle | Modèle réduit Cemantbot | Modèle original Fauconnier |
|---|---:|---:|
| Entrées lues | 55 402 | 1 081 995 |
| Dimensions | 500 | 500 |
| Entrées préparées | 55 402 | 1 074 309 |
| Entrées écartées pour caractères invalides ou espaces | 0 | 7 682 |
| Entrées écartées pour encodage UTF-8 invalide | 0 | 4 |
| Formes ambiguës après normalisation lexicale | 0 | 53 |

Les 55 402 formes du réduit sont présentes dans l’original, qui apporte 1 018 854 formes normalisées supplémentaires. Le SHA-256 du réduit concorde avec son pointeur LFS. Pour l’original, le MD5 publié `14da334ef867fec69a086cd6b4805609` a été vérifié avant de fixer son SHA-256 dans le registre des sources. [Empreintes publiées](https://embeddings.net/embeddings/md5sum.txt)

Sur le modèle réduit, le produit matrice-vecteur de « rivière » a produit 55 402 scores en 6,8 ms lors d’une mesure locale, matrice déjà ouverte. L’écart absolu maximal avec le produit scalaire recalculé en float64 était de 1,33 × 10⁻⁷ au plus. Ce contrôle mesure la précision numérique du moteur. La calibration avec le jeu réel relève du sprint 4.

Le build TypeScript, les deux tests de la CLI et les trois tests Python passent. La régression couvre notamment le score négatif, deux mots distincts à 100 °C, les entrées invalides et la détection d’une conversion tronquée avant publication. Le prochain jalon est la résolution automatique de grilles simulées avec un premier benchmark de référence.

## Sprint 1 — Essayer un mot

US-001 est livrée. La commande accepte un mot, soumet le formulaire de la grille active et journalise le numéro de grille, le mot, sa température et sa progression. Elle relaie le message du jeu lorsqu’il refuse le mot.

Sur la grille nº 1729, le formulaire a affiché 4,52 °C pour « rivière » et a rejeté « zzzzzzzz ». Les appels HTTP directs avaient attribué 100 °C aux deux essais « maison » et « zzzzzzzz ». Le client utilise donc le résultat affiché par le jeu et vérifie que la ligne correspond au mot soumis.

Le test de régression reproduit l’activation différée du bouton Envoyer et l’ouverture des règles à l’initialisation du jeu. Il couvre un score classé, une température négative sans progression et un refus. La vérification TypeScript et les deux tests passent.

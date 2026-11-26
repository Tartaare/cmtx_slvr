# Avancement

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

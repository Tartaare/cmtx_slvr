# CÉMANTIX PWN
## Spécifications techniques — Version 1.0

### 1. Mission

Développer une application complète capable de résoudre automatiquement une énigme Cémantix en exploitant les scores de similarité sémantique associés aux mots proposés.

Le solveur doit surpasser les performances du projet Cemantbot, tant dans des conditions idéales où le modèle vectoriel est identique à celui du jeu que dans des conditions dégradées où des différences existent.

Le système doit être autonome dans ses décisions, reproductible, testable, maintenable et indépendant de son interface graphique.

**Ordre de priorité des objectifs :**

1. Maximiser le taux de résolution.
2. Minimiser le nombre de propositions nécessaires.
3. Minimiser le nombre de requêtes externes.
4. Minimiser le temps de calcul.
5. Maximiser la robustesse face aux divergences entre modèles.

Le solveur ne doit jamais exploiter une liste contenant les solutions futures, une fuite de données ou une connaissance préalable du mot recherché.

---

### 2. Ressources et projets de référence

Étudier et exploiter, sous réserve de leurs licences respectives, les ressources suivantes :

- Projet Cemantbot : https://github.com/Amodio/cemantbot
- Modèles Word2Vec de Jean-Philippe Fauconnier : https://fauconnier.github.io/
- Cémantix : https://cemantix.certitudes.org/
- Documentation officielle : https://static.certitudes.org/html/cemantix-faq
- Projet complémentaire d'inférence bayésienne : https://github.com/Birdycheat/cemantix-bayesian

Cemantbot constitue notre référence algorithmique initiale et notre baseline de performance.

Ne pas reproduire aveuglément son implémentation. Identifier les méthodes pertinentes, les reproduire proprement, corriger leurs limitations et mesurer objectivement les améliorations.

Vérifier les licences avant toute réutilisation ou redistribution de code et de données.

---

### 3. Architecture générale

Organiser l'application autour de composants indépendants :

- Gestionnaire de modèles vectoriels.
- Gestionnaire de vocabulaire.
- Moteur de calcul des similarités.
- Moteur d'inversion vectorielle.
- Moteur d'inférence probabiliste.
- Moteur de sélection des propositions.
- Système de calibration et de diagnostic.
- Gestionnaire des sessions de résolution.
- Interface d'acquisition des scores.
- Simulateur local.
- Moteur de benchmark.
- Interface utilisateur.
- Système de persistance et de journalisation.

Le cœur algorithmique doit pouvoir fonctionner sans interface graphique, sans connexion Internet et sans dépendance au site Cémantix.

Privilégier Python pour le moteur de calcul, avec NumPy, SciPy et Gensim. Utiliser une architecture permettant d'optimiser ultérieurement les opérations critiques avec des technologies compilées si les mesures le justifient.

Ne pas introduire de complexité architecturale sans bénéfice mesurable.

**Validation :** le moteur doit pouvoir résoudre une partie simulée depuis une interface en ligne de commande, indépendamment de tous les autres composants applicatifs.

---

### 4. Acquisition des modèles vectoriels

#### 4.1. Modèle principal

Récupérer le modèle français réduit utilisé par Cemantbot :

frWac_no_postag_phrase_500_cbow_cut10_stripped.bin

Le modèle est disponible dans le dossier models du dépôt.

Récupérer également le modèle original correspondant auprès de Jean-Philippe Fauconnier afin de disposer d'un vocabulaire plus étendu.

Le modèle réduit doit servir de première référence, mais ne doit pas être considéré comme nécessairement identique au modèle actuellement utilisé par Cémantix.

#### 4.2. Gestion des modèles

Créer un système permettant de charger, comparer, remplacer et versionner plusieurs modèles vectoriels.

Conserver pour chaque modèle :

- Sa provenance.
- Sa licence.
- Sa version.
- Son empreinte cryptographique.
- Son nombre de mots.
- Ses dimensions.
- Sa précision numérique.
- Ses résultats de calibration.
- Sa couverture lexicale constatée.

Normaliser les vecteurs une seule fois lors de leur préparation. Préserver les données originales et produire un format de stockage optimisé pour les calculs matriciels.

Vérifier l'intégrité des fichiers et détecter les vecteurs nuls, non finis, invalides ou dupliqués.

**Validation :** produire un rapport d'intégrité et de comparaison des modèles, accompagné de tests démontrant que les similarités calculées après normalisation correspondent aux similarités cosinus de référence.

---

### 5. Construction et gestion du vocabulaire

Distinguer impérativement deux ensembles :

- Le vocabulaire des propositions : mots susceptibles d'être utilisés pour obtenir une information.
- Le vocabulaire des solutions : mots susceptibles d'être le mot secret.

Le premier ensemble peut être plus vaste que le second.

Construire le vocabulaire initial à partir du modèle réduit de Cemantbot, puis l'enrichir avec le modèle original et des ressources lexicales françaises dont les licences sont compatibles.

Étudier notamment Lexique 3 et les données lexicales françaises disponibles publiquement.

Associer aux mots, lorsque ces informations sont disponibles :

- Leur fréquence d'utilisation.
- Leur catégorie grammaticale.
- Leur lemme.
- Leur caractère commun ou rare.
- Leur statut de validité.
- Leur présence dans les différents modèles.
- Leur éventuel statut de nom propre ou de forme fléchie.

Utiliser ces caractéristiques pour établir une probabilité initiale d'apparition comme solution.

Ne jamais éliminer définitivement un mot uniquement parce qu'il est rare ou grammaticalement atypique.

Gérer correctement les accents, apostrophes, caractères Unicode, homonymes, variantes orthographiques et différences de casse.

Ne pas confondre un mot absent du modèle local avec un mot refusé par Cémantix.

**Validation :** produire un rapport de couverture lexicale, identifier les différences entre les vocabulaires et vérifier que chaque mot reste correctement associé à son vecteur.

---

### 6. Calibration du modèle vectoriel

Cette étape est prioritaire. La qualité de la correspondance entre le modèle local et le jeu conditionne l'ensemble des performances.

#### 6.1. Constitution d'un jeu de calibration

Constituer un dataset de couples de mots accompagnés de scores Cémantix réellement observés et obtenus de manière autorisée.

Utiliser des parties terminées dont le mot secret est connu, des historiques de parties et des observations fournies par les joueurs.

Inclure des scores négatifs, faibles, moyens et élevés, ainsi que des mots appartenant à des domaines sémantiques variés.

Séparer strictement les données de calibration, de validation et de test par mot secret et par partie.

#### 6.2. Comparaison des scores

Pour chaque observation, comparer la similarité calculée localement avec le score réel.

Mesurer :

- L'erreur absolue moyenne.
- L'erreur quadratique moyenne.
- L'erreur médiane.
- Les percentiles 95 et 99 des erreurs.
- L'erreur maximale.
- Les coefficients de corrélation.
- La proportion de scores compatibles avec différentes tolérances.
- La proportion de mots absents du modèle.

Déterminer si les différences proviennent principalement de l'arrondi, de la quantification, de la précision numérique ou d'une divergence entre modèles.

Une corrélation élevée ne suffit pas à démontrer que deux modèles sont identiques.

#### 6.3. Sélection et correction du modèle

Comparer les modèles disponibles et sélectionner celui qui reproduit le plus fidèlement les observations.

Si un biais systématique est identifié, étudier une correction statistique validée sur des données indépendantes.

Ne pas appliquer de transformation complexe sans démontrer son intérêt sur le jeu de test.

**Validation :** produire un rapport de calibration reproductible permettant de justifier le modèle principal, sa marge d'erreur et les conditions dans lesquelles l'inversion exacte peut être utilisée.

---

### 7. Moteur de similarité vectorielle

Créer un moteur capable de calculer efficacement la similarité cosinus entre n'importe quel mot et l'ensemble des candidats.

Exploiter les vecteurs normalisés pour remplacer le calcul complet de similarité cosinus par des produits scalaires.

Utiliser des opérations matricielles vectorisées.

Le moteur doit permettre :

- Le calcul d'une similarité entre deux mots.
- Le calcul des similarités entre un mot et tout le vocabulaire.
- Le calcul des similarités entre plusieurs propositions et plusieurs candidats.
- La recherche des mots correspondant à une similarité précise.
- La recherche des voisins vectoriels.
- Le calcul des écarts entre scores observés et scores prédits.
- La quantification des scores conformément au comportement mesuré du jeu.

Ne pas confondre la recherche d'une similarité précise avec une recherche classique des mots les plus proches.

Éviter de précalculer systématiquement toutes les similarités entre tous les mots. Une telle matrice présenterait un coût mémoire et un coût de préparation disproportionnés pour une première version.

**Validation :** comparer les résultats du moteur optimisé avec une implémentation mathématique de référence et mesurer son temps de calcul sur le vocabulaire complet.

---

### 8. Moteur d'inversion de la similarité cosinus

Implémenter le principe fondamental de Cemantbot.

Pour chaque proposition accompagnée d'un score, calculer les similarités prédites entre le mot proposé et tous les candidats.

Identifier les candidats capables de reproduire le score observé.

Exploiter chaque nouvelle observation pour réduire progressivement l'espace des solutions possibles.

Le moteur doit utiliser la totalité des observations disponibles, y compris les mots froids et les scores négatifs.

Ne jamais limiter arbitrairement l'analyse aux deux premiers mots ou aux mots les plus chauds.

#### 8.1. Mode exact

Lorsque la calibration confirme une correspondance suffisante entre les modèles, exploiter les intervalles définis par la précision et la quantification des scores.

Conserver les candidats compatibles avec l'ensemble des observations.

Distinguer les véritables divergences des simples erreurs d'arrondi.

#### 8.2. Mode tolérant

Lorsque les observations ne sont plus compatibles avec le mode exact, utiliser des marges d'erreur adaptatives.

La tolérance doit dépendre des résultats de calibration, de la précision des scores et de l'incertitude estimée.

Ne pas utiliser une constante unique pour toutes les situations.

Conserver la possibilité de restaurer un candidat précédemment écarté lorsqu'une divergence de modèle est détectée.

**Validation :** sur un simulateur utilisant exactement le même modèle, le véritable mot secret ne doit jamais être éliminé à cause d'une erreur numérique ou d'un arrondi correctement modélisé.

---

### 9. Moteur d'inférence bayésienne

L'inversion vectorielle doit être complétée par un système probabiliste capable de fonctionner lorsque les scores locaux diffèrent des scores réels.

Attribuer à chaque candidat une probabilité initiale d'être le mot recherché.

Cette probabilité peut être uniforme ou pondérée par les caractéristiques lexicales, selon la configuration et les résultats des benchmarks.

Pour chaque nouvelle observation, actualiser la probabilité de chaque candidat en fonction de sa capacité à reproduire le score observé.

Un candidat dont les scores prédits correspondent précisément aux scores réels doit devenir plus probable.

Un candidat présentant des divergences doit être pénalisé progressivement, proportionnellement à leur importance.

Étudier plusieurs modèles de vraisemblance :

- Distribution gaussienne.
- Distribution de Laplace.
- Distribution de Student.
- Mélange de distributions permettant de gérer les observations aberrantes.

Utiliser un modèle robuste aux divergences occasionnelles et travailler dans l'espace logarithmique pour éviter les problèmes de précision numérique.

Tenir compte des intervalles d'arrondi plutôt que de considérer systématiquement les scores affichés comme des valeurs continues exactes.

Les probabilités annoncées devront être qualifiées de probabilités estimées si leur calibration empirique n'est pas démontrée.

**Validation :** comparer les différents modèles probabilistes sur des parties simulées bruitées et des historiques réels indépendants. Mesurer notamment le classement du vrai mot, le taux de résolution et la calibration des probabilités.

---

### 10. Minimisation de l'erreur globale

Implémenter une stratégie de classement des candidats fondée sur l'ensemble des écarts entre les scores observés et les scores prédits.

Comparer au minimum :

- La somme des erreurs absolues.
- La somme des erreurs quadratiques.
- Une fonction de perte robuste de type Huber.
- La vraisemblance probabiliste issue du moteur bayésien.

Cette stratégie doit exploiter toutes les observations disponibles et ne pas se limiter au comptage des correspondances comprises dans une marge fixe.

Éviter de comptabiliser deux fois la même information : si la minimisation de l'erreur est déjà intégrée dans le modèle de vraisemblance, ne pas multiplier arbitrairement les deux scores.

**Validation :** comparer cette méthode au simple comptage des correspondances de Cemantbot, particulièrement lorsque des différences existent entre les modèles.

---

### 11. Sélection optimale des propositions

Ce composant représente notre principal levier d'amélioration par rapport à Cemantbot.

Ne pas sélectionner systématiquement le mot le plus chaud, le plus probable ou un mot aléatoire.

Chaque proposition doit être choisie en fonction de son utilité pour identifier le véritable mot.

#### 11.1. Maximisation du gain d'information

Pour chaque proposition potentielle, calculer la distribution des scores qu'elle pourrait produire selon les candidats encore plausibles.

Évaluer sa capacité à séparer les candidats en groupes distincts.

Privilégier les propositions réduisant le plus fortement l'incertitude attendue après réception du prochain score.

Utiliser l'entropie et le gain d'information attendu comme critères de sélection.

Lorsque le modèle est incertain, intégrer cette incertitude dans les distributions de scores prédites.

#### 11.2. Minimisation des collisions

Identifier les propositions qui minimisent la probabilité que plusieurs candidats génèrent un score identique ou indiscernable.

Tester la minimisation de la masse de probabilité des groupes de candidats partageant la même réponse.

Comparer cette stratégie avec la maximisation de l'entropie.

#### 11.3. Équilibre entre exploration et résolution

Distinguer deux catégories de propositions :

- Les propositions exploratoires, destinées à acquérir une information discriminante.
- Les propositions de résolution, correspondant aux solutions les plus probables.

Prendre en compte la probabilité de résoudre immédiatement la partie lorsqu'un candidat est proposé.

Une proposition qui apporte légèrement plus d'information n'est pas nécessairement préférable à un candidat possédant déjà une forte probabilité d'être la solution.

Pour les petits ensembles de candidats, étudier une planification sur plusieurs coups afin de minimiser le nombre attendu de propositions restantes.

#### 11.4. Optimisation du premier mot

Déterminer empiriquement les meilleurs mots de départ.

Calculer leur capacité à discriminer l'ensemble du vocabulaire avant toute observation.

Ne pas confondre diversité sémantique et pouvoir discriminant mathématique.

Précalculer et mettre en cache une sélection de propositions initiales optimales, associée à chaque version du modèle et du vocabulaire.

#### 11.5. Optimisation du coût de recherche

Lorsque le nombre de propositions potentielles est trop important, utiliser une présélection, un échantillonnage reproductible ou une évaluation progressive.

Évaluer exhaustivement les propositions lorsque l'espace restant devient suffisamment petit.

Mesurer le compromis entre le temps consacré à sélectionner une proposition et le nombre d'essais économisés.

**Validation :** comparer systématiquement les stratégies aléatoires, les stratégies de similarité maximale, les stratégies de faible corrélation, l'entropie, la minimisation des collisions et la planification sur plusieurs coups.

---

### 12. Reconstruction du vecteur inconnu

Implémenter une méthode secondaire capable d'estimer directement le vecteur du mot secret à partir des propositions et de leurs scores.

Construire un système d'équations associant les vecteurs normalisés des propositions aux similarités observées.

Étudier les méthodes suivantes :

- Résolution par moindres carrés.
- Pseudo-inverse.
- Régularisation de Tikhonov.
- Décomposition en valeurs singulières.
- Régression robuste.
- Résolution tenant compte de la contrainte de norme unitaire.

Analyser le rang et le conditionnement du système.

Ne pas considérer qu'un petit nombre d'observations permet de reconstruire exactement un vecteur de 500 dimensions.

Utiliser le vecteur reconstruit pour identifier de nouvelles régions pertinentes dans le modèle principal ou dans un vocabulaire plus étendu.

Ne pas laisser cette stratégie contredire sans justification des observations exactes déjà acquises.

**Validation :** comparer la proximité entre le vecteur reconstruit et le véritable vecteur secret sur des parties simulées. Mesurer l'intérêt réel de cette méthode dans les situations où l'inversion principale échoue.

---

### 13. Gestion intelligente des stratégies

Créer un orchestrateur central capable d'adapter la stratégie de résolution à l'état courant de la partie.

L'orchestrateur doit exploiter :

- Le nombre d'observations disponibles.
- Le nombre de candidats plausibles.
- La distribution de leurs probabilités.
- La cohérence entre les scores observés et les scores prédits.
- L'incertitude du modèle.
- Le coût attendu des prochaines propositions.
- Le budget d'essais restant.

En conditions idéales, privilégier l'inversion exacte et la sélection de propositions discriminantes.

En présence de divergences, utiliser le moteur probabiliste et les fonctions de perte robustes.

En cas d'incompatibilité généralisée, réexaminer les observations, la calibration et la couverture lexicale, puis exploiter éventuellement un modèle alternatif ou la reconstruction vectorielle.

Ne pas additionner artificiellement les résultats de plusieurs algorithmes corrélés.

Chaque stratégie doit apporter une amélioration mesurable. Les stratégies redondantes ou inefficaces doivent pouvoir être désactivées.

**Validation :** simuler des parties nécessitant différentes stratégies et vérifier que l'orchestrateur sélectionne un comportement cohérent et explicable.

---

### 14. Déroulement d'une résolution

Le cycle complet doit suivre la logique suivante :

1. Identifier et initialiser la partie.
2. Charger le modèle vectoriel calibré.
3. Charger les vocabulaires et les probabilités initiales.
4. Restaurer les observations existantes, le cas échéant.
5. Sélectionner la meilleure proposition selon la stratégie active.
6. Obtenir le score associé à cette proposition.
7. Vérifier la validité de l'observation.
8. Enregistrer durablement le résultat.
9. Actualiser les contraintes vectorielles.
10. Actualiser les probabilités des candidats.
11. Analyser la cohérence des observations.
12. Adapter la stratégie si nécessaire.
13. Sélectionner la prochaine proposition.
14. Répéter jusqu'à confirmation de la solution ou atteinte d'une condition d'arrêt.

Une forte probabilité, un candidat unique ou une similarité proche de 100 ne doivent pas être considérés à eux seuls comme une victoire.

La résolution doit être confirmée explicitement par la source de score.

**Validation :** vérifier le déroulement complet, depuis une partie vide jusqu'à la confirmation de la solution, ainsi que depuis une partie déjà commencée.

---

### 15. Interface d'acquisition des scores

Séparer totalement l'acquisition des scores du moteur algorithmique.

Créer une interface commune permettant d'utiliser différentes sources :

- Un simulateur local.
- Des historiques de parties enregistrés.
- Une saisie ou un import de scores réels.

Le simulateur doit permettre une résolution entièrement automatique.

Pour le jeu réel, en l'absence d'une interface automatisée disponible, conserver un fonctionnement assisté permettant au joueur de renseigner les scores.

Ne pas désactiver les protections anti-automatisation du site.

L'intégration doit gérer les erreurs, les scores manquants, les mots refusés, les interruptions et les changements de partie.

Appliquer un budget strict de requêtes et ne jamais envoyer des propositions en masse.

**Validation :** démontrer qu'il est possible de remplacer une source de scores par une autre sans modifier le moteur de résolution.

---

### 16. Robustesse et situations dégradées

Prévoir explicitement les situations suivantes :

- Mot secret absent du vocabulaire réduit.
- Mot secret absent de tous les modèles.
- Proposition refusée.
- Proposition absente du modèle local.
- Score incorrect ou mal interprété.
- Différence de quantification.
- Modèle vectoriel incompatible.
- Absence totale de candidats exacts.
- Plusieurs candidats indistinguables.
- Vecteurs identiques associés à des mots différents.
- Observations contradictoires.
- Propositions déjà effectuées.
- Changement de partie quotidienne.
- Interruption de la résolution.
- Budget maximal d'essais atteint.

Le solveur doit pouvoir abandonner proprement lorsqu'il ne dispose plus d'informations suffisantes.

Ne jamais générer de boucle infinie, de fausse solution ou de répétitions incontrôlées.

En cas d'échec, fournir un diagnostic indiquant la cause probable et les observations problématiques.

**Validation :** créer des tests automatisés couvrant chacune de ces situations.

---

### 17. Simulateur local de Cémantix

Développer un simulateur reproduisant le principe de fonctionnement du jeu sans dépendance externe.

Le simulateur doit sélectionner un mot secret et retourner uniquement les informations normalement accessibles au solveur.

Prévoir plusieurs modes :

- Modèle vectoriel strictement identique.
- Arrondi et quantification configurables.
- Bruit aléatoire sur les scores.
- Erreurs systématiques.
- Observations aberrantes.
- Modèle vectoriel différent.
- Vocabulaire incomplet.
- Mots refusés.
- Vecteurs identiques.
- Relecture de parties historiques.

Le simulateur doit être isolé du solveur. Celui-ci ne doit jamais avoir accès directement au mot secret ni au vecteur correspondant.

Prévoir des graines aléatoires reproductibles.

**Validation :** exécuter des milliers de parties automatiquement sans aucune connexion Internet.

---

### 18. Benchmark et comparaison scientifique

La supériorité du solveur doit être démontrée par des résultats, et non supposée à partir de la sophistication des algorithmes.

#### 18.1. Baselines

Implémenter des références comparables :

- Sélection aléatoire.
- Sélection du mot le plus proche.
- Inversion exacte simple.
- Algorithme principal de Cemantbot.
- Inversion avec comptage des correspondances.

#### 18.2. Scénarios

Évaluer tous les algorithmes sur les mêmes parties, avec les mêmes vocabulaires, les mêmes observations disponibles et les mêmes budgets d'essais.

Créer des benchmarks distincts pour les conditions exactes, bruitées et réelles.

Pour les historiques réels incomplets, ne pas inventer les scores des propositions absentes. Utiliser ces historiques pour évaluer la qualité des prédictions et du classement, et non prétendre mesurer un nombre d'essais complet lorsque celui-ci ne peut pas être reconstitué.

#### 18.3. Métriques

Mesurer systématiquement :

- Le taux de résolution.
- Le nombre moyen d'essais.
- Le nombre médian d'essais.
- Les percentiles 90, 95 et 99.
- Le nombre maximal d'essais.
- Le taux de résolution en 2, 3, 5, 10 et 20 propositions.
- Le temps de calcul par proposition.
- Le temps total de résolution.
- La consommation mémoire.
- Le nombre de mots refusés.
- Le taux de faux diagnostics.
- La proportion de solutions absentes du vocabulaire.
- Le classement du véritable mot après chaque observation.

Les parties échouées doivent être comptabilisées explicitement. Ne pas améliorer artificiellement la moyenne en supprimant les échecs.

#### 18.4. Études d'ablation

Tester le système complet puis désactiver indépendamment chaque amélioration :

- Probabilités lexicales initiales.
- Inférence bayésienne.
- Tolérance adaptative.
- Maximisation du gain d'information.
- Minimisation des collisions.
- Reconstruction vectorielle.
- Modèles alternatifs.

Identifier précisément les composants responsables des améliorations.

#### 18.5. Objectifs de performance

Viser un taux de résolution de 100 % en conditions exactes lorsque le mot secret appartient au vocabulaire et que le budget permet de distinguer les candidats.

Viser une médiane inférieure ou égale à trois propositions dans ce même scénario.

Chercher à surpasser Cemantbot sur le nombre moyen d'essais et les percentiles élevés.

En conditions dégradées, rechercher une amélioration significative du taux de résolution par rapport à Cemantbot, à budget d'essais identique.

Ces objectifs sont des cibles expérimentales et non des performances garanties.

**Validation :** fournir un rapport comparatif complet, les résultats bruts, les configurations utilisées et une procédure permettant de reproduire chaque benchmark.

---

### 19. Optimisation des performances

Privilégier une implémentation CPU vectorisée avant d'envisager une accélération GPU.

Optimiser en priorité :

- Le chargement du modèle.
- La disposition mémoire des vecteurs.
- Les produits matriciels.
- La réutilisation des calculs.
- La réduction progressive de l'espace de recherche.
- Le calcul du gain d'information.
- Le traitement par lots.
- Le cache des propositions initiales.
- La limitation des allocations mémoire inutiles.

Évaluer l'intérêt des bibliothèques BLAS optimisées, du parallélisme CPU et des fichiers mappés en mémoire.

N'introduire CUDA, C++ ou Rust que si les profils de performance démontrent que leur utilisation apporte un gain pertinent.

Préserver la précision numérique des calculs critiques.

**Validation :** fournir des mesures à froid et à chaud, avec les caractéristiques du matériel utilisé. Identifier les principaux goulets d'étranglement.

---

### 20. Interface utilisateur

Créer une application web locale, utilisable depuis un navigateur, connectée au moteur de résolution.

L'interface doit privilégier la lisibilité des informations scientifiques et le contrôle de la résolution.

#### 20.1. Tableau de bord

Afficher :

- La partie courante.
- Le modèle vectoriel actif.
- L'état du solveur.
- Le niveau de calibration du modèle.
- Le nombre d'essais effectués.
- Le nombre de candidats restants.
- La stratégie active.
- Le temps de résolution.
- La prochaine proposition recommandée.
- La solution lorsqu'elle est confirmée.

#### 20.2. Historique des propositions

Afficher pour chaque essai le mot proposé, le score obtenu, le score prédit lorsque pertinent, l'écart constaté, le temps de calcul et la stratégie ayant motivé sa sélection.

#### 20.3. Liste des candidats

Afficher un classement dynamique contenant les candidats les plus plausibles, leur probabilité estimée, leur compatibilité avec les observations et leur erreur globale.

Mettre en évidence les changements de classement après chaque nouvelle observation.

#### 20.4. Visualisation algorithmique

Afficher graphiquement :

- La réduction du nombre de candidats.
- L'évolution de l'entropie.
- La distribution des probabilités.
- La convergence du solveur.
- Les écarts entre scores réels et prédits.
- Les changements de stratégie.
- Les performances temporelles.

Une projection vectorielle en deux ou trois dimensions peut être proposée à titre pédagogique, mais ne doit pas servir de base aux calculs de résolution.

#### 20.5. Contrôles

Permettre de démarrer, suspendre, reprendre, interrompre ou réinitialiser une résolution.

Permettre de sélectionner le modèle, la stratégie, la source de scores et le budget maximal d'essais.

Prévoir un mode automatique et un mode pas à pas.

**Validation :** l'utilisateur doit pouvoir effectuer une résolution complète, comprendre les décisions du moteur et diagnostiquer un échec depuis l'interface.

---

### 21. Persistance et historique

Conserver durablement les parties, les observations, les modèles utilisés et les configurations algorithmiques.

Enregistrer les performances de chaque résolution et les changements de stratégie.

Permettre de reprendre une session interrompue sans perdre ses observations.

Ne jamais écraser l'historique des parties précédentes.

Séparer les observations de résolution des mots secrets connus afin d'éviter toute fuite de données vers le moteur.

Permettre l'export des parties et des benchmarks dans des formats standards.

**Validation :** interrompre volontairement une partie, redémarrer l'application et vérifier que la résolution reprend dans un état cohérent.

---

### 22. Tests et qualité logicielle

Mettre en place des tests unitaires, des tests d'intégration, des tests de bout en bout et des tests de non-régression.

Tester particulièrement les propriétés mathématiques du moteur :

- Normalisation correcte des vecteurs.
- Symétrie de la similarité cosinus.
- Gestion des scores négatifs.
- Gestion des limites d'arrondi.
- Conservation du véritable candidat en conditions exactes.
- Normalisation des distributions probabilistes.
- Stabilité numérique des mises à jour.
- Cohérence du calcul de l'entropie.
- Absence de propositions répétées involontairement.
- Arrêt déterministe du solveur.

Mettre en place des tests empêchant le solveur d'accéder au mot secret du simulateur.

Intégrer les tests dans un processus d'intégration continue.

**Validation :** tous les tests critiques doivent réussir avant la livraison. Chaque anomalie connue doit être documentée.

---

### 23. Ordre d'implémentation obligatoire

**Phase 1 — Fondations**

Acquisition des modèles, préparation du vocabulaire, moteur vectoriel, simulateur local et premiers tests mathématiques.

**Phase 2 — Solveur de référence**

Reproduction de l'inversion vectorielle de Cemantbot, gestion des observations et premier benchmark de référence.

**Phase 3 — Calibration**

Constitution des jeux de données, comparaison des modèles, analyse des erreurs et sélection du modèle principal.

**Phase 4 — Optimisation du choix des mots**

Entropie, gain d'information, minimisation des collisions, optimisation du premier mot et planification des derniers essais.

**Phase 5 — Robustesse probabiliste**

Inférence bayésienne, tolérance adaptative, fonctions de perte robustes et diagnostic des divergences.

**Phase 6 — Stratégies de secours**

Reconstruction vectorielle, vocabulaire étendu, modèles alternatifs et orchestrateur adaptatif.

**Phase 7 — Application**

Interface utilisateur, persistance, gestion des sessions et intégration des différentes sources de scores.

**Phase 8 — Validation finale**

Benchmarks exhaustifs, études d'ablation, optimisation des performances, correction des anomalies et documentation.

Chaque phase doit être validée avant d'introduire la complexité de la suivante.

---

### 24. Livrables attendus

Livrer :

- Le code source complet et structuré.
- L'application web fonctionnelle.
- Le moteur de résolution autonome.
- Le gestionnaire de modèles et de vocabulaires.
- Le simulateur local.
- Les scripts d'acquisition et de préparation des données.
- Les jeux de tests.
- Les outils de benchmark.
- Les résultats expérimentaux bruts.
- Le rapport de calibration.
- Le rapport comparatif avec Cemantbot.
- La documentation de l'architecture.
- La documentation des algorithmes.
- Les instructions d'installation et d'utilisation.
- Le registre des licences.
- La liste des limitations connues.

### 25. Définition d'un projet terminé

Le projet ne sera considéré comme terminé que si :

- Le solveur fonctionne automatiquement en environnement local.
- Il exploite l'intégralité des observations disponibles.
- Son comportement est reproductible.
- Il fonctionne en conditions exactes et dégradées.
- Il sait diagnostiquer ses échecs.
- Il respecte ses budgets d'essais.
- Il ne dépend pas d'une connaissance préalable des solutions.
- Ses performances sont objectivement comparées à Cemantbot.
- Les améliorations revendiquées sont démontrées expérimentalement.
- L'ensemble de l'application est documenté et testable.

La sophistication algorithmique n'est pas une finalité. Tout composant ajouté doit contribuer à résoudre davantage de parties, avec moins de propositions ou une meilleure robustesse.
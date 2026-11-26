# Cémantix Pwn — Galaxie sémantique 3D

## 1. Objectif

Faire de la visualisation du dictionnaire l'élément central de l'expérience du solveur. L'utilisateur doit pouvoir observer l'algorithme explorer un univers de mots, comprendre ses déplacements et suivre sa progression vers le mot du jour.

La scène doit être immersive, minimaliste, interactive et fluide. Elle doit représenter le dictionnaire réel dans son intégralité en 3D, et non un réseau décoratif généré aléatoirement.

## 2. Direction artistique

S'inspirer de la dataviz de référence : un nuage de points dense, composé de régions colorées qui se fondent progressivement les unes dans les autres, sur un fond noir profond.

- Représenter chaque mot par une particule carrée, de petite taille à distance.
- Employer des couleurs distinctes mais harmonieuses pour différencier les familles sémantiques. Éviter les aplats opaques, les halos excessifs et la fumée volumétrique.
- Conserver une sensation de profondeur par la perspective, la densité et l'atténuation des éléments éloignés.
- Afficher les libellés en typographie sobre, avec une hiérarchie claire : mot courant, mots pertinents, autres mots.
- Préserver la direction artistique existante de l'application. Ne pas encombrer la scène de panneaux, légendes ou contrôles permanents.

## 3. Représentation des données

Le dictionnaire de référence annoncé contient **55 402 mots**, associés à des embeddings de 500 dimensions. Confirmer ces chiffres avec les données réellement utilisées avant intégration.

Calculer en amont une projection 3D des embeddings réels (UMAP à privilégier, PCA comme référence de comparaison). Les positions doivent rester stables entre les essais et les sessions, à version de données identique. Les régions colorées doivent découler de regroupements sémantiques réels, non d'une répartition arbitraire.

Chaque mot doit être présent dans la scène globale et identifiable par un identifiant stable. La projection est exclusivement destinée à la visualisation : elle ne remplace ni les vecteurs utilisés par le solveur ni les scores retournés par Cémantix. La distance en 3D n'est pas une mesure exacte de la proximité avec le mot du jour.

## 4. Navigation et niveaux de détail

Les trois niveaux constituent une seule scène continue, sans rupture de caméra ni changement brutal de représentation.

| Niveau | Comportement attendu |
|---|---|
| Global | Vue d'ensemble du dictionnaire, régions colorées reconnaissables, très peu de libellés. |
| Régional | Carrés individualisés, libellés des mots pertinents et voisins progressivement révélés. |
| Immersif | Caméra à l'intérieur du nuage, centrée sur le mot sélectionné ou testé, avec une perception claire de la profondeur. |

Permettre la rotation, le zoom, le déplacement, la sélection d'un mot et le retour à la vue globale. Les libellés doivent rester lisibles, orientés vers la caméra, sans chevauchements importants. Leur densité s'adapte à la distance et à l'espace disponible.

Prévoir deux modes : suivi automatique du solveur et exploration libre. Une interaction manuelle suspend le suivi automatique sans interrompre la résolution. Une action explicite permet de le réactiver.

## 5. Animation de la résolution

La visualisation est pilotée par les événements réels du solveur, jamais par une simulation indépendante de sa recherche.

- **Essai en cours :** la caméra se déplace avec fluidité vers le mot testé ; celui-ci devient le point focal.
- **Résultat reçu :** le mot adopte un indicateur visuel correspondant à son score réel. Distinguer clairement les couleurs des clusters de celles utilisées pour les scores, par exemple avec un contour ou un marqueur dédié.
- **Historique :** conserver la trace des mots testés et matérialiser les déplacements successifs avec des lignes fines. Limiter les connexions visibles aux trajectoires et voisinages utiles.
- **Meilleur essai :** identifier le meilleur score obtenu, sans déplacer artificiellement les mots ni inventer une direction vers la solution.
- **Solution :** mettre en évidence le mot trouvé uniquement après confirmation par le jeu.

En cas d'essais rapides, agréger ou accélérer les transitions visuelles pour éviter une file d'animations en retard. Ne jamais ralentir le solveur pour attendre la caméra. L'historique doit conserver tous les essais, même ceux dont la transition n'a pas été animée individuellement.

Prévoir une réduction des mouvements et un état dégradé lisible si le rendu 3D est indisponible.

## 6. Contraintes de rendu

Privilégier Three.js et un rendu GPU groupé des particules (`BufferGeometry`, shaders ou instanciation selon les besoins). Ne pas créer un objet 3D, un élément DOM ou un matériau indépendant pour chaque mot.

Charger les positions précalculées et les métadonnées utiles ; ne pas recalculer la projection dans le navigateur. Adapter la densité des libellés, les effets et la résolution interne aux performances de l'appareil. Conserver tous les mots dans les données de la scène, même si le niveau de détail réduit temporairement leur représentation à l'écran.

Objectif : 60 FPS sur ordinateur récent et au moins 30 FPS en mode dégradé sur les appareils moins puissants. La résolution du solveur doit rester indépendante du rendu. Aucun effet esthétique ne doit être conservé au détriment de la fluidité.

## 7. Tests de recette

Les seuils ci-dessous sont des objectifs de recette proposés, à valider sur les appareils cibles. Tester avec le dictionnaire complet et de vrais événements du solveur, pas uniquement une scène de démonstration.

| ID | Test | Critère de réussite |
|---|---|---|
| D01 | Intégrité du dictionnaire | Le nombre d'identifiants uniques correspond exactement au dictionnaire réel ; chaque mot possède des coordonnées 3D finies. Aucun mot fictif, manquant ou ajouté. |
| D02 | Cohérence sémantique | Vérifier plusieurs familles de mots connues et mesurer la conservation des voisinages entre embeddings originaux et projection. Comparer UMAP et PCA sur le même échantillon ; documenter les distorsions et justifier le choix. |
| D03 | Stabilité spatiale | Rejouer une session et recharger la page : à version de données identique, les mêmes mots conservent les mêmes positions et couleurs de cluster. |
| V01 | Fidélité visuelle | La vue globale évoque la référence : fond sombre, nuage dense, régions colorées, profondeur perceptible, carrés et interface minimaliste. Validation visuelle sur captures des trois niveaux. |
| V02 | Lisibilité | Aucun chevauchement majeur entre les libellés prioritaires ; mot courant et meilleur essai identifiables immédiatement, y compris sans distinguer les couleurs. |
| U01 | Navigation | Zoomer de la vue globale jusqu'au mot, tourner autour, sélectionner un autre mot et revenir à la vue globale sans saut de caméra, clipping gênant ou perte de sélection. |
| U02 | Contrôle utilisateur | Le mouvement manuel suspend le suivi ; le solveur continue ; la reprise recentre correctement la caméra sur l'état courant. |
| U03 | Synchronisation | Rejouer une suite d'essais connue, incluant résultats négatifs, nouveaux meilleurs scores et solution. Vérifier les mots, scores, états et ordre des événements affichés contre le journal réel. |
| U04 | Essais en rafale | Rejouer des événements plus vite que les animations. Aucun essai perdu dans l'historique, aucun retard croissant de la caméra, aucun blocage du solveur. |
| U05 | Accessibilité et adaptation | Tester redimensionnement, mobile, commandes clavier utiles, réduction des mouvements et indisponibilité WebGL. Les résultats restent consultables sans scène 3D. |
| P01 | Fluidité desktop | Sur un PC récent de référence, en 1080p, viser au moins 58 FPS moyens et un 95e percentile du temps de frame inférieur ou égal à 20 ms sur 60 s de navigation et de résolution. |
| P02 | Mode dégradé | Sur GPU intégré ou mobile cible, viser au moins 30 FPS moyens et un 95e percentile inférieur ou égal à 40 ms après adaptation automatique de la qualité. |
| P03 | Endurance | Faire tourner la scène pendant 15 min avec navigation et essais répétés. Pas de fuite mémoire persistante, d'accumulation d'objets GPU ou de baisse progressive significative des FPS. |
| P04 | Indépendance du solveur | Comparer le débit de résolution avec et sans visualisation sur le même scénario reproductible. Aucun blocage par les animations ; viser une dégradation médiane inférieure à 5 %. |

Consigner pour les tests de performance : matériel, navigateur, résolution, nombre de mots, qualité graphique, FPS moyens, temps de frame au 95e percentile et mémoire lorsque mesurable. Exclure la phase de chargement initial des mesures de navigation et la mesurer séparément.

## 8. Livrables et validation finale

Fournir une scène intégrée à l'application, connectée au solveur réel, accompagnée de captures des trois niveaux de détail et d'un court rapport de recette avec résultats mesurés, appareils testés et écarts éventuels.

La fonctionnalité est considérée réussie lorsque le dictionnaire réel est explorable dans son intégralité, que la recherche est représentée fidèlement et que les objectifs de fluidité sont atteints sans compromettre la lisibilité ni le fonctionnement du solveur.

# Sprint 21 · Galaxie sémantique

Le joueur ouvre la carte complète, explore un mot, lance un essai puis retrouve le résultat dans la carte et le journal. L’exploration libre et le mode automatique du solveur disposent de commandes indépendantes.

| Lot | Critère de sortie | Preuve attendue | État initial |
| --- | --- | --- | --- |
| US-028 · Données | D01–D03 · Un identifiant par ligne du lexique réduit, projection versionnée et familles calculées sur les vecteurs | Contrôle d’intégrité, comparaison des voisinages UMAP/PCA et test de reproductibilité | À mesurer |
| US-029 · Exploration | V01–V02, U01–U02 · Une scène continue et des commandes utilisables au clavier, au tactile et à la souris | Captures globale, régionale et immersive, sélection et reprise du suivi | À intégrer |
| US-030 · Partie | U03–U05 · Essais réels, meilleurs scores, victoire, historique intégral et repli sans WebGL | Parcours navigateur sur une base isolée et contrôle mobile | À intégrer |
| US-031 · Recette | P01–P04 · Fluidité, endurance et indépendance du solveur | Mesures avec appareil, navigateur, résolution, durée et limites | À mesurer |

Architecture retenue pour ce sprint : génération hors ligne à partir du modèle préparé, livraison locale des positions et du lexique, rendu groupé en WebGL natif, état de partie issu de l’API existante. Le modèle étendu peut proposer un mot extérieur à la carte ; le journal doit alors l’indiquer et conserver le score.

[Spécification et critères de recette](galaxie-semantique-spec-ui-ux.md)

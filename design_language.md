# Langage visuel · Galaxie sémantique

L’accueil s’ouvre sur le dictionnaire. La scène 3D couvre la fenêtre bord à bord. Le logo et le titre Cémantix occupent le coin supérieur gauche. La recherche, le zoom, le retour à la vue globale et l’aide de navigation se superposent à la scène.

Dans l’atelier de résolution, la carte, la proposition du solveur et le journal forment trois niveaux de lecture dans cet ordre. Les diagnostics et paramètres de session s’ouvrent à la demande.

| Élément | Règle |
| --- | --- |
| Surface et texte | Fond graphite `#0a0c0f`, scène presque noire, texte principal `#f2f1ed`, secondaire `#a5acb2`. Les filets séparent les fonctions. |
| Action principale | Ambre `#f5b86d` pour jouer un essai, signaler le suivi et repérer le focus clavier. |
| Typographie | Sans empattement pour la navigation et le mot proposé. Chasse fixe pour les libellés de carte, relevés et mesures. Piles de polices locales définies dans `interface/style.css`. |
| Dictionnaire | Une particule carrée par mot. La couleur identifie son groupe de vecteurs. Les traits relient deux essais successifs localisables. |
| Résultats | Contour pour un essai, étoile pour le meilleur, coche pour une victoire confirmée. Le score reste lisible en toutes lettres ou en degrés dans le journal. |
| Mouvement | Une caméra continue entre trois échelles. Une manipulation suspend le suivi. La préférence système de réduction du mouvement applique la pose directement. |
| Petit écran | À l’accueil, la scène suit la hauteur visible et les commandes respectent les zones sûres. Dans l’atelier, la commande de jeu et le journal se lisent sous la carte, dans une colonne. |

[Spécification de la galaxie](documents_design/cemantix_galaxy/galaxie-semantique-spec-ui-ux.md)

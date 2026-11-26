# Langage visuel · Galaxie sémantique

L’accueil s’ouvre sur le dictionnaire. La scène 3D couvre la fenêtre bord à bord. Le logo et le titre Cémantix occupent le coin supérieur gauche. La recherche, le zoom, le retour à la vue globale et l’aide de navigation se superposent à la scène.

Dans l’atelier de résolution, la carte, la proposition du solveur et le journal forment trois niveaux de lecture dans cet ordre. Les diagnostics et paramètres de session s’ouvrent à la demande.

| Élément | Règle |
| --- | --- |
| Surface et texte | Fond graphite `#0a0c0f`, scène presque noire, texte principal `#f2f1ed`, secondaire `#a5acb2`. Les filets séparent les fonctions. |
| Action principale | Ambre `#f5b86d` pour jouer un essai, signaler le suivi et repérer le focus clavier. |
| Typographie | Sans empattement pour la navigation et le mot proposé. Chasse fixe pour les libellés de carte, relevés et mesures. Piles de polices locales définies dans `interface/style.css`. |
| Dictionnaire | Une particule ronde et ombrée par mot. La taille apparente augmente au premier plan avec un plafond progressif. La couleur identifie le groupe de vecteurs. Les arcs fins suivent la scène 3D jusque sur les bords de la vue. Le zoom révèle davantage de liens locaux. |
| Repères | En vue globale, les champs lexicaux s’affichent au voisinage du centre de leur groupe, avec une pastille de sa couleur. Au survol, le titre prend un filet de cette couleur et les points de son groupe gagnent en luminosité. Les autres points passent en gris neutre en conservant leur opacité et leur relief. Les mots apparaissent en vue rapprochée. Les libellés se répartissent sans recouvrir les commandes ou les repères prioritaires. |
| Résultats | Sur une grille réelle, dès qu’un essai est localisable, les mots non testés et leurs arcs passent au second plan. Les arcs pointillés suivent l’ordre des essais. Un contour signale un essai, une étoile repère le meilleur et une coche indique la victoire. |
| Mouvement | Une caméra continue entre trois échelles. Une manipulation suspend le suivi. La préférence système de réduction du mouvement applique la pose directement. |
| Petit écran | À l’accueil, la scène suit la hauteur visible et les commandes respectent les zones sûres. Dans l’atelier, la commande de jeu et le journal se lisent sous la carte, dans une colonne. |

[Spécification de la galaxie](documents_design/cemantix_galaxy/galaxie-semantique-spec-ui-ux.md)

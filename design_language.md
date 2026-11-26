# Langage visuel · Galaxie sémantique

L’accueil s’ouvre sur le dictionnaire. La scène 3D couvre la fenêtre bord à bord. Le logo et le titre Cémantix occupent le coin supérieur gauche. La recherche, le zoom, le retour à la vue globale et l’aide de navigation se superposent à la scène.

Dans l’atelier de résolution, la carte, la proposition du solveur et le journal forment trois niveaux de lecture dans cet ordre. Les diagnostics et paramètres de session s’ouvrent à la demande.

| Élément | Règle |
| --- | --- |
| Surface et texte | Fond graphite `#0a0c0f`, scène presque noire, texte principal `#f2f1ed`, secondaire `#a5acb2`. Les filets séparent les fonctions. |
| Action principale | Ambre `#f5b86d` pour jouer un essai, signaler le suivi et repérer le focus clavier. |
| Navigation principale | Capsule graphite translucide centrée en bas dans les trois vues, pictogrammes au trait et libellés visibles. En déplacement, la lentille de verre se soulève, s’étire et grossit les pictogrammes et les libellés à son passage. Elle suit le pointeur pendant un glissement et reprend la forme d’une capsule à l’arrivée. Le pictogramme et le libellé de la vue active passent à l’ambre. La réduction du mouvement place la lentille directement. La réduction de transparence donne des fonds opaques à la capsule et à la lentille. Sur petit écran, les commandes de la carte d’accueil passent au-dessus. |
| En-tête de jeu | Le contexte se lit sous le titre Cémantix, aligné sur le texte du nom. La grille du jour affiche son numéro officiel au format « n°1730 ». L’atelier affiche « Partie Locale ». |
| Typographie | Sans empattement pour la navigation et le mot proposé. Chasse fixe pour les libellés de carte, relevés et mesures. Piles de polices locales définies dans `interface/style.css`. |
| Dictionnaire | Une particule ronde et ombrée par mot. La taille apparente augmente au premier plan avec un plafond progressif. La couleur identifie le groupe de vecteurs. Les arcs fins suivent la scène 3D jusque sur les bords de la vue. Le zoom révèle davantage de liens locaux. |
| Repères | En vue globale, les champs lexicaux s’affichent au voisinage du centre de leur groupe. La case « Champs lexicaux », près du zoom, masque ou affiche leurs titres. Au survol, le filet du titre, le cœur des points et leur halo reprennent la couleur du groupe. Les autres points passent en gris neutre en conservant leur opacité et leur relief. Les mots apparaissent en vue rapprochée. |
| Résultats | Sur une grille réelle, dès qu’un essai est localisable, les mots non testés et leurs arcs passent au second plan. Les arcs pointillés suivent l’ordre des essais. Un contour signale un essai, une étoile repère le meilleur et une coche indique la victoire. |
| Mouvement | Une caméra continue entre trois échelles. Une manipulation suspend le suivi. La préférence système de réduction du mouvement applique la pose directement. |
| Petit écran | À l’accueil, la scène suit la hauteur visible et les commandes respectent les zones sûres. Dans l’atelier, la commande de jeu et le journal se lisent sous la carte, dans une colonne. |

[Spécification de la galaxie](documents_design/cemantix_galaxy/galaxie-semantique-spec-ui-ux.md)

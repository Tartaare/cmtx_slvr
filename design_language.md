# Interface de l’atelier Cémantix

L’écran de résolution suit l’ordre des décisions du joueur. Le mot recommandé et le budget restant occupent le premier plan. La trajectoire et le classement expliquent ce choix. Le journal conserve le détail de chaque essai.

Les couleurs de référence sont définies dans `interface/style.css`. Le vert profond `--dark` porte la proposition courante, l’abricot `--heat` désigne l’action principale et le fond `--paper` sépare les zones de lecture. Les titres et les mots proposés utilisent Georgia. Les contrôles et les données utilisent une police sans empattement disponible localement. Les valeurs numériques sont alignées dans les colonnes.

Le libellé accompagne chaque état et chaque changement de stratégie. Les graphiques ont une description accessible et leurs valeurs restent consultables dans le tableau de bord. Les contrôles utilisent les éléments natifs du navigateur, un focus visible et un retour de chargement. Sur petit écran, la trajectoire puis les candidats passent sur une seule colonne. Le journal défile horizontalement dans sa propre section.

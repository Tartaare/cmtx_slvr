# Avancement

## Sprint 1 — Essayer un mot

US-001 est livrée. La commande accepte un mot, soumet le formulaire de la grille active et journalise le numéro de grille, le mot, sa température et sa progression. Elle relaie le message du jeu lorsqu’il refuse le mot.

Sur la grille nº 1729, le formulaire a affiché 4,52 °C pour « rivière » et a rejeté « zzzzzzzz ». Les appels HTTP directs avaient attribué 100 °C aux deux essais « maison » et « zzzzzzzz ». Le client utilise donc le résultat affiché par le jeu et vérifie que la ligne correspond au mot soumis.

Le test de régression reproduit l’activation différée du bouton Envoyer et l’ouverture des règles à l’initialisation du jeu. Il couvre un score classé, une température négative sans progression et un refus. La vérification TypeScript et les deux tests passent.

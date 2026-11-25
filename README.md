# Cémantix en ligne de commande

Soumettez un mot à la grille du jour de [Cémantix](https://cemantix.certitudes.org/) et lisez son score dans le terminal.

## Jouer

Installez Node.js 22.16 ou supérieur et disposez de Microsoft Edge sous Windows ou de Google Chrome sous macOS et Linux. Depuis le dossier du projet, installez les dépendances une fois avec `npm ci`, puis lancez un essai.

```sh
npm start -- rivière
```

Résultat observé sur la grille nº 1729 :

```text
Grille n°1729 · rivière · 4,52 °C · hors classement
```

La commande ouvre le site dans un navigateur en arrière-plan, soumet le mot et lit le résultat affiché. La dernière colonne indique la progression en ‰ lorsque le jeu classe le mot. Chaque lancement utilise une session temporaire indépendante.

Un mot refusé ou un site inaccessible produit un message sur la sortie d’erreur et un code de sortie de 1. Un essai réussi renvoie 0.

Pour utiliser une autre installation de Chromium, définissez la variable d’environnement `CEMANTIX_BROWSER` avec le chemin complet de son exécutable.

## Vérifier le projet

- `npm run build` vérifie les types en mode strict. Node exécute directement les fichiers TypeScript.
- `npm test` vérifie la saisie et le parcours du formulaire dans un navigateur local, hors ligne.

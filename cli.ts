import { errors } from "playwright-core";
import { observer, resoudreJour } from "./jour.ts";
import { essayerMot, lireMot, ouvrirNavigateur } from "./jeu.ts";

async function jouer(): Promise<void> {
  const args = process.argv.slice(2);
  const automatique = args[0] === "--resoudre";
  if (automatique && args.length > 2) throw new Error("Usage : npm start -- --resoudre [budget]");
  const releve = args[0] === "--observation";
  const numero = args[0] === "--grille";
  const avecExpiration = numero && args[1] === "--expiration";
  const mot = automatique || numero ? "" : lireMot(releve ? args.slice(2) : args);
  const navigateur = await ouvrirNavigateur();
  try {
    const page = await navigateur.newPage({ locale: "fr-FR", timezoneId: avecExpiration ? "Europe/Paris" : undefined });
    page.setDefaultTimeout(20_000);
    const instant = Date.now();
    const accueil = await page.goto("https://cemantix.certitudes.org/", { waitUntil: "domcontentloaded" });
    if (!accueil?.ok()) throw new Error(`Site indisponible (HTTP ${accueil?.status() ?? "inconnu"}).`);
    if (avecExpiration) {
      const grille = await page.locator("#script").evaluate((script, debut) => {
        const publication = new Date(debut);
        publication.setHours(24, 0, 0, 0);
        return {grille: script.getAttribute("data-puzzle-number"), expiration: publication.getTime() / 1000};
      }, instant);
      console.log(JSON.stringify(grille));
      return;
    }
    if (numero || releve) {
      console.log(JSON.stringify(numero ? await page.locator("#script").getAttribute("data-puzzle-number")
        : await observer(page, args[1], mot)));
      return;
    }
    if (automatique) {
      process.exitCode = await resoudreJour(page, Number(args[1] ?? 20));
      return;
    }
    const score = await essayerMot(page, mot);
    const temperature = score.temperature.toLocaleString("fr-FR", {
      minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
    const progression = score.progression === null ? "hors classement" : `${score.progression} ‰`;
    console.log(`Grille n°${score.grille} · ${score.mot} · ${temperature} °C · ${progression}`);
  } finally {
    await navigateur.close();
  }
}

jouer().catch((erreur: unknown) => {
  const message = erreur instanceof errors.TimeoutError
    ? "Délai dépassé en attendant le jeu ou son résultat."
    : erreur instanceof Error ? erreur.message : String(erreur);
  console.error(`Erreur · ${message}`);
  process.exitCode = 1;
});

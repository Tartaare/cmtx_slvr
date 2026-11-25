import { errors } from "playwright-core";
import { essayerMot, lireMot, ouvrirNavigateur } from "./jeu.ts";

async function jouer(): Promise<void> {
  const mot = lireMot(process.argv.slice(2));
  const navigateur = await ouvrirNavigateur();
  try {
    const page = await navigateur.newPage({ locale: "fr-FR" });
    page.setDefaultTimeout(20_000);
    const accueil = await page.goto("https://cemantix.certitudes.org/", { waitUntil: "domcontentloaded" });
    if (!accueil?.ok()) throw new Error(`Site indisponible (HTTP ${accueil?.status() ?? "inconnu"}).`);
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

import { chromium, type Browser, type Page } from "playwright-core";

export function ouvrirNavigateur(): Promise<Browser> {
  const executablePath = process.env.CEMANTIX_BROWSER;
  return chromium.launch(executablePath
    ? { executablePath }
    : { channel: process.platform === "win32" ? "msedge" : "chrome" });
}

export function lireMot(argumentsCli: string[]): string {
  const mot = argumentsCli[0]?.trim().normalize("NFC").toLocaleLowerCase("fr");
  if (argumentsCli.length !== 1 || !mot || !/^\p{L}[\p{L}\p{M}]*(?:[-'’]\p{L}[\p{L}\p{M}]*)*$/u.test(mot)) {
    throw new Error("Indiquez un seul mot. Exemple : npm start -- rivière");
  }
  return mot;
}

export interface Score {
  mot: string;
  grille: string;
  temperature: number;
  progression: number | null;
}

export async function essayerMot(page: Page, mot: string): Promise<Score> {
  const grille = await page.locator("#script").getAttribute("data-puzzle-number");
  if (!grille || !/^\d+$/.test(grille)) throw new Error("Numéro de grille illisible.");

  const bandeau = page.locator(".fc-consent-root").getByRole("button", { name: /^(fermer|close)$/i });
  await page.addLocatorHandler(bandeau, () => bandeau.click());
  await page.locator("#guess").fill(mot);
  const envoyer = page.locator("#guess-btn:enabled");
  await envoyer.waitFor();
  const fermer = page.locator("#dialog-close");
  if (await fermer.isVisible()) await fermer.click();
  await envoyer.click();

  const reponse = await page.waitForFunction((motAttendu: string) => {
    const erreur = document.querySelector("#error")?.textContent?.trim();
    if (erreur) return { erreur };
    const cellules = document.querySelectorAll("#guessed td");
    if (cellules[1]?.textContent?.trim().normalize("NFC") !== motAttendu) return null;
    const temperature = cellules[2]?.textContent?.trim();
    if (!temperature || cellules.length < 5) return null;
    return { temperature, progression: cellules[4].textContent?.trim() ?? "" };
  }, mot);
  const brut = await reponse.jsonValue();
  if (!brut) throw new Error("La grille n’a fourni aucun résultat.");
  if ("erreur" in brut) throw new Error(`Cémantix · ${mot} · ${brut.erreur}`);

  const valeur = brut.temperature.replace("−", "-").replace(",", ".");
  const temperature = Number(valeur);
  const progression = brut.progression ? Number(brut.progression) : null;
  if (!/^-?\d+(?:\.\d+)?$/.test(valeur) || Math.abs(temperature) > 100 ||
      (progression !== null && (!/^\d+$/.test(brut.progression) || progression < 1 || progression > 1000))) {
    throw new Error(`Score illisible pour « ${mot} » sur la grille ${grille}.`);
  }
  return { mot, grille, temperature, progression };
}

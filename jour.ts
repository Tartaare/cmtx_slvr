import type { Page } from "playwright-core";
import type { Observation, Partie } from "./interface/rendu.ts";
import { essayerMot, MotRefuse } from "./jeu.ts";

async function publier(chemin: string, donnees: object): Promise<Partie> {
  let reponse: Response;
  try {
    reponse = await fetch("http://127.0.0.1:8765/api/parties" + chemin, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(donnees),
    });
  } catch (cause) {
    throw new Error("Atelier inaccessible. Lancez python -m solveur application.", { cause });
  }
  const partie = await reponse.json();
  if (!reponse.ok) throw new Error(partie.erreur || `Atelier indisponible (HTTP ${reponse.status}).`);
  return partie;
}

export async function resoudreJour(page: Page, budget: number): Promise<number> {
  if (!Number.isInteger(budget) || budget < 1 || budget > 200) throw new Error("Budget attendu entre 1 et 200.");
  const numero = () => page.locator("#script").getAttribute("data-puzzle-number");
  const grille = await numero();
  if (!grille || !/^\d+$/.test(grille)) throw new Error("Grille illisible.");
  let partie = await publier("", { config: { source: "assiste", grille, budget } });
  while (partie.statut === "active" && partie.essais.length < budget) {
    const mot = partie.prochain;
    if (!mot) throw new Error("Le moteur ne propose plus de mot.");
    if (partie.essais.length) await page.reload({ waitUntil: "domcontentloaded" });
    if (await numero() !== grille) throw new Error("La grille a changé pendant la résolution.");
    let observation: Observation;
    try {
      const score = await essayerMot(page, mot);
      const victoire = score.progression === 1000 && score.temperature === 100;
      observation = { mot, temperature: score.temperature, statut: victoire ? "victoire" : "score" };
    } catch (erreur) {
      if (!(erreur instanceof MotRefuse)) throw erreur;
      observation = { mot, statut: "refus", temperature: null };
    }
    console.log(`Grille ${grille} · essai ${partie.essais.length + 1}/${budget} · ${mot} · ${observation.temperature === null ? "refus" : observation.temperature + " °C"}`);
    partie = await publier("/" + partie.id, { revision: partie.revision, action: "essai", observations: [observation] });
  }
  console.log(partie.statut === "resolu" ? "Solution confirmée." : `Fin de partie · ${partie.statut}`);
  return partie.statut === "resolu" ? 0 : 2;
}

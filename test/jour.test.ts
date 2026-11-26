import assert from "node:assert/strict";
import test from "node:test";
import { ouvrirNavigateur } from "../jeu.ts";
import { resoudreJour } from "../jour.ts";

test("la résolution enchaîne les recommandations et exige le rang gagnant", async t => {
  const navigateur = await ouvrirNavigateur();
  t.after(() => navigateur.close());
  const page = await navigateur.newPage();
  const statuts: string[] = [];
  t.mock.method(globalThis, "fetch", async (_url: string, init: RequestInit) => {
    const corps = JSON.parse(String(init.body));
    if (corps.action) statuts.push(corps.observations[0].statut);
    else assert.deepEqual(corps.config, { source: "assiste", grille: "12", budget: 2 });
    const n = statuts.length;
    return Response.json({ id: "session", revision: n, essais: [...statuts],
      prochain: ["été", "glace", null][n], statut: n === 2 ? "resolu" : "active" });
  });
  await page.route("https://exemple.test/", route => route.fulfill({ contentType: "text/html", body:
    `<meta charset="utf-8"><script id="script" data-puzzle-number="12"></script>
     <input id="guess"><button id="guess-btn">Envoyer</button><table><tr id="guessed"></tr></table>
     <script>document.querySelector("button").onclick = () => {
       const mot = document.querySelector("input").value;
       for (const texte of ["1", mot, "100", "", mot === "été" ? "999" : "1000"])
         document.querySelector("tr").insertCell().textContent = texte;
     };</script>` }));
  await page.goto("https://exemple.test/");
  assert.equal(await resoudreJour(page, 2), 0);
  assert.deepEqual(statuts, ["score", "victoire"]);
});

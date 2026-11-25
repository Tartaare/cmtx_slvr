import assert from "node:assert/strict";
import test from "node:test";
import { essayerMot, lireMot, ouvrirNavigateur } from "../jeu.ts";

test("la commande accepte un mot accentué et refuse plusieurs mots", () => {
  assert.equal(lireMot(["  E\u0301té "]), "été");
  for (const args of [[], [""], ["deux mots"], ["deux", "mots"]]) {
    assert.throws(() => lireMot(args), /un seul mot/);
  }
});

test("le formulaire fournit un score classé, un score froid ou un refus", async () => {
  const navigateur = await ouvrirNavigateur();
  try {
    const page = await navigateur.newPage();
    page.setDefaultTimeout(3_000);
    for (const mot of ["été", "glace", "zzzz"]) {
      await page.setContent(`
        <script id="script" data-puzzle-number="12"></script>
        <form><input id="guess"><button id="guess-btn" disabled>Envoyer</button></form>
        <dialog><button id="dialog-close">Fermer les règles</button></dialog>
        <span id="error"></span><table><tbody><tr id="guessed"></tr></tbody></table>
        <script>
          document.querySelector("#guess").oninput = () => setTimeout(() => {
            document.querySelector("dialog").showModal();
            document.querySelector("#guess-btn").disabled = false;
          }, 10);
          document.querySelector("#dialog-close").onclick = () => document.querySelector("dialog").close();
          document.querySelector("form").onsubmit = event => {
            event.preventDefault();
            const mot = document.querySelector("#guess").value;
            if (mot === "zzzz") {
              document.querySelector("#error").textContent = "Mot inconnu";
              return;
            }
            const row = document.querySelector("#guessed");
            for (const texte of ["1", mot, mot === "été" ? "34,12" : "-2.30", "", mot === "été" ? "964" : ""]) {
              row.insertCell().textContent = texte;
            }
          };
        </script>`);
      if (mot === "zzzz") {
        await assert.rejects(essayerMot(page, mot), /Mot inconnu/);
      } else {
        assert.deepEqual(await essayerMot(page, mot), {
          mot, grille: "12", temperature: mot === "été" ? 34.12 : -2.3,
          progression: mot === "été" ? 964 : null,
        });
      }
    }
  } finally {
    await navigateur.close();
  }
});

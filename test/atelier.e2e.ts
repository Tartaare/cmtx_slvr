import assert from "node:assert/strict";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { once } from "node:events";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { createInterface } from "node:readline";
import test from "node:test";
import type { Archive } from "../interface/rendu.ts";
import { ouvrirNavigateur } from "../jeu.ts";

async function demarrer(base: string): Promise<[ChildProcessWithoutNullStreams, string]> {
  const processus = spawn(process.env.CEMANTIX_PYTHON || "python",
    ["-m", "test.serveur_fixture", base],
    { windowsHide: true, env: { ...process.env, PYTHONIOENCODING: "utf-8", OPENBLAS_NUM_THREADS: "1" } });
  let erreurs = "";
  processus.stderr.on("data", (m: Buffer) => { erreurs += m.toString(); });
  const lignes = createInterface({ input: processus.stdout });
  for await (const ligne of lignes) {
    const url = ligne.match(/http:\/\/127\.0\.0\.1:\d+\//)?.[0];
    if (url) return [processus, url];
  }
  throw new Error(erreurs || "Le serveur ne s’est pas lancé.");
}
async function fermer(p: ChildProcessWithoutNullStreams): Promise<void> {
  if (p.exitCode !== null || p.signalCode !== null) return;
  const fin = once(p, "exit"); p.kill(); await fin;
}

test("la partie reprend après redémarrage du serveur et aboutit dans le navigateur", {timeout: 90000}, async () => {
  const dossier = await mkdtemp(join(tmpdir(), "cemantix-s8-"));
  const base = join(dossier, "sessions.sqlite3");
  const navigateur = await ouvrirNavigateur();
  let serveur: ChildProcessWithoutNullStreams | undefined;
  try {
    let url: string;
    [serveur, url] = await demarrer(base);
    const page = await navigateur.newPage();
    const erreurs: Error[] = [];
    page.on("pageerror", e => erreurs.push(e));
    const apiLocale = new URL("api/parties", url).href;
    let lectures = 0;
    await page.route(apiLocale, route => {
      lectures++;
      return route.abort("connectionreset");
    });
    const logoRecu = page.waitForResponse(new URL("logo-cemantix-transparent.png", url).href);
    await page.goto(url);
    const logo = await logoRecu;
    assert.equal(logo.status(), 200);
    assert.equal(logo.headers()["content-type"], "image/png");
    const marque = page.getByRole("link", {name:"Cémantix, accueil"}).locator("img");
    assert.ok(await marque.evaluate((image: HTMLImageElement) => image.naturalWidth > 0));
    await page.getByRole("alert").filter({hasText:"Connexion au moteur local interrompue"}).waitFor();
    assert.equal(lectures, 2);
    await page.unroute(apiLocale);
    await page.route(apiLocale, route => route.abort("connectionreset"), {times:1});
    await page.reload();
    await page.getByRole("heading", {name:"hirsute",exact:true}).or(page.locator("#erreur:visible")).waitFor();
    assert.ok(await page.locator("#erreur").isHidden(), await page.locator("#erreur").textContent() ?? "");
    await page.getByRole("button", {name:"Jouer un essai"}).click();
    await page.getByRole("cell", {name:"hirsute",exact:true}).waitFor();
    const prochain = await page.locator("#mot").innerText();
    const budget = await page.locator("#restants").innerText();
    await fermer(serveur);
    [serveur, url] = await demarrer(base);
    await page.goto(url);
    await page.getByRole("heading", {name:prochain,exact:true}).waitFor();
    assert.equal(await page.locator("#restants").innerText(),budget);
    await page.getByRole("button", {name:"Mode automatique"}).click();
    await page.getByText("Solution confirmée", {exact:true}).first().waitFor();
    assert.equal(await page.locator("#mot").innerText(),"balane");
    await page.setViewportSize({width:375,height:812});
    assert.ok(await page.evaluate(()=>document.body.scrollWidth <= window.innerWidth));
    await page.getByRole("button", {name:"Nouvelle partie"}).click();
    const config = page.locator("#creation");
    await config.locator("[name=source]").selectOption("assiste");
    await config.locator("[name=grille]").fill("contrôle");
    await config.locator("[name=fichier]").setInputFiles({
      name:"scores.jsonl", mimeType:"text/plain", buffer:Buffer.from('{"mot":"hirsute","statut":"score","temperature":70.71}')
    });
    await config.getByRole("button", {name:"Démarrer la partie"}).click();
    await page.getByRole("heading", {name:"chignin-bergeron"}).waitFor();
    assert.equal(await page.locator("#strategie").innerText(),"Inversion étendue");
    await page.getByRole("button", {name:"Saisir le score"}).click();
    await page.locator("#score [name=statut]").selectOption("victoire");
    await page.getByRole("button", {name:"Enregistrer l’essai"}).click();
    await page.getByText("Solution confirmée", {exact:true}).first().waitFor();
    await page.getByRole("button", {name:"Mes parties"}).click();
    await page.locator(".archive").first().waitFor();
    assert.equal(await page.locator(".archive").count(),2);
    await page.getByRole("button", {name:"Nouvelle partie"}).click();
    await config.locator("[name=source]").selectOption("jour");
    await config.locator("[name=budget]").fill("1");
    await config.getByRole("button", {name:"Résoudre la grille du jour"}).click();
    await page.getByText("Grille 1234", {exact:true}).waitFor();
    await page.getByText("Solution confirmée", {exact:true}).first().waitFor();
    assert.equal(await page.locator("#mot").innerText(),"hirsute");
    assert.equal(await page.locator("#restants").innerText(),"0");
    await page.getByRole("button", {name:"Mes parties"}).click();
    const lignes = page.locator(".archive");
    const controle = lignes.filter({hasText:"Grille contrôle"});
    const dialogue = page.getByRole("dialog", {name:"Supprimer cette partie ?"});
    const confirmer = dialogue.getByRole("button", {name:"Supprimer la partie"});
    await controle.getByRole("button", {name:/^Supprimer/}).click();
    assert.equal(await page.evaluate(()=>document.activeElement?.textContent),"Annuler");
    await dialogue.getByRole("button", {name:"Annuler"}).click();
    assert.equal(await lignes.count(),3);
    const endpoint = new URL("api/parties", url).href;
    const archives: Archive[] = await (await page.request.get(endpoint)).json();
    const assiste = archives.find(a=>a.config.grille==="contrôle");
    assert.ok(assiste);
    const urlControle = `${endpoint}/${assiste.id}`;
    const conflit = await page.request.delete(urlControle,{data:{revision:assiste.revision-1}});
    assert.equal(conflit.status(),409);
    await page.route(urlControle, route=>route.fulfill({status:501,contentType:"text/html",body:"<h1>Unsupported method</h1>"}));
    await controle.getByRole("button", {name:/^Supprimer/}).click();
    await confirmer.click();
    await dialogue.getByRole("alert").filter({hasText:"Redémarrez-le, puis réessayez."}).waitFor();
    assert.equal(await lignes.count(),3);
    assert.equal((await page.request.get(urlControle)).status(),200);
    await page.unroute(urlControle);
    await confirmer.click();
    await controle.waitFor({state:"detached"});
    assert.equal((await page.request.get(urlControle)).status(),404);
    await lignes.filter({hasText:"Grille 1234"}).getByRole("button", {name:/^Supprimer/}).click();
    await confirmer.click();
    await page.getByRole("button", {name:"Atelier",exact:true}).click();
    await page.locator("#atelier-vide").waitFor();
    assert.ok(await page.locator("#espace").isHidden());
    await page.getByRole("button", {name:"Mes parties"}).click();
    await lignes.getByRole("button", {name:/^Supprimer/}).click();
    await confirmer.click();
    const vide = page.getByText("Aucune partie enregistrée.");
    await vide.waitFor();
    assert.ok(await page.evaluate(()=>document.body.scrollWidth <= window.innerWidth));
    await page.reload();
    await vide.waitFor();
    await fermer(serveur);
    [serveur, url] = await demarrer(base);
    assert.deepEqual(await (await page.request.get(new URL("api/parties", url).href)).json(),[]);
    assert.deepEqual(erreurs,[]);
  } finally {
    if (serveur) await fermer(serveur);
    await navigateur.close();
    if (dirname(resolve(dossier)) === resolve(tmpdir())) await rm(dossier,{recursive:true});
  }
});

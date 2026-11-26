import assert from "node:assert/strict";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { once } from "node:events";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { createInterface } from "node:readline";
import test from "node:test";
import type { Page } from "playwright-core";
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

async function attendreUniforme(page: Page, nom: string, valeur: number): Promise<void> {
  await page.waitForFunction(({nom,valeur}) => {
    const gl = document.querySelector<HTMLCanvasElement>("#galaxie")?.getContext("webgl");
    const programme = gl?.getParameter(gl.CURRENT_PROGRAM) as WebGLProgram | null | undefined;
    const uniforme = programme && gl?.getUniformLocation(programme, nom);
    return uniforme && gl?.getUniform(programme, uniforme) === valeur;
  }, {nom,valeur});
}

type MesurePixels = {erreur: number; moities: number[]; couleurs: number[][]};
function mesurerPixels(page: Page, zooms: number): Promise<MesurePixels> {
  return page.locator("#galaxie").evaluate((canevas: HTMLCanvasElement, nombre) => new Promise<MesurePixels>(fin => {
    const gl = canevas.getContext("webgl")!;
    const dessiner = gl.drawArrays;
    gl.drawArrays = function (mode, debut, compte) {
      dessiner.call(this, mode, debut, compte);
      if (mode !== gl.POINTS) return;
      gl.drawArrays = dessiner;
      const {width, height} = canevas;
      const pixels = new Uint8Array(width * height * 4);
      gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      const moities = [0, 0];
      const couleurs = [[0,0,0,0],[0,0,0,0]];
      for (let i = 0; i < width * height; i++) {
        const debutPixel = 4 * i, alpha = pixels[debutPixel + 3];
        if (alpha <= 20) continue;
        const moitie = Number(i % width >= width / 2);
        moities[moitie]++;
        if (alpha > couleurs[moitie][3]) couleurs[moitie] = Array.from(pixels.subarray(debutPixel,debutPixel+4));
      }
      fin({erreur: gl.getError(), moities, couleurs});
    };
    if (nombre === 0) canevas.dispatchEvent(new KeyboardEvent("keydown", {key: "Home"}));
    for (let i = 0; i < nombre; i++) canevas.dispatchEvent(new KeyboardEvent("keydown", {key: "+"}));
  }), zooms);
}

type Libelle = {texte: string; x: number; y: number};
function lireLibelles(page: Page, touche: string): Promise<Libelle[]> {
  return page.evaluate(cle => new Promise<Libelle[]>(fin => {
    const canvas = document.querySelector<HTMLCanvasElement>("#galaxie")!;
    const ctx = document.querySelector<HTMLCanvasElement>("#annotations")!.getContext("2d")!;
    const dessiner = ctx.fillText, libelles: Libelle[] = [];
    ctx.fillText = function (texte, x, y) {
      libelles.push({texte,x,y});
      dessiner.call(this, texte, x, y);
    };
    canvas.dispatchEvent(new KeyboardEvent("keydown", {key: cle}));
    requestAnimationFrame(() => { ctx.fillText = dessiner; fin(libelles); });
  }), touche);
}

test("l’accueil affiche la carte sur toute la fenêtre sans ouvrir de partie", {timeout: 90000}, async () => {
  const dossier = await mkdtemp(join(tmpdir(), "cemantix-carte-"));
  const navigateur = await ouvrirNavigateur();
  let serveur: ChildProcessWithoutNullStreams | undefined;
  try {
    let url: string;
    [serveur, url] = await demarrer(join(dossier, "sessions.sqlite3"));
    const page = await navigateur.newPage({viewport: {width: 1440, height: 900}, reducedMotion: "reduce"});
    const appels: string[] = [], erreurs: Error[] = [];
    page.on("request", r => { if (new URL(r.url()).pathname.startsWith("/api/")) appels.push(r.url()); });
    page.on("pageerror", e => erreurs.push(e));
    const atlas = new URL("/atlas.json", url).href;
    await page.route(atlas, route => route.abort());
    await page.goto(url);
    const recharger = page.getByRole("button", {name: "Recharger la carte"});
    await recharger.waitFor();
    await page.unroute(atlas);
    await recharger.click();
    const recherche = page.getByRole("searchbox");
    await recherche.waitFor();
    await attendreUniforme(page, "modeEssais", 0);
    const marque = page.getByRole("heading", {name: "Cémantix", exact: true});
    assert.equal(await page.getByRole("heading").count(), 1);
    assert.ok(await marque.locator("img").evaluate((image: HTMLImageElement) => image.naturalWidth > 0));
    assert.equal(await page.getByRole("button", {name: /nouvelle partie|mes parties|suivi du solveur/i}).count(), 0);
    const canevas = page.locator("#galaxie");
    for (const dimensions of [{width: 1440, height: 900}, {width: 320, height: 640}]) {
      await page.setViewportSize(dimensions);
      assert.deepEqual(await canevas.boundingBox(), {x: 0, y: 0, ...dimensions});
      assert.ok(await page.evaluate(() => document.documentElement.scrollHeight === innerHeight));
      const titre = await marque.boundingBox();
      const champ = await recherche.boundingBox();
      assert.ok(titre && champ && titre.x + titre.width < champ.x);
      const libelles = await lireLibelles(page, "Home");
      const noms = libelles.map(({texte}) => texte);
      assert.ok(noms.length >= (dimensions.width === 320 ? 3 : 8), noms.join(", "));
      assert.ok(noms.every(nom => nom.includes(" ") && /^[A-ZÉ]/u.test(nom)), noms.join(", "));
      if (dimensions.width === 1440) {
        const titreChamp = libelles.find(({texte}) => texte === "Langues et musique");
        assert.ok(titreChamp);
        const survoler = () => page.mouse.move(titreChamp.x + 8, titreChamp.y - 5);
        await survoler();
        await attendreUniforme(page, "champSurvole", 11);
        await page.mouse.move(20, 180);
        await attendreUniforme(page, "champSurvole", -1);
        await survoler();
        await attendreUniforme(page, "champSurvole", 11);
        await canevas.press("+");
        await canevas.press("+");
        await attendreUniforme(page, "champSurvole", -1);
      }
    }
    await page.locator(".aide summary").click();
    await page.getByText("Glissez ou utilisez les flèches", {exact: false}).waitFor();
    await recherche.fill("zzzzzzzzzzzz");
    await recherche.press("Enter");
    await page.locator("#resultats").getByText("Mot absent du dictionnaire réduit").waitFor();
    await recherche.fill("hirsut");
    await page.getByRole("button", {name: "hirsute", exact: true}).waitFor();
    await recherche.press("Enter");
    assert.equal(await recherche.inputValue(), "hirsute");
    assert.deepEqual(erreurs.map(e => e.message), []);
    await page.waitForFunction(() => document.querySelector("#niveau")?.textContent === "Vue immersive", undefined, {timeout: 5000});
    const mots = (await lireLibelles(page, "ArrowRight")).map(({texte}) => texte);
    assert.ok(mots.includes("hirsute") && mots.every(mot => !mot.includes(" ")), mots.join(", "));
    await page.getByRole("button", {name: "Dézoomer", exact: true}).click();
    await page.waitForFunction(() => document.querySelector("#niveau")?.textContent === "Vue régionale", undefined, {timeout: 5000});
    await page.getByRole("button", {name: "Zoomer", exact: true}).click();
    await page.waitForFunction(() => document.querySelector("#niveau")?.textContent === "Vue immersive", undefined, {timeout: 5000});
    await page.getByRole("button", {name: "Revenir à la vue globale"}).click();
    await page.waitForFunction(() => document.querySelector("#niveau")?.textContent === "Vue globale");
    assert.deepEqual(appels, []);

    // À ce zoom, les deux mots sont hors champ et seul le milieu de leur arc est visible.
    await page.setViewportSize({width: 800, height: 600});
    const entete = {format: 1, modele: "contrôle", dimensions: 3, methode: "contrôle", reperes: [0, 1]};
    await page.route(atlas, route => route.fulfill({json: {...entete,
      mots: [["ouest", -9000, 0, 0, 0], ["est", 9000, 0, 0, 0]], voisins: [[1], [0]]
    }}), {times: 1});
    await page.reload();
    await recherche.waitFor();
    const {erreur: erreurArc, moities: [gauche, droite]} = await mesurerPixels(page, 7);
    assert.equal(erreurArc, 0);
    assert.ok(gauche > 200 && droite > 200, `Arc au zoom : ${gauche}/${droite} pixels`);

    // Deux mots de même couleur occupent des surfaces distinctes selon leur profondeur.
    await page.route(atlas, route => route.fulfill({json: {...entete,
      mots: [["proche", 45, 0, 1700, 0], ["lointain", 800, 0, -1350, 0]]
    }}), {times: 1});
    await page.reload();
    await recherche.waitFor();
    const {erreur: erreurPoints, moities: [proche, lointain]} = await mesurerPixels(page, 8);
    assert.equal(erreurPoints, 0);
    assert.ok(lointain > 0 && proche > 3 * lointain, `Points proche/lointain : ${proche}/${lointain} pixels`);

    await page.route(atlas, route => route.fulfill({json: {...entete,
      mots: [["sulfone",-6000,0,0,0],["rainurer",6000,0,0,1]]
    }}), {times: 1});
    await page.reload();
    await recherche.waitFor();
    await page.mouse.move(20, 150);
    const normal = await mesurerPixels(page, 0);
    const titre = (await lireLibelles(page, "Home")).find(({texte}) => texte === "Chimie et biochimie");
    assert.ok(titre);
    await page.mouse.move(titre.x + 8, titre.y - 5);
    await attendreUniforme(page, "champSurvole", 0);
    const survol = await mesurerPixels(page, 0);
    assert.equal(survol.erreur, 0);
    const [champ, autre] = survol.couleurs;
    assert.ok(champ[3] > normal.couleurs[0][3] && champ[1] > normal.couleurs[0][1]);
    assert.deepEqual(autre, [autre[0], autre[0], autre[0], normal.couleurs[1][3]]);
    assert.ok(normal.couleurs[1][0] > normal.couleurs[1][2]);
    assert.deepEqual(erreurs, []);
  } finally {
    if (serveur) await fermer(serveur);
    await navigateur.close();
    await rm(dossier, {recursive: true, force: true});
  }
});

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
    const atlas = new URL("atlas.json", url).href;
    await page.route(atlas, route=>route.abort("connectionreset"));
    await page.goto(new URL("/atelier", url).href);
    const logo = await logoRecu;
    assert.equal(logo.status(), 200);
    assert.equal(logo.headers()["content-type"], "image/png");
    const marque = page.getByRole("link", {name:"Cémantix, accueil"}).locator("img");
    assert.ok(await marque.evaluate((image: HTMLImageElement) => image.naturalWidth > 0));
    await page.getByRole("alert").filter({hasText:"Connexion au moteur local interrompue"}).waitFor();
    await page.getByRole("button",{name:"Recharger la carte"}).waitFor();
    await page.unroute(atlas);
    await page.getByRole("button",{name:"Recharger la carte"}).click();
    await page.locator("#suivi:visible").waitFor();
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
    await page.goto(new URL("/atelier", url).href);
    await page.getByRole("heading", {name:prochain,exact:true}).waitFor();
    assert.equal(await page.locator("#restants").innerText(),budget);
    await page.getByRole("button", {name:"Mode automatique"}).click();
    await page.getByText("Solution confirmée", {exact:true}).first().waitFor();
    assert.equal(await page.locator("#mot").innerText(),"balane");
    await attendreUniforme(page, "modeEssais", 0);
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
    await attendreUniforme(page, "modeEssais", 1);
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
    await attendreUniforme(page, "modeEssais", 1);
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

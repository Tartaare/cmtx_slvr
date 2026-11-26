/** Recette locale sur les vrais modèles préparés. Les parties utilisent une base temporaire. */
import assert from "node:assert/strict";
import {spawn} from "node:child_process";
import {once} from "node:events";
import {createInterface} from "node:readline";
import {mkdtemp, readFile, writeFile, rm} from "node:fs/promises";
import {cpus, tmpdir} from "node:os";
import {join} from "node:path";
import type {Browser, Page} from "playwright-core";
import {ouvrirNavigateur} from "../jeu.ts";

const sortie="documents_design/cemantix_galaxy", dossier=await mkdtemp(join(tmpdir(),"galaxie-recette-"));
const base=join(dossier,"parties.sqlite3"), python=process.env.CEMANTIX_PYTHON || "python";
const courte=process.argv.includes("--courte");
const moteur=spawn(python,["-m","solveur","application","--port","0","--base",base],{
  windowsHide:true,env:{...process.env,OPENBLAS_NUM_THREADS:"1",PYTHONIOENCODING:"utf-8"}
});
let diagnostic="";
moteur.stderr.on("data",(b:Buffer)=>{diagnostic=(diagnostic+b.toString()).slice(-2000);});
moteur.on("error",e=>{diagnostic=e.message;});
const lignes=createInterface({input:moteur.stdout});
let navigateur:Browser|undefined;
const mediane=(v:number[])=>[...v].sort((a,b)=>a-b)[Math.floor(v.length/2)];
async function tourner(page:Page,duree:number){
  return page.evaluate(async ms=>{
    const canvas=document.querySelector<HTMLCanvasElement>("#galaxie")!;
    const gl=canvas.getContext("webgl")!, debug=gl.getExtension("WEBGL_debug_renderer_info");
    const pas:number[]=[], memoire:number[]=[];
    const debut=performance.now();
    let precedent=0,prochainReleve=0,premiereMinute:number[]=[];
    await new Promise<void>(fin=>{
      function tour(t:number){
        if(precedent)pas.push(t-precedent);
        if(!premiereMinute.length && t-debut>=60000)premiereMinute=pas.slice();
        precedent=t;
        canvas.dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowRight"}));
        if(t>=prochainReleve){
          const mem=(performance as Performance & {memory?:{usedJSHeapSize:number}}).memory;
          if(mem)memoire.push(Math.round(mem.usedJSHeapSize/1048576));
          prochainReleve=t+60000;
        }
        if(t-debut<ms)requestAnimationFrame(tour);else fin();
      }
      requestAnimationFrame(tour);
    });
    const stats=(v:number[])=>{
      const trie=[...v].sort((a,b)=>a-b);
      return {fps:+(1000*v.length/v.reduce((a,b)=>a+b,0)).toFixed(2),p95_ms:trie[Math.ceil(trie.length*.95)-1]};
    };
    return {duree_ms:Math.round(performance.now()-debut),...stats(pas),premiere_minute:stats(premiereMinute.length?premiereMinute:pas),
      derniere_minute:stats(pas.slice(-Math.max(1,Math.round(pas.length*60000/ms)))),
      gpu:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),
      viewport:[innerWidth,innerHeight],scene:[canvas.width,canvas.height],memoire_Mio:memoire};
  },duree);
}
async function nouvelle(page:Page){
  if (await page.locator("#contenu-jeu").isHidden()) await page.locator("#volet").click();
  await page.locator("#nouvelle").click();
  await page.locator("#creation [name=strategie]").selectOption("plan");
  await page.locator("#creation button[type=submit]").click();
  await page.locator("#parametres").waitFor({state:"hidden"});
}
async function resoudre(page:Page){
  return page.locator("#auto").evaluate(bouton=>new Promise<number>((fin,rejet)=>{
    const debut=performance.now(), statut=document.querySelector("#legende")!;
    const observation=new MutationObserver(()=>{
      if(statut.textContent==="Solution confirmée"){
        observation.disconnect();clearTimeout(delai);fin(Math.round(performance.now()-debut));
      }
    });
    const delai=setTimeout(()=>{observation.disconnect();rejet(new Error("Résolution inachevée"));},30000);
    observation.observe(statut,{childList:true});(bouton as HTMLButtonElement).click();
  }));
}
try{
  navigateur=await ouvrirNavigateur();
  let url="";
  for await(const ligne of lignes){url=ligne.match(/http:\/\/127\.0\.0\.1:\d+\//)?.[0]??"";if(url)break;}
  assert.ok(url,diagnostic || "Adresse du moteur local indisponible");
  url=new URL("/atelier",url).href;
  const page=await navigateur.newPage({viewport:{width:1920,height:1080}});
  const erreurs:string[]=[];page.on("pageerror",e=>erreurs.push(e.message));
  const empreinte=()=>page.evaluate(async()=>{
    const r=await fetch("/atlas.json");
    if(!r.ok)throw new Error("Lecture de l’atlas impossible");
    const digest=await crypto.subtle.digest("SHA-256",await r.arrayBuffer());
    return Array.from(new Uint8Array(digest),n=>n.toString(16).padStart(2,"0")).join("");
  });
  await page.goto(url);
  await page.locator("#suivi:visible").waitFor();
  await page.waitForFunction(()=>document.querySelector("#mot")?.textContent==="hirsute");
  const ouverture=await page.evaluate(()=>Math.round(performance.now()));
  const signature=await empreinte();
  await page.screenshot({path:join(sortie,"vue-globale.png")});
  await page.locator("#plus").click();await page.locator("#plus").click();
  await page.waitForFunction(()=>document.querySelector("#niveau")?.textContent==="Vue régionale");
  await page.waitForTimeout(600);await page.screenshot({path:join(sortie,"vue-regionale.png")});
  await page.locator("#recherche").fill("piano");await page.locator("#recherche").press("Enter");
  await page.waitForFunction(()=>document.querySelector("#niveau")?.textContent==="Vue immersive");
  await page.waitForTimeout(600);await page.screenshot({path:join(sortie,"vue-immersive.png")});
  assert.equal(await page.locator("#suivi").getAttribute("aria-pressed"),"false");
  await page.locator("#essai").click();await page.locator("#volet").click();
  await page.locator("#recents tr").first().waitFor();
  assert.equal(await page.locator("#etat-carte").innerText(),"piano");
  await page.locator("#suivi").click();assert.equal(await page.locator("#etat-carte").innerText(),"hirsute");
  await resoudre(page);assert.equal(await page.locator("#mot").innerText(),"balane");
  await page.reload();await page.locator("#suivi:visible").waitFor();
  assert.equal(await empreinte(),signature);
  assert.equal(await page.locator("#recents tr").count(),3);
  const sans=await navigateur.newPage({viewport:{width:1920,height:1080},reducedMotion:"reduce"});
  await sans.addInitScript(()=>{
    const obtenir=HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,type:string,...args:unknown[]){
      return type==="webgl"?null:Reflect.apply(obtenir,this,[type,...args]);
    } as typeof obtenir;
  });
  await sans.goto(url);await sans.locator("#repli:visible").waitFor();
  const avec3d:number[]=[],sans3d:number[]=[];
  for(let i=0;i<5;i++){
    for(const p of i%2?[sans,page]:[page,sans]){
      await nouvelle(p);(p===page?avec3d:sans3d).push(await resoudre(p));
    }
  }
  await sans.close();
  const debit={avec3d_ms:avec3d,sans3d_ms:sans3d,ecart_median_pct:+(100*(mediane(avec3d)/mediane(sans3d)-1)).toFixed(2)};
  const historiques=JSON.parse(await readFile("benchmarks/calibration/parties.json","utf8")) as {
    grille:string;secret:string;observations:[string,number][]}[];
  const jeu=historiques[0];
  const observations=jeu.observations.map(([mot,temperature])=>({mot,temperature,statut:"score"}));
  await page.locator("#nouvelle").click();
  await page.locator("#creation [name=source]").selectOption("assiste");
  await page.locator("#creation [name=grille]").fill(jeu.grille);
  await page.locator("#creation [name=fichier]").setInputFiles({name:"grille.jsonl",mimeType:"text/plain",
    buffer:Buffer.from(observations.map(o=>JSON.stringify(o)).join("\n"))});
  await page.locator("#creation button[type=submit]").click();
  await page.locator("#parametres").waitFor({state:"hidden"});
  assert.deepEqual(await page.locator("#recents td:nth-child(2)").allTextContents(),observations.map(o=>o.mot).reverse());
  assert.equal(await page.locator("#etat-carte").innerText(),observations.at(-1)!.mot);
  assert.match(await page.locator("#meilleur").innerText(),/merveilleux/);
  assert.match(await page.locator("#recents tr").last().innerText(),/-0,92 °C/);
  await page.locator("#essai").click();
  await page.locator("#score [name=mot]").fill(jeu.secret);
  await page.locator("#score [name=statut]").selectOption("victoire");
  await page.locator("#score button:not([type=button])").click();
  await page.locator("#saisie").waitFor({state:"hidden"});
  assert.equal(await page.locator("#mot").innerText(),jeu.secret);
  assert.equal(await page.locator("#recents tr").count(),observations.length+1);
  console.log("Synchronisation vérifiée. Mesure du bureau.",debit);
  await nouvelle(page);await page.locator("#globale").click();
  const mesures=tourner(page,courte?60000:900000);
  // Le mouvement de la caméra continue pendant quinze résolutions de la même simulation.
  const repetitions=courte?1:15;
  for(let i=0;i<repetitions;i++){
    if(i)await nouvelle(page);
    await resoudre(page);
    if(i+1<repetitions)await page.waitForTimeout(58000);
  }
  const bureau=await mesures;
  const telephone=await navigateur.newPage({viewport:{width:375,height:812},isMobile:true,
    hasTouch:true,deviceScaleFactor:2,reducedMotion:"reduce"});
  const cdp=await telephone.context().newCDPSession(telephone);
  await cdp.send("Emulation.setCPUThrottlingRate",{rate:4});
  await telephone.goto(url);await telephone.locator("#suivi:visible").waitFor();
  await nouvelle(telephone);await telephone.locator("#globale").click();
  const mobile=await Promise.all([tourner(telephone,60000),resoudre(telephone)]).then(r=>r[0]);
  assert.ok(await telephone.evaluate(()=>document.body.scrollWidth<=innerWidth));
  assert.deepEqual(erreurs,[]);
  const chargement=await page.evaluate(()=>performance.getEntriesByType("resource").filter(r=>r.name.endsWith("atlas.json")).map(r=>Math.round(r.duration)));
  const rapport={cpu:cpus()[0].model,navigateur:navigateur.version(),mots:55402,atlas_sha256:signature,
    ouverture_atelier_ms:ouverture,chargement_atlas_ms:chargement,debit,bureau,mobile};
  await writeFile(join(sortie,courte?"mesures-controle.json":"mesures.json"),JSON.stringify(rapport,null,2)+"\n");
  console.log(JSON.stringify(rapport));
}finally{
  await navigateur?.close();
  if(moteur.pid && moteur.exitCode===null && moteur.signalCode===null){const fin=once(moteur,"exit");moteur.kill();await fin;}
  await rm(dossier,{recursive:true,force:true});
}

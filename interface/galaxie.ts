import {el, texte} from "./rendu.js";
import type {Partie} from "./rendu.js";
import {cleMot as cle, indexer} from "./projection.js";
import type {Atlas, Carte} from "./projection.js";
import {Scene} from "./scene.js";

let carte: Carte | undefined, scene: Scene | undefined, partie: Partie | undefined;
let suivi=true, selection="", enCours="", focal="";
const canvas=el<HTMLCanvasElement>("galaxie"), recherche=el<HTMLInputElement>("recherche");
const statut=(valeur:string)=>texte("etat-carte",valeur);
function mode(actif:boolean): void {
  suivi=actif;
  el("suivi").setAttribute("aria-pressed",String(actif));
  texte("libelle-suivi",actif?"Suivi du solveur":"Reprendre le suivi");
}
function centrer(mot:string,distance:number): void {
  const i=carte?.index.get(cle(mot));
  if(i===undefined || !scene) return;
  selection=mot;scene.selection(i,distance);
  statut(mot);
}
function synchroniser(force=false): void {
  if(!partie || !scene || !carte)return;
  const mot=enCours || partie.essais.at(-1)?.observation.mot || (force?partie.prochain:"") || "";
  if(suivi && mot && (force || focal!==mot)){
    if(carte.index.has(cle(mot)))centrer(mot,.32);
    else {selection="";scene.deselectionner();statut(mot+" · hors de la carte réduite");}
  }
  focal=mot;
}
function journal():void {
  scene?.journal(partie?.essais.map(e=>e.observation)??[]);
  if(!carte)return;
  for(const ligne of el("recents").querySelectorAll<HTMLTableRowElement>("tr")){
    const cellule=ligne.cells[1], mot=cellule.firstChild?.textContent;
    if(mot && !carte.index.has(cle(mot)) && !cellule.querySelector("small")){
      const note=document.createElement("small");note.textContent=" · hors carte";cellule.append(note);
    }
  }
}
export function effacerPartie():void {
  partie=undefined;mode(true);selection="";focal="";enCours="";
  recherche.value="";el("resultats").replaceChildren();scene?.nouvellePartie();
  if(scene)statut("Dictionnaire complet");
}
export function actualiserGalaxie(s:Partie,vueInitiale=false):void {
  if(partie?.id!==s.id)effacerPartie();
  if(vueInitiale && s.essais.length)mode(false);
  partie=s;enCours="";journal();synchroniser();
}
export function essaiEnCours(mot:string):void { enCours=mot;synchroniser(); }
export function annulerFoyer():void {
  enCours="";
  if(!partie?.essais.length && suivi){scene?.nouvellePartie();selection="";statut("Dictionnaire complet");}
  synchroniser();
}
function explorer(mot:string):void {
  mode(false);centrer(mot,.32);el("resultats").replaceChildren();recherche.value=mot;
}
const form=el<HTMLFormElement>("chercher");
function propositions():string[] {
  const saisie=cle(recherche.value);
  if(!saisie || !carte)return [];
  const mots:string[]=[];
  for(const mot of carte.index.keys()){
    if(mot.startsWith(saisie))mots.push(mot);
    if(mots.length===6)break;
  }
  return mots;
}
recherche.oninput=()=>{
  const liste=el("resultats");liste.replaceChildren();
  for(const mot of propositions()){
    const b=document.createElement("button");b.type="button";b.textContent=mot;
    b.onclick=()=>explorer(mot);liste.append(b);
  }
};
form.onsubmit=e=>{
  e.preventDefault();
  const essai=cle(recherche.value), mot=carte?.index.has(essai)?essai:propositions()[0];
  if(mot)explorer(mot);else statut("Mot absent du dictionnaire réduit");
};
form.onkeydown=e=>{if(e.key==="Escape"){el("resultats").replaceChildren();recherche.focus();}};
form.addEventListener("focusout",e=>{if(!form.contains(e.relatedTarget as Node|null)) el("resultats").replaceChildren();});
el("suivi").onclick=()=>{mode(!suivi);if(suivi)synchroniser(true);};
function globale():void {mode(false);scene?.globale();statut(selection?"Sélection · "+selection:"Dictionnaire complet");}
function zoom(f:number):void {mode(false);scene?.zoom(f);}
el("globale").onclick=globale;el("plus").onclick=()=>zoom(.7);el("moins").onclick=()=>zoom(1/.7);
canvas.onwheel=e=>{e.preventDefault();zoom(Math.exp(Math.max(-1,Math.min(1,e.deltaY*.0018))));};
canvas.onkeydown=e=>{
  const d:Record<string,[number,number]>={ArrowLeft:[-18,0],ArrowRight:[18,0],ArrowUp:[0,-18],ArrowDown:[0,18]};
  if(d[e.key]){mode(false);scene?.orienter(...d[e.key],e.shiftKey);}
  else if(e.key==="+" || e.key==="=")zoom(.75);
  else if(e.key==="-")zoom(1/.75);
  else if(e.key==="Home")globale();else return;
  e.preventDefault();
};
const contacts=new Map<number,[number,number]>();
let depart:[number,number]=[0,0], glisse=false;
canvas.onpointerdown=e=>{
  if(e.button!==0 && e.button!==2)return;
  canvas.setPointerCapture(e.pointerId);contacts.set(e.pointerId,[e.clientX,e.clientY]);
  if(contacts.size===1){depart=[e.clientX,e.clientY];glisse=false;}else glisse=true;
  mode(false);
};
canvas.oncontextmenu=e=>e.preventDefault();
canvas.onpointermove=e=>{
  const p=contacts.get(e.pointerId);if(!p)return;
  const dx=e.clientX-p[0],dy=e.clientY-p[1];
  glisse ||= Math.hypot(e.clientX-depart[0],e.clientY-depart[1])>4;
  if(contacts.size===2){
    const autre=[...contacts.entries()].find(([id])=>id!==e.pointerId)![1];
    const a=Math.hypot(autre[0]-p[0],autre[1]-p[1]),b=Math.hypot(autre[0]-e.clientX,autre[1]-e.clientY);
    if(a>2 && b>2)scene?.zoom(a/b);
    scene?.orienter(dx/2,dy/2,true);
  }else if(glisse)scene?.orienter(dx,dy,e.shiftKey || e.buttons===2);
  contacts.set(e.pointerId,[e.clientX,e.clientY]);
};
canvas.onpointerup=e=>{
  if(!contacts.delete(e.pointerId) || glisse || !scene || !carte)return;
  const r=canvas.getBoundingClientRect(), i=scene.pointer(e.clientX-r.left,e.clientY-r.top);
  if(i>=0)explorer(carte.atlas.mots[i][0]);
};
canvas.onlostpointercapture=e=>contacts.delete(e.pointerId);

function indisponible(message:string):void {
  scene?.arreter();scene=undefined;
  texte("niveau","Vue textuelle");
  el("scene").classList.add("indisponible");texte("diagnostic-carte",message);el("repli").hidden=false;
  el("outils-carte").hidden=true;el("chercher").hidden=true;el("suivi").hidden=true;canvas.tabIndex=-1;
}
function monter():void {
  if(!carte)return;
  scene=new Scene(canvas,el<HTMLCanvasElement>("annotations"),carte,nom=>{
    if(el("niveau").textContent!==nom)texte("niveau",nom);
  });
  el("scene").classList.remove("indisponible");el("repli").hidden=true;
  el("outils-carte").hidden=false;el("chercher").hidden=false;el("suivi").hidden=false;canvas.tabIndex=0;
  statut("Dictionnaire complet");journal();synchroniser(!!partie?.essais.length);
}
canvas.addEventListener("webglcontextlost",e=>{e.preventDefault();indisponible("Rendu 3D interrompu. Le journal reste disponible.");});
canvas.addEventListener("webglcontextrestored",()=>{try{monter();}catch{indisponible("Rendu 3D indisponible. Le journal reste disponible.");}});
export async function ouvrirGalaxie():Promise<void>{
  const lire=async():Promise<Atlas>=>{
    const r=await fetch("/atlas.json",{signal:AbortSignal.timeout(6000)});
    if(!r.ok)throw new Error("Carte locale indisponible.");
    return r.json() as Promise<Atlas>;
  };
  el("retenter-carte").hidden=true;
  try{
    carte=indexer(await lire().catch(lire));
    texte("compte-mots",carte.index.size.toLocaleString("fr-FR"));
    texte("dimensions",carte.atlas.dimensions.toString());
    journal();
  }catch{
    indisponible("Le dictionnaire n’a pas pu être chargé. Le journal reste disponible.");
    statut("Affichage textuel");el("retenter-carte").hidden=false;return;
  }
  try{monter();}catch{indisponible("Rendu 3D indisponible. Vous pouvez jouer et consulter tous les essais ci-dessous.");statut("Affichage textuel");}
}
el("retenter-carte").onclick=()=>{statut("Chargement du dictionnaire…");void ouvrirGalaxie();};

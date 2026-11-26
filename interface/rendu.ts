export interface Config {
  source: "simulation" | "assiste"; modele: string; strategie: string; modele_source: string;
  scenario: string; graine: number; budget: number; grille: string;
}
export interface Observation { mot: string; statut: "score" | "victoire" | "refus"; temperature: number | null }
interface Essai { observation: Observation; prediction: number | null; motif: string | null; phase: string;
  apres: string; nombre: number; entropie: number | null; ms: number; recommande: string }
interface Candidat { mot: string; p: number; rms: number | null; rang_avant?: number | null }
export interface Archive { id: string; config: Config; statut: string; creation: string }
export interface Partie extends Archive { revision: number; prochain: string | null; etendu: boolean; initial_ms: number;
  nombre_initial: number; essais: Essai[]; vue: {phase: string; modele: string; nombre: number; entropie: number | null; candidats: Candidat[]} }
export function el<T extends HTMLElement = HTMLElement>(id: string): T { return document.getElementById(id) as T }
export const texte = (id: string, valeur: string) => { el(id).textContent = valeur };
const fmt = (n: number, max = 2) => n.toLocaleString("fr-FR", {maximumFractionDigits: max});
const phases: Record<string,string> = {exact_principal:"Inversion exacte",exact_alternatif:"Inversion étendue",melange:"Repli probabiliste"};
export const statuts: Record<string,string> = {active:"En cours",pause:"Suspendue",resolu:"Solution confirmée",
  interrompue:"Interrompue",aucun_candidat:"Aucun candidat",budget_epuise:"Budget épuisé"};
export const nom = (p: Archive) => p.config.source === "simulation" ? "Simulation · " + p.config.graine : "Grille " + p.config.grille;
const phase = (s: string) => phases[s] ?? s;
function motif(s: string): string {
  return s.split("+").map(part => ({principal_sans_candidat:"Le modèle réduit a épuisé ses candidats.",
    alternatif_sans_candidat:"Les scores écartent aussi les candidats exacts du modèle étendu.",
    aucun_candidat_exact:"Les températures divergent des prédictions exactes.",
    sonde_absente_du_principal:"Seul le modèle étendu reconnaît la sonde."}[part] ?? part)).join(" ");
}
function cellule(tag: string, contenu: string): HTMLElement {
  const e = document.createElement(tag); e.textContent = contenu; return e;
}
function surface(id: string): [CanvasRenderingContext2D, number, number] | null {
  const c = el<HTMLCanvasElement>(id);
  const w = c.clientWidth, h = c.clientHeight;
  if (!w || !h) return null;
  const ratio = window.devicePixelRatio || 1;
  c.width = Math.round(w * ratio); c.height = Math.round(h * ratio);
  const g = c.getContext("2d"); if (!g) return null;
  g.scale(ratio, ratio); return [g, w, h];
}
export function graphiques(s: Partie): void {
  const dial = surface("jauge");
  if (dial) {
    const [g,w,h] = dial, r = Math.min(w,h)*.42, k = 1 - s.essais.length/s.config.budget;
    g.translate(w/2,h/2);
    for (let i=0;i<60;i++) {
      const a = i*Math.PI/30 - Math.PI/2;
      g.strokeStyle = i/60 < k ? "#ffbf86" : "#4c7365"; g.lineWidth = i%5 ? 1.4 : 3;
      g.beginPath(); g.moveTo(Math.cos(a)*r,Math.sin(a)*r);
      const fin=r*(i%5 ? 1.05 : 1.12); g.lineTo(Math.cos(a)*fin,Math.sin(a)*fin); g.stroke();
    }
    g.strokeStyle="#729686";g.lineWidth=1;g.beginPath();g.arc(0,0,r*.91,0,2*Math.PI);g.stroke();
  }
  const mesure = el<HTMLSelectElement>("mesure").value;
  const ys: Array<number|null> = s.essais.map(e => mesure==="ecart" ?
    (e.prediction!==null && e.observation.temperature!==null ? Math.abs(e.prediction-e.observation.temperature) : null)
    : mesure==="entropie"?e.entropie:mesure==="ms"?e.ms:e.nombre);
  ys.unshift(mesure==="nombre"?s.nombre_initial:mesure==="entropie"?Math.log2(s.nombre_initial):mesure==="ms"?s.initial_ms:null);
  const dernier=ys.at(-1), unite=({nombre:"candidats · échelle logarithmique",entropie:"bits",ecart:"°C · hypothèse précédente",ms:"ms"}[mesure] ?? "");
  texte("valeur",dernier==null?"—":fmt(dernier)); texte("unite",unite); texte("tour","Essai "+s.essais.length);
  const c=el("courbe"); c.setAttribute("aria-label",unite+" par essai. "+ys.map((y,i)=>i+" : "+(y===null?"indisponible":fmt(y))).join(", "));
  const surf=surface("courbe"); if(!surf) return;
  const [g,w,h]=surf;
  const points=ys.map(y=> y===null?null:mesure==="nombre"?Math.log10(1+y):y);
  const max=Math.max(1,...points.filter((v):v is number=>v!==null));
  for(let i=0;i<4;i++){const y=10+i*(h-20)/3;g.strokeStyle="#d5ded4";g.setLineDash([3,4]);g.beginPath();g.moveTo(3,y);g.lineTo(w-3,y);g.stroke()}
  g.setLineDash([]);g.lineWidth=2.5;g.strokeStyle="#257458";g.beginPath();
  let relier=false;
  points.forEach((v,i)=>{if(v===null){relier=false;return}const x=7+i*(w-14)/Math.max(1,points.length-1),y=h-10-v/max*(h-20);
    if(relier)g.lineTo(x,y);else g.moveTo(x,y);relier=true});
  g.stroke();
  points.forEach((v,i)=>{if(v===null)return;const x=7+i*(w-14)/Math.max(1,points.length-1),y=h-10-v/max*(h-20);
    g.fillStyle=i===points.length-1?"#ad5427":"#257458";g.beginPath();g.arc(x,y,4,0,Math.PI*2);g.fill()});
}
export function afficher(s: Partie): void {
  const n=s.essais.length, v=s.vue, dernier=s.essais.at(-1), active=s.statut==="active";
  texte("legende",active?"Proposition du solveur":statuts[s.statut]);
  texte("mot",s.statut==="resolu"?dernier!.observation.mot:s.prochain??statuts[s.statut]);
  const explication = s.statut==="resolu" ? "Le mot a été confirmé en "+n+" essai"+(n>1?"s.":".") :
    s.statut==="budget_epuise"?"Le dernier essai a été consommé. Le journal conserve les hypothèses examinées.":
    s.statut==="aucun_candidat"?"Aucun mot admissible ne reste dans la recherche active. Consultez les scores et le modèle.":
    s.statut==="interrompue"?"La partie est archivée avec ses observations.":s.statut==="pause"?"Reprenez la partie pour jouer le mot proposé.":
    !n ? (s.prochain==="hirsute"?"Ouverture sélectionnée par entropie sur le vocabulaire réduit.":"Ouverture reproductible sur le vocabulaire disponible.") :
    v.phase==="melange"?"Le moteur propose le candidat le plus probable selon les températures reçues.":
    v.nombre===1?"Un seul candidat reste compatible. Jouez-le pour confirmer la solution.":
    s.config.strategie==="robuste" || (s.config.strategie==="secours" && !s.etendu)?"Le moteur tente un mot compatible avec les scores reçus.":
    "Le moteur cherche à départager les candidats compatibles avec les températures reçues.";
  texte("raison",(dernier?.motif?motif(dernier.motif)+" ":"")+explication);
  texte("restants",String(s.config.budget-n));texte("grille",nom(s));texte("modele",v.modele==="original"?"Fauconnier original":"Cemantbot réduit");
  texte("strategie",phase(v.phase));texte("temps",fmt((s.initial_ms+s.essais.reduce((a,e)=>a+e.ms,0))/1000)+" s");
  el("essai").hidden=!active && s.statut!=="pause"; texte("essai",s.statut==="pause"?"Reprendre":s.config.source==="simulation"?"Jouer un essai":"Saisir le score");
  el("auto").hidden=!active || s.config.source!=="simulation";el("pause").hidden=!active;el("interrompre").hidden=!active&&s.statut!=="pause";
  texte("total",fmt(v.nombre)+" au total");
  const liste=el("candidats");liste.replaceChildren();
  v.candidats.forEach((c,i)=>{const item=document.createElement("li"), barre=document.createElement("progress");
    barre.max=1;barre.value=c.p;barre.setAttribute("aria-label","Probabilité estimée de "+c.mot);
    const delta=c.rang_avant==null?(n?"Entrée":""):c.rang_avant===i+1?"":String(c.rang_avant-i-1).replace(/^(\d)/,"+$1");
    const libelle=cellule("b",c.mot);
    if(c.rms!==null)libelle.append(cellule("small","RMS "+fmt(c.rms,3)+" °C"));
    item.append(cellule("small",String(i+1)),libelle,cellule("small",delta),barre,cellule("span",fmt(c.p*100,c.p<.001?4:1)+" %"));
    liste.append(item)});
  const premier=v.candidats[0];texte("egalite",s.statut==="resolu"?"Victoire confirmée par la source.":!premier?"Aucun candidat disponible.":v.phase==="melange"?
    "Classement probabiliste · écart RMS du premier "+(premier.rms===null?"indisponible":fmt(premier.rms)+" °C"):
    "Candidats exacts équiprobables, dans l’ordre du lexique.");
  const journal=el("journal");journal.replaceChildren();
  if(!n){const vide=cellule("p","Le premier mot joué apparaîtra ici.");vide.className="empty";journal.append(vide)}
  else{
    const table=document.createElement("table"), thead=table.createTHead().insertRow();
    for(const label of ["Essai","Mot joué","Observé","Prédit¹","Écart¹","Décision","Calcul"])thead.append(cellule("th",label));
    const body=table.createTBody();
    [...s.essais].reverse().forEach((e,i)=>{const o=e.observation,row=body.insertRow(),score=o.temperature;
      for(const valeur of [String(n-i),o.mot,o.statut==="victoire"?"Victoire":score===null?"Refus":fmt(score)+" °C",
        e.prediction===null?"—":fmt(e.prediction)+" °C",e.prediction===null||score===null?"—":fmt(score-e.prediction)+" °C",
        (e.recommande!==o.mot?"Saisie libre · ":"")+phase(e.phase)+(e.motif?" · "+motif(e.motif):""),fmt(e.ms,0)+" ms"])row.insertCell().textContent=valeur});
    journal.append(table,cellule("small","¹ Prédiction du candidat en tête avant l’essai. L’écart est la température observée moins cette prédiction."))}
  texte("calibration","Calibration sur deux grilles de test · "+(v.modele==="original"?"21":"19")+" températures reproduites au centième sur 21.");
  texte("couverture",s.etendu?"Secours activé · modèle réduit, puis original, puis mélange probabiliste si les scores divergent.":
    s.config.strategie==="plan"?"Plan exact · la recherche s’arrête si les observations éliminent tous les candidats.":
    "Repli probabiliste sur un modèle. Pour étendre le vocabulaire, préparez l’original et démarrez en mode adaptatif sur le réduit.");
  graphiques(s);
}

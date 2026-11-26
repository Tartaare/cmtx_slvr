export interface Config {
  source: "simulation" | "assiste" | "jour"; modele: string; strategie: string; modele_source: string;
  scenario: string; graine: number; budget: number; grille: string;
}
export interface Observation { mot: string; statut: "score" | "victoire" | "refus"; temperature: number | null }
interface Essai { observation: Observation; prediction: number | null; motif: string | null; phase: string; inexploitable: boolean;
  apres: string; nombre: number; entropie: number | null; ms: number; recommande: string }
interface Candidat { mot: string; p: number; rms: number | null; rang_avant?: number | null }
export interface Archive { id: string; config: Config; statut: string; creation: string; revision: number }
export interface Partie extends Archive { prochain: string | null; etendu: boolean; initial_ms: number;
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
  el("essai").hidden=!active && s.statut!=="pause"; texte("essai",s.statut==="pause"?"Reprendre":s.config.source==="assiste"?"Saisir le score":"Jouer un essai");
  el("auto").hidden=!active || s.config.source==="assiste";el("pause").hidden=!active;el("interrompre").hidden=!active&&s.statut!=="pause";
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
  const recents=el("recents");recents.replaceChildren();
  let meilleur: Observation | undefined;
  for (const [i,e] of s.essais.entries()) {
    const o=e.observation, item=document.createElement("tr");
    if(o.temperature!==null && (o.statut==="victoire" || o.temperature>(meilleur?.temperature??-Infinity)))meilleur=o;
    const resultat=o.statut==="victoire"?"Victoire · 100 °C":o.temperature===null?"Refus":fmt(o.temperature)+" °C";
    item.append(cellule("td",String(i+1)),cellule("td",o.mot),cellule("td",resultat));
    recents.prepend(item);
  }
  texte("meilleur",meilleur?meilleur.mot+" · "+fmt(meilleur.temperature!)+" °C":"Aucun score");
  el("historique").hidden=n===0;
  el("aucun-essai").hidden=n>0;
  texte("joues",String(n));
  const jauge=el<HTMLProgressElement>("jauge");jauge.max=s.config.budget;jauge.value=Math.max(0,s.config.budget-n);
  texte("calibration","Calibration sur deux grilles de test · "+(v.modele==="original"?"21":"19")+" températures reproduites au centième sur 21.");
  texte("couverture",s.etendu?"Secours activé · modèle réduit, puis original, puis mélange probabiliste si les scores divergent.":
    s.config.strategie==="plan"?"Plan exact · la recherche s’arrête si les observations éliminent tous les candidats.":
    "Repli probabiliste sur un modèle. Pour étendre le vocabulaire, préparez l’original et démarrez en mode adaptatif sur le réduit.");
}

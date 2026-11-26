import {afficher, el, graphiques, nom, statuts, texte} from "./rendu.js";
import type {Archive, Config, Observation, Partie} from "./rendu.js";

const api = "/api/parties", cleSession = "cemantix-session";
let session: Partie | null = null, occupe = false, automatique = false;
let prochainTour: number | undefined;
const creation = el<HTMLFormElement>("creation"), score = el<HTMLFormElement>("score");
const parametres = el<HTMLDialogElement>("parametres"), saisie = el<HTMLDialogElement>("saisie");

async function requete<T>(url: string, corps?: object): Promise<T> {
  const options = corps ? {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(corps)} : {};
  const r = await fetch(url, options);
  const d = await r.json();
  if (!r.ok) {
    if (r.status === 409 && session) choisir(await requete<Partie>(api+"/"+session.id));
    throw new Error(d.erreur || "Le serveur local est indisponible.");
  }
  return d as T;
}
function verrou(actif: boolean): void {
  occupe = actif; el("espace").setAttribute("aria-busy",String(actif));
  document.body.classList.toggle("busy", actif);
  document.querySelectorAll<HTMLButtonElement>("button").forEach(b => b.disabled = actif && !(automatique && b.id==="auto"));
  texte("auto",automatique?"Arrêter l’automatique":"Mode automatique");
}
async function traiter(travail: () => Promise<void>): Promise<void> {
  if (occupe) return;
  verrou(true); el("erreur").hidden=true;
  document.querySelectorAll(".feedback").forEach(e=>e.textContent="");
  try { await travail(); }
  catch(e) {
    automatique=false;
    const message = e instanceof Error?e.message:String(e);
    const local=document.querySelector("dialog[open] .feedback");
    if(local)local.textContent=message;
    else {texte("erreur",message);el("erreur").hidden=false}
    if(!session){texte("legende","Moteur indisponible");texte("mot","Session indisponible");
      texte("raison","Vérifiez le diagnostic ci-dessus ou démarrez une nouvelle partie avec un modèle préparé.");
      el("essai").hidden=true}
  } finally { verrou(false); }
}
function onglet(archives: boolean): void {
  el("bibliotheque").hidden=!archives;el("espace").hidden=archives;
  for(const id of ["atelier","archives"])el(id).removeAttribute("aria-current");
  el(archives?"archives":"atelier").setAttribute("aria-current","page");
  texte("titre",archives?"Mes parties":"Atelier de résolution");
}
function choisir(s: Partie): void {
  session=s;localStorage.setItem(cleSession,s.id);onglet(false);afficher(s);
  texte("message",nom(s)+" · "+statuts[s.statut]+" · "+s.essais.length+" essais");
  if(s.statut!=="active")automatique=false;
}
async function modifier(action: string, observations?: Observation[]): Promise<void> {
  if(!session)return;
  choisir(await requete<Partie>(api+"/"+session.id,{revision:session.revision,action,observations}));
}
function champ<T extends HTMLInputElement | HTMLSelectElement>(form: HTMLFormElement, name: string): T {
  return form.elements.namedItem(name) as T;
}
function sourceChange(): void {
  const assiste=champ(creation,"source").value==="assiste";
  const source=champ(creation,"source").value;
  for(const e of document.querySelectorAll<HTMLElement>("[data-simulation]"))e.hidden=source!=="simulation";
  creation.querySelector("button[type=submit]")!.textContent=source==="jour"?"Résoudre la grille du jour":"Démarrer la partie";
  document.querySelector<HTMLElement>("[data-assiste]")!.hidden=!assiste;
  champ(creation,"grille").required=assiste;
}
function nouvelle(config?: Config): void {
  window.clearTimeout(prochainTour);automatique=false;creation.reset();
  if(config)for(const [k,v] of Object.entries(config))champ(creation,k).value=String(v);
  sourceChange();parametres.showModal();
}
el("nouvelle").onclick=()=>nouvelle();
el("reset").onclick=()=>nouvelle(session?.config);
champ(creation,"source").onchange=sourceChange;
for(const bouton of document.querySelectorAll<HTMLElement>("[data-close]"))bouton.onclick=()=>bouton.closest("dialog")!.close();
creation.onsubmit=e=>{
  e.preventDefault();
  void traiter(async()=>{
    const f=new FormData(creation);
    const config={source:f.get("source"),modele:f.get("modele"),strategie:f.get("strategie"),
      budget:Number(f.get("budget")),graine:Number(f.get("graine")),modele_source:f.get("modele_source"),
      grille:String(f.get("grille")).trim(),scenario:f.get("scenario")};
    let observations: Observation[]|undefined;
    const fichier=champ<HTMLInputElement>(creation,"fichier").files?.[0];
    if(config.source==="assiste" && fichier){
      if(fichier.size>250000)throw new Error("L’historique dépasse 250 Ko.");
      observations=(await fichier.text()).trim().split(/\r?\n/).map((ligne,i)=>{
        try{return JSON.parse(ligne)}catch{throw new Error("JSON invalide à la ligne "+(i+1)+".")}
      });
    }
    if(config.source==="jour")creation.querySelector(".feedback")!.textContent="Ouverture de la grille du jour…";
    choisir(await requete<Partie>(api,{config,observations}));parametres.close();
    if(config.source==="jour"){
      automatique=true;
      prochainTour=window.setTimeout(()=>void boucle(),0);
    }
  });
};
el("essai").onclick=()=>{
  if(!session)return;
  if(session.statut==="pause"){void traiter(()=>modifier("reprendre"));return}
  if(session.config.source!=="assiste"){void traiter(()=>modifier("essai"));return}
  score.reset();champ(score,"mot").value=session.prochain??"";afficherTemperature();saisie.showModal();
};
function afficherTemperature(): void {
  const visible=champ(score,"statut").value==="score";el("champ-temp").hidden=!visible;
  champ(score,"temperature").required=visible;
}
champ(score,"statut").onchange=afficherTemperature;
score.onsubmit=e=>{
  e.preventDefault();
  void traiter(async()=>{
    const statut=champ(score,"statut").value as Observation["statut"];
    const temperature=statut==="refus"?null:statut==="victoire"?100:Number(champ(score,"temperature").value);
    await modifier("essai",[{mot:champ(score,"mot").value,statut,temperature}]);saisie.close();
  });
};
async function boucle(): Promise<void> {
  if(!automatique || !session || session.statut!=="active")return;
  await traiter(()=>modifier("essai"));
  if(automatique)prochainTour=window.setTimeout(()=>void boucle(),350);
}
el("auto").onclick=()=>{
  window.clearTimeout(prochainTour);
  automatique=!automatique;
  texte("auto",automatique?"Arrêter l’automatique":"Mode automatique");
  if(automatique)void boucle();
};
el("pause").onclick=()=>{automatique=false;void traiter(()=>modifier("pause"))};
el("interrompre").onclick=()=>{
  automatique=false;
  if(confirm("Interrompre cette partie et conserver son journal ?"))void traiter(()=>modifier("interrompre"));
};
el("export").onclick=()=>{
  if(!session)return;
  const blob=new Blob([JSON.stringify(session,null,2)],{type:"application/json"});
  const lien=document.createElement("a");lien.href=URL.createObjectURL(blob);lien.download="cemantix-"+session.id+".json";
  lien.click();setTimeout(()=>URL.revokeObjectURL(lien.href),1000);
};
el("mesure").onchange=()=>{if(session)graphiques(session)};
new ResizeObserver(()=>{if(session&&!el("espace").hidden)graphiques(session)}).observe(el("courbe"));
el("atelier").onclick=()=>{onglet(false);if(session)afficher(session)};
el("archives").onclick=()=>{
  automatique=false;
  void traiter(async()=>{
    const archives=await requete<Archive[]>(api);onglet(true);
    const liste=el("liste");liste.replaceChildren();
    for(const a of archives){
      const ligne=document.createElement("div");ligne.className="archive";
      const label=document.createElement("div");label.textContent=nom(a);
      const info=document.createElement("small");info.textContent=new Date(a.creation).toLocaleString("fr-FR")+" · "+statuts[a.statut];
      const ouvrir=document.createElement("button");ouvrir.textContent="Ouvrir";ouvrir.onclick=()=>void traiter(async()=>choisir(await requete<Partie>(api+"/"+a.id)));
      label.append(info);ligne.append(label,ouvrir);liste.append(ligne);
    }
    if(!archives.length)liste.textContent="Aucune partie enregistrée.";
  });
};
void traiter(async()=>{
  const archives=await requete<Archive[]>(api);
  const id=localStorage.getItem(cleSession), archive=archives.find(a=>a.id===id)??archives[0];
  choisir(archive?await requete<Partie>(api+"/"+archive.id):await requete<Partie>(api,{initial:true}));
});

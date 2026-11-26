type Ressort = {position: number; vitesse: number};
type Geste = {id: number; origine: number; x: number; vitesse: number; instant: number; glisse: boolean};

function avancer(ressort: Ressort, cible: number, raideur: number, amortissement: number, dt: number): void {
  ressort.vitesse += (raideur * (cible - ressort.position) - amortissement * ressort.vitesse) * dt;
  ressort.position += ressort.vitesse * dt;
}

function contour(centre: number, hauteur: number, demiLargeur: number, rx: number, ry: number): string {
  const a = centre - demiLargeur + rx, b = centre + demiLargeur - rx;
  const haut = hauteur / 2 - ry, bas = hauteur / 2 + ry;
  return `M${a} ${haut}H${b}A${rx} ${ry} 0 0 1 ${b} ${bas}H${a}A${rx} ${ry} 0 0 1 ${a} ${haut}Z`;
}

export function animerLentille(dock: HTMLElement): void {
  const rangee = dock.querySelector<HTMLElement>(".dock-options")!;
  const options = [...rangee.querySelectorAll<HTMLInputElement>('input[type="radio"]')];
  const faces = [...rangee.querySelectorAll<HTMLElement>(".dock-face")];
  const reflet = document.createElement("div");
  reflet.className = "dock-reflet";
  reflet.setAttribute("aria-hidden", "true");
  const copie = rangee.cloneNode(true) as HTMLElement;
  copie.querySelectorAll("input").forEach(option => option.remove());
  reflet.append(copie);
  dock.append(reflet);
  const selection = () => options.findIndex(option => option.checked);
  const mouvementReduit = matchMedia("(prefers-reduced-motion: reduce)");
  const position: Ressort = {position: selection(), vitesse: 0};
  const hauteur: Ressort = {position: 0, vitesse: 0};
  let geste: Geste | undefined;
  let animation = 0;
  let precedent = 0;

  const limiter = (rang: number) => Math.max(0, Math.min(options.length - 1, rang));
  function rangDepuis(x: number, projection = 0): number {
    const premier = options[0].getBoundingClientRect();
    const pas = options[1].getBoundingClientRect().left - premier.left;
    return (x + projection - premier.left - premier.width / 2) / pas;
  }

  function poser(): void {
    position.position = selection();
    position.vitesse = hauteur.position = hauteur.vitesse = precedent = 0;
    dock.removeAttribute("data-soulevee");
    dock.removeAttribute("data-survol");
    dock.style.removeProperty("--position");
    dock.style.removeProperty("--largeur-lentille");
    dock.style.removeProperty("--hauteur-lentille");
  }

  function peindre(positionX: number, soulevement: number, etirement: number): void {
    const sx = (1 + .28 * soulevement) * (1 + etirement);
    const sy = (1 + .48 * soulevement) / (1 + .55 * etirement);
    const soulevee = soulevement > .035;
    if (soulevee) {
      // La copie agrandie remplace uniquement les pixels sous la lentille.
      const cadres = faces.map(face => face.getBoundingClientRect());
      const {width: largeur, height: hauteur, left: gauche} = cadres[0];
      const pas = cadres[1].left - gauche;
      const centre = largeur / 2 + positionX * pas;
      const rayon = Math.min(largeur, hauteur) / 2;
      const capsule = (x: number) => contour(x, hauteur, largeur * sx / 2, rayon * sx, rayon * sy);
      dock.style.setProperty("--centre-lentille", `${centre}px`);
      dock.style.setProperty("--clip-lentille", `path("${capsule(centre)}")`);
      dock.style.setProperty("--grossissement", String(1 + .18 * soulevement));
      faces.forEach((face, rang) => {
        const cadre = cadres[rang];
        const rectangle = `M0 0H${cadre.width}V${cadre.height}H0Z`;
        face.style.setProperty("--clip-face", `path(evenodd,"${rectangle}${capsule(centre - (cadre.left - gauche))}")`);
      });
    }
    dock.style.setProperty("--position", String(positionX));
    dock.style.setProperty("--largeur-lentille", String(sx));
    dock.style.setProperty("--hauteur-lentille", String(sy));
    dock.toggleAttribute("data-soulevee", soulevee);
    if (geste || soulevee) dock.dataset.survol = String(geste ? limiter(Math.round(positionX)) : selection());
  }

  function actualiser(instant: number): void {
    animation = 0;
    const rang = geste ? rangDepuis(geste.x) : selection();
    const borne = limiter(rang), depassement = rang - borne;
    const cible = borne + .36 * depassement / (1 + Math.abs(depassement));
    if (mouvementReduit.matches) {
      poser();
      if (geste?.glisse) peindre(borne, 0, 0);
      return;
    }
    const delta = precedent ? Math.min(instant - precedent, 40) / 1000 : 1 / 60;
    precedent = instant;
    const pas = Math.ceil(delta * 120) || 1;
    for (let i = 0; i < pas; i++) {
      const enRoute = Math.abs(position.position - cible) > .09 || Math.abs(position.vitesse) > .95;
      avancer(position, cible, geste ? 560 : 185, geste ? 42 : 24, delta / pas);
      avancer(hauteur, geste || enRoute ? 1 : 0, 240, 27, delta / pas);
    }
    if (!geste && Math.abs(position.position - cible) < .004 && Math.abs(position.vitesse) < .045
        && Math.abs(hauteur.position) < .006 && Math.abs(hauteur.vitesse) < .045) {
      poser();
      return;
    }
    const soulevement = Math.max(0, hauteur.position);
    peindre(position.position, soulevement, Math.min(.18, Math.abs(position.vitesse) * .023));
    const immobile = Math.abs(position.position - cible) < .004 && Math.abs(position.vitesse) < .045
      && Math.abs(hauteur.position - 1) < .006 && Math.abs(hauteur.vitesse) < .045;
    if (geste && immobile) precedent = 0;
    else animer();
  }

  function animer(): void {
    if (!animation) animation = requestAnimationFrame(actualiser);
  }

  dock.dataset.lentille = "";
  dock.addEventListener("change", animer);
  mouvementReduit.addEventListener("change", animer);
  dock.addEventListener("pointerdown", evenement => {
    if (geste || !evenement.isPrimary || evenement.button !== 0 || !(evenement.target instanceof HTMLInputElement)) return;
    geste = {id: evenement.pointerId, origine: evenement.clientX, x: evenement.clientX,
      vitesse: 0, instant: evenement.timeStamp, glisse: false};
    animer();
  });
  window.addEventListener("pointermove", evenement => {
    if (!geste || evenement.pointerId !== geste.id) return;
    const delta = evenement.timeStamp - geste.instant;
    if (delta > 0 && evenement.clientX !== geste.x) {
      geste.vitesse = (evenement.clientX - geste.x) / delta;
      geste.instant = evenement.timeStamp;
    }
    geste.x = evenement.clientX;
    if (!geste.glisse && Math.abs(geste.x - geste.origine) > 6) {
      geste.glisse = true;
      dock.setPointerCapture(geste.id);
    }
    animer();
  });
  function terminer(evenement: PointerEvent): void {
    if (!geste || geste.id !== evenement.pointerId) return;
    const dernier = geste;
    geste = undefined;
    dock.removeAttribute("data-survol");
    if (dernier.glisse && evenement.type === "pointerup") {
      const recent = evenement.timeStamp - dernier.instant < 90;
      const projection = recent ? Math.max(-90, Math.min(90, dernier.vitesse * 120)) : 0;
      const option = options[limiter(Math.round(rangDepuis(evenement.clientX, projection)))];
      option.focus({preventScroll: true});
      option.click();
    }
    animer();
  }
  window.addEventListener("pointerup", terminer);
  window.addEventListener("pointercancel", terminer);
  dock.addEventListener("lostpointercapture", evenement => {
    if (evenement.target === dock) terminer(evenement);
  });
}

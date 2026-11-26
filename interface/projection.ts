export type Point = [number, number, number];
export const cleMot=(mot:string)=>mot.trim().normalize("NFC").toLocaleLowerCase("fr").replaceAll("’","'");
type Ligne = [string, number, number, number, number];
export interface Atlas {
  mots: Ligne[]; reperes: number[]; dimensions: number; methode: string; format: number; modele: string;
  voisins?: number[][];
}

const palette = ["ffb458","f39452","fc7966","f16a91","ea6dad","d884ed","bb8bfa","938cfa",
  "78a9ff","64c2ef","53d8da","65dbc1","95dc9b","b1db81","d6ce6c","e7c078"];

// Chaque nom est associé au mot le plus représentatif du groupe dans l’atlas livré.
const nomsChamps = new Map([
  ["sulfone","Chimie et biochimie"], ["rainurer","Outils et mécanique"],
  ["mésentérique","Médecine et santé"], ["dipolaire","Physique et mesures"],
  ["logiciel","Numérique et médias"], ["anhistorique","Pensée et philosophie"],
  ["toutefois","Droit et procédures"], ["paradoxalement","Société et économie"],
  ["veulerie","Caractère et attitudes"], ["frissonnant","Sensations et paysages"],
  ["séditieux","Pouvoir et conflits"], ["assamais","Langues et musique"],
  ["ah","Langage familier"], ["solier","Métiers et patrimoine"],
  ["nerprun","Plantes et cuisine"], ["fouisseur","Faune et milieux"]
]);

export function indexer(atlas: Atlas) {
  if (atlas.format !== 1 || !atlas.mots.length) throw new Error("Format de carte inconnu.");
  const n = atlas.mots.length;
  if (atlas.voisins !== undefined && (!Array.isArray(atlas.voisins) || atlas.voisins.length !== n ||
    atlas.voisins.some((ligne, i) => !Array.isArray(ligne) || ligne.length !== Math.min(4,n-1) ||
      new Set(ligne).size !== ligne.length ||
      ligne.some(j => !Number.isInteger(j) || j < 0 || j >= n || j === i)))) {
    throw new Error("Liens de projection incohérents.");
  }
  const index = new Map<string, number>(), positions = new Float32Array(atlas.mots.length * 3);
  const couleurs = new Uint8Array(positions.length), groupes = new Uint8Array(n);
  const sommes = new Float64Array(palette.length * 3), effectifs = new Uint32Array(palette.length);
  atlas.mots.forEach(([mot,x,y,z,groupe],i) => {
    if (!mot || index.has(mot) || ![x,y,z].every(Number.isFinite) || !palette[groupe])
      throw new Error("Données de projection incohérentes.");
    index.set(mot,i);
    positions.set([x/10000,y/10000,z/10000],3*i);
    const rgb = parseInt(palette[groupe],16);
    couleurs.set([rgb >> 16, (rgb >> 8) & 255, rgb & 255],3*i);
    groupes[i]=groupe;
    sommes[3*groupe]+=x;sommes[3*groupe+1]+=y;sommes[3*groupe+2]+=z;
    effectifs[groupe]++;
  });
  const centres = Float32Array.from(sommes,(s,i)=>s/(10000*Math.max(1,effectifs[Math.floor(i/3)])));
  const champs = atlas.reperes.flatMap((id,groupe)=>{
    const repere=atlas.mots[id];
    const nom=repere?.[4]===groupe?nomsChamps.get(repere[0]):undefined;
    return nom?[{groupe,nom,couleur:"#"+palette[groupe]}]:[];
  }).sort((a,b)=>effectifs[b.groupe]-effectifs[a.groupe]);
  return {atlas,index,positions,couleurs,groupes,centres,champs};
}
export type Carte = ReturnType<typeof indexer>;

export interface Camera { centre: Point; distance: number; longitude: number; latitude: number }
export const cameraInitiale = (aspect: number): Camera => ({
  centre:[0,0,0], distance:Math.max(2.08,2.35/aspect), longitude:0.09, latitude:-0.08
});

export function axes(c: Camera): [Point,Point,Point] {
  const x = Math.cos(c.longitude), z = Math.sin(c.longitude);
  const y = Math.cos(c.latitude), v = Math.sin(c.latitude);
  return [[x,0,-z],[-z*v,y,-x*v],[z*y,v,x*y]];
}

export function cadre(c: Camera, largeur: number, hauteur: number) {
  const [droite,haut,avant] = axes(c);
  const scalaire = (p: Point) => p.reduce((s,a,i)=>s+a*c.centre[i],0);
  const k = 1.85, aspect = largeur/hauteur;
  const matrice = new Float32Array(16);
  for (let i=0;i<3;i++) {
    matrice[i*4] = droite[i]*k/aspect;
    matrice[i*4+1] = haut[i]*k;
    matrice[i*4+2] = -avant[i]*1.0001;
    matrice[i*4+3] = -avant[i];
  }
  matrice[12] = -scalaire(droite)*k/aspect;
  matrice[13] = -scalaire(haut)*k;
  matrice[15] = c.distance+scalaire(avant);
  matrice[14] = matrice[15]*1.0001-.004;
  return matrice;
}

export function projeter(m: Float32Array, points: Float32Array, i: number, w: number, h: number): Point {
  const x=points[i*3], y=points[i*3+1], z=points[i*3+2];
  const profondeur=m[3]*x+m[7]*y+m[11]*z+m[15];
  return [(1+(m[0]*x+m[4]*y+m[8]*z+m[12])/profondeur)*w/2,
    (1-(m[1]*x+m[5]*y+m[9]*z+m[13])/profondeur)*h/2, profondeur];
}

export type Zone = [x: number, y: number, largeur: number, hauteur: number];
export function placerLibelle([x,y]: Point, largeur: number, hauteur: number, w: number, h: number,
  zones: Zone[], champ: boolean): Zone | undefined {
  if(largeur+10>w || hauteur+10>h)return;
  const positions=champ
    ? [[x-largeur/2,y-hauteur-8],[x-largeur/2,y+8],[x+10,y-hauteur/2],[x-largeur-10,y-hauteur/2]]
    : [[x+9,y-20]];
  for(const [gauche,haut] of positions){
    const a=Math.max(5,Math.min(gauche,w-largeur-5)), b=Math.max(5,Math.min(haut,h-hauteur-5));
    if((b<62 && (a<120 || a+largeur>w-220)) || (b+hauteur>h-52 && (a<155 || a+largeur>w-150)))continue;
    if(zones.some(([c,d,l,k])=>a<c+l+12 && a+largeur+12>c && b<d+k+9 && b+hauteur+9>d))continue;
    return [a,b,largeur,hauteur];
  }
}

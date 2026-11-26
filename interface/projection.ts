export type Point = [number, number, number];
export const cleMot=(mot:string)=>mot.trim().normalize("NFC").toLocaleLowerCase("fr").replaceAll("’","'");
type Ligne = [string, number, number, number, number];
export interface Atlas {
  mots: Ligne[]; reperes: number[]; dimensions: number; methode: string; format: number; modele: string;
}

export function indexer(atlas: Atlas) {
  if (atlas.format !== 1 || !atlas.mots.length) throw new Error("Format de carte inconnu.");
  const index = new Map<string, number>(), positions = new Float32Array(atlas.mots.length * 3);
  const couleurs = new Uint8Array(positions.length);
  const palette = ["ffb458","f39452","fc7966","f16a91","ea6dad","d884ed","bb8bfa","938cfa",
    "78a9ff","64c2ef","53d8da","65dbc1","95dc9b","b1db81","d6ce6c","e7c078"];
  atlas.mots.forEach(([mot,x,y,z,groupe],i) => {
    if (!mot || index.has(mot) || ![x,y,z].every(Number.isFinite) || !palette[groupe])
      throw new Error("Données de projection incohérentes.");
    index.set(mot,i);
    positions.set([x/10000,y/10000,z/10000],3*i);
    const rgb = parseInt(palette[groupe],16);
    couleurs.set([rgb >> 16, (rgb >> 8) & 255, rgb & 255],3*i);
  });
  return {atlas,index,positions,couleurs};
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

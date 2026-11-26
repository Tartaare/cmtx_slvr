import type {Carte, Point} from "./projection.js";

type Lien = [a: number, b: number];
type Bloc = {debut: number; compte: number; min: Point; max: Point; distance: number};
type Plan = [x: number, y: number, z: number, seuil: number];
const SEGMENTS = 6;
const SOMMETS = 2 * SEGMENTS;
const OCTETS = 10;
const cle = (a: number, b: number, n: number) => Math.min(a,b)*n+Math.max(a,b);

function echantillonner(carte: Carte): {globaux: Lien[]; locaux: Lien[][]} {
  const {voisins,mots}=carte.atlas;
  const globaux: Lien[]=[];
  if(!voisins)return {globaux,locaux:[]};
  const n=mots.length, vus=new Set<number>();
  const pas=Math.max(1,Math.ceil(n/960));
  for(let a=0;a<n;a+=pas){
    for(const b of voisins[a].slice(0,2)){
      const id=cle(a,b,n);
      if(vus.has(id))continue;
      vus.add(id);globaux.push([a,b]);
    }
  }
  const cases=new Map<string,Lien[]>();
  for(let a=0;a<n;a++){
    const [,x,y,z]=mots[a];
    for(let rang=0;rang<Math.min(2,voisins[a].length);rang++){
      const b=voisins[a][rang], id=cle(a,b,n);
      if(vus.has(id))continue;
      vus.add(id);
      const [,u,v,w]=mots[b];
      const position=[Math.floor((x+u)/3200),Math.floor((y+v)/3200),Math.floor((z+w)/3200)].join("/");
      const caseLocale=cases.get(position);
      if(caseLocale)caseLocale.push([a,b]);else cases.set(position,[[a,b]]);
    }
  }
  // Une densité bornée par case maintient la lisibilité des amas. L'échantillon couvre toute la case.
  const locaux=Array.from(cases.values(),liens=>Array.from({length:Math.min(64,liens.length)},
    (_,i)=>liens[Math.floor(i*liens.length/Math.min(64,liens.length))]));
  return {globaux,locaux};
}

class Geometrie {
  readonly donnees: Uint8Array<ArrayBuffer>;
  private readonly positions: Int16Array;
  private nombre=0;

  constructor(arcs: number, private readonly carte: Carte) {
    this.donnees=new Uint8Array(arcs*SOMMETS*OCTETS);
    this.positions=new Int16Array(this.donnees.buffer);
  }

  bloc(liens: Lien[], opacite: number): Bloc {
    const debut=this.nombre;
    const min: Point=[Infinity,Infinity,Infinity], max: Point=[-Infinity,-Infinity,-Infinity];
    for(const [a,b] of liens){
      const [,x,y,z]=this.carte.atlas.mots[a], [,u,v,w]=this.carte.atlas.mots[b];
      const dx=u-x,dy=v-y,dz=w-z;
      const horizontal=Math.hypot(dx,dy), longueur=Math.hypot(dx,dy,dz);
      const courbure=(a<b?1:-1)*Math.min(longueur*.38,1900);
      const bx=horizontal>1?-dy/horizontal*courbure:0;
      const by=horizontal>1?dx/horizontal*courbure:courbure;
      const ecrire=(segment: number)=>{
        const t=segment/SEGMENTS, courbe=2*t*(1-t);
        const px=Math.round(x+dx*t+bx*courbe), py=Math.round(y+dy*t+by*courbe), pz=Math.round(z+dz*t);
        min[0]=Math.min(min[0],px);min[1]=Math.min(min[1],py);min[2]=Math.min(min[2],pz);
        max[0]=Math.max(max[0],px);max[1]=Math.max(max[1],py);max[2]=Math.max(max[2],pz);
        const sommet=this.nombre++;
        const position=sommet*(OCTETS/2);
        this.positions[position]=px;this.positions[position+1]=py;this.positions[position+2]=pz;
        const couleurs=this.carte.couleurs;
        for(let i=0;i<3;i++)this.donnees[sommet*OCTETS+6+i]=Math.round(couleurs[3*a+i]*(1-t)+couleurs[3*b+i]*t);
        this.donnees[sommet*OCTETS+9]=opacite;
      };
      for(let segment=0;segment<SEGMENTS;segment++){ecrire(segment);ecrire(segment+1);}
    }
    return {debut,compte:this.nombre-debut,min,max,distance:0};
  }
}

function plansVisibles(m: Float32Array): Plan[] {
  // Les sommets des blocs sont stockés en dix-millièmes d'unité de la scène.
  return [0,1,2].flatMap(axe=>[-1,1].map((signe):Plan=>[
    m[3]+signe*m[axe],m[7]+signe*m[4+axe],m[11]+signe*m[8+axe],10000*(m[15]+signe*m[12+axe])
  ]));
}

function dansChamp(bloc: Bloc, plans: Plan[]): boolean {
  for(const [x,y,z,seuil] of plans){
    if(x*(x<0?bloc.min[0]:bloc.max[0])+y*(y<0?bloc.min[1]:bloc.max[1])+
      z*(z<0?bloc.min[2]:bloc.max[2])+seuil<0)return false;
  }
  return true;
}

export class Arcs {
  private readonly tampon: WebGLBuffer;
  private readonly accent: WebGLBuffer;
  private readonly global: Bloc;
  private readonly locaux: Bloc[];
  private readonly visibilite: WebGLUniformLocation | null;
  private readonly position: number;
  private readonly couleur: number;
  private compteAccent=0;

  constructor(private readonly gl: WebGLRenderingContext, private readonly carte: Carte, programme: WebGLProgram) {
    this.position=gl.getAttribLocation(programme,"position");
    this.couleur=gl.getAttribLocation(programme,"couleur");
    this.visibilite=gl.getUniformLocation(programme,"visibiliteArcs");
    this.tampon=gl.createBuffer()!;
    this.accent=gl.createBuffer()!;
    const {globaux,locaux}=echantillonner(carte);
    const geometrie=new Geometrie(globaux.length+locaux.reduce((n,liens)=>n+liens.length,0),carte);
    this.global=geometrie.bloc(globaux,88);
    this.locaux=locaux.map(liens=>geometrie.bloc(liens,97));
    gl.bindBuffer(gl.ARRAY_BUFFER,this.tampon);
    gl.bufferData(gl.ARRAY_BUFFER,geometrie.donnees,gl.STATIC_DRAW);
  }

  mettreEnValeur(choix: number, joues: Set<number>, attenuer: boolean): void {
    const {voisins,mots}=this.carte.atlas;
    if(!voisins)return;
    const favoris: Lien[]=[], essais: Lien[]=[], vus=new Set<number>();
    if(attenuer){
      for(const a of joues){
        for(const b of voisins[a]){
          const id=cle(a,b,mots.length);
          if(!joues.has(b) || vus.has(id))continue;
          vus.add(id);essais.push([a,b]);
        }
      }
    }
    if(choix>=0){
      for(const b of voisins[choix]){
        if(!vus.has(cle(choix,b,mots.length)))favoris.push([choix,b]);
      }
    }
    const geometrie=new Geometrie(favoris.length+essais.length,this.carte);
    this.compteAccent=geometrie.bloc(favoris,attenuer?21:145).compte+geometrie.bloc(essais,220).compte;
    const gl=this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER,this.accent);
    gl.bufferData(gl.ARRAY_BUFFER,geometrie.donnees,gl.DYNAMIC_DRAW);
  }

  private lier(tampon: WebGLBuffer): void {
    const gl=this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER,tampon);
    gl.vertexAttribPointer(this.position,3,gl.SHORT,false,OCTETS,0);
    gl.vertexAttribPointer(this.couleur,4,gl.UNSIGNED_BYTE,true,OCTETS,6);
  }

  dessiner(m: Float32Array, centre: Point, distance: number, budget: number, attenuer: boolean): void {
    if(!this.global.compte && !this.locaux.length && !this.compteAccent)return;
    const gl=this.gl, opacite=attenuer?.22:1;
    this.lier(this.tampon);
    const detail=Math.min(1,Math.max(0,(1.2-distance)/.55));
    gl.uniform1f(this.visibilite,opacite*(1-.25*detail));
    gl.drawArrays(gl.LINES,this.global.debut,this.global.compte);
    if(detail>0){
      const plans=plansVisibles(m);
      const [x,y,z]=centre.map(v=>v*10000);
      const visibles=this.locaux.filter(bloc=>{
        if(!dansChamp(bloc,plans))return false;
        const {min,max}=bloc;
        const dx=(min[0]+max[0])/2-x,dy=(min[1]+max[1])/2-y,dz=(min[2]+max[2])/2-z;
        bloc.distance=dx*dx+dy*dy+dz*dz;
        return true;
      }).sort((a,b)=>a.distance-b.distance);
      gl.uniform1f(this.visibilite,opacite*detail);
      let reste=budget*SOMMETS;
      for(const bloc of visibles){
        const compte=Math.min(reste,bloc.compte);
        gl.drawArrays(gl.LINES,bloc.debut,compte);
        reste-=compte;
        if(!reste)break;
      }
    }
    if(this.compteAccent){
      this.lier(this.accent);
      gl.uniform1f(this.visibilite,1);
      gl.drawArrays(gl.LINES,0,this.compteAccent);
    }
  }
}

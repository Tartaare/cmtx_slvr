import {Arcs} from "./arcs.js";
import {axes, cadre, cameraInitiale, cleMot, projeter} from "./projection.js";
import type {Camera, Carte, Point} from "./projection.js";
import type {Observation} from "./rendu.js";

const sommet = `
attribute vec3 position;
attribute vec4 couleur;
attribute float joue;
uniform mat4 camera;
uniform float resolution, modeEssais, diametre, visibiliteArcs;
uniform bool modeArcs;
varying vec4 teinte;
void main() {
  if (modeArcs) {
    gl_Position = camera * vec4(position * .0001, 1.);
    teinte = vec4(couleur.rgb, couleur.a * visibiliteArcs);
    return;
  }
  gl_Position = camera * vec4(position, 1.);
  float d = max(.002, gl_Position.w);
  float intensite = mix(1., mix(.11, 1., joue), modeEssais);
  // Perspective en 1/d, avec un plafond progressif pour contenir le coût au premier plan.
  gl_PointSize = (1. + diametre / (d + diametre / 20.) + 2. * joue * modeEssais) * resolution;
  teinte = vec4(mix(vec3(.43, .49, .55), couleur.rgb, intensite), clamp(.9 * inversesqrt(d), .24, .96) * intensite);
}`;
const fragment = `
precision mediump float;
uniform bool modeArcs;
varying vec4 teinte;
void main() {
  if (modeArcs) {
    gl_FragColor = teinte;
    return;
  }
  vec2 p = 2. * gl_PointCoord - 1.;
  if (dot(p, p) >= 1.) discard;
  float bord = 1. - smoothstep(.68, 1., length(p));
  float relief = sqrt(max(0., 1. - dot(p, p)));
  float lumiere = max(0., dot(vec3(p, relief), vec3(-.36, -.42, .83)));
  gl_FragColor = vec4(teinte.rgb * (.62 + .55 * lumiere), teinte.a * bord);
}`;
const limite = (n: number, min: number, max: number) => Math.min(max,Math.max(min,n));
function courbe(ctx: CanvasRenderingContext2D, [x,y]: Point, [u,v]: Point, sens: number): void {
  const dx=u-x, dy=v-y, inflexion=sens*Math.min(.36,96/Math.hypot(dx,dy));
  ctx.beginPath();
  ctx.moveTo(x,y);
  ctx.quadraticCurveTo((x+u)/2-dy*inflexion,(y+v)/2+dx*inflexion,u,v);
  ctx.stroke();
}

export class Scene {
  readonly cible: Camera;
  private camera: Camera;
  private readonly gl: WebGLRenderingContext;
  private readonly matrice: WebGLUniformLocation | null;
  private readonly resolution: WebGLUniformLocation | null;
  private readonly modeEssais: WebGLUniformLocation | null;
  private readonly diametre: WebGLUniformLocation | null;
  private readonly modeArcs: WebGLUniformLocation | null;
  private readonly points: {attribut: number; tampon: WebGLBuffer; type: number; normalise: boolean}[];
  private readonly joue: number;
  private readonly arcs: Arcs;
  private readonly masque: WebGLBuffer;
  private readonly dessin: CanvasRenderingContext2D;
  private frame = 0;
  private dernier = 0;
  private qualite = Math.min(1.65,devicePixelRatio);
  private lents = 0;
  private choix = -1;
  private proches: number[] = [];
  private essais: Observation[] = [];
  private resultats = new Map<string,Observation>();
  private meilleur: Observation | undefined;
  private readonly joues = new Set<number>();
  private attenuer = false;
  private readonly taille: ResizeObserver;
  private readonly mouvement = matchMedia("(prefers-reduced-motion: reduce)");

  constructor(private canvas: HTMLCanvasElement, overlay: HTMLCanvasElement, readonly carte: Carte,
    private niveau: (nom: string)=>void) {
    const gl=canvas.getContext("webgl",{alpha:true,antialias:false,depth:false,preserveDrawingBuffer:false});
    const dessin=overlay.getContext("2d");
    if (!gl || !dessin) throw new Error("Rendu 3D indisponible");
    this.gl=gl; this.dessin=dessin;
    this.camera=cameraInitiale(canvas.clientWidth/Math.max(1,canvas.clientHeight));
    this.cible=structuredClone(this.camera);
    const programme=gl.createProgram()!;
    for (const [type,source] of [[gl.VERTEX_SHADER,sommet],[gl.FRAGMENT_SHADER,fragment]] as const) {
      const shader=gl.createShader(type)!;
      gl.shaderSource(shader,source); gl.compileShader(shader); gl.attachShader(programme,shader); gl.deleteShader(shader);
    }
    gl.linkProgram(programme);
    if (!gl.getProgramParameter(programme,gl.LINK_STATUS)) throw new Error("Programme graphique indisponible");
    gl.useProgram(programme);
    this.points=([
      ["position",carte.positions,gl.FLOAT,false], ["couleur",carte.couleurs,gl.UNSIGNED_BYTE,true]
    ] as const).map(([nom,donnees,type,normalise])=>{
      const tampon=gl.createBuffer()!;
      gl.bindBuffer(gl.ARRAY_BUFFER,tampon); gl.bufferData(gl.ARRAY_BUFFER,donnees,gl.STATIC_DRAW);
      const attribut=gl.getAttribLocation(programme,nom);
      gl.enableVertexAttribArray(attribut);
      return {attribut,tampon,type,normalise};
    });
    this.masque=gl.createBuffer()!;
    gl.bindBuffer(gl.ARRAY_BUFFER,this.masque);
    gl.bufferData(gl.ARRAY_BUFFER,new Uint8Array(carte.index.size),gl.DYNAMIC_DRAW);
    this.joue=gl.getAttribLocation(programme,"joue");
    gl.vertexAttribPointer(this.joue,1,gl.UNSIGNED_BYTE,true,0,0);
    gl.enable(gl.BLEND); gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
    this.matrice=gl.getUniformLocation(programme,"camera");
    this.resolution=gl.getUniformLocation(programme,"resolution");
    this.modeEssais=gl.getUniformLocation(programme,"modeEssais");
    this.diametre=gl.getUniformLocation(programme,"diametre");
    this.modeArcs=gl.getUniformLocation(programme,"modeArcs");
    this.arcs=new Arcs(gl,carte,programme);
    this.taille=new ResizeObserver(()=>{
      if(this.choix<0 && this.cible.centre.every(x=>x===0)) this.globale();
      this.actualiser();
    });
    this.taille.observe(canvas);
    this.actualiser();
  }
  arreter(): void { this.taille.disconnect(); cancelAnimationFrame(this.frame); }
  deselectionner(): void {
    this.choix=-1;this.proches=[];
    this.arcs.mettreEnValeur(this.choix,this.joues,this.attenuer);
    this.actualiser();
  }
  nouvellePartie(): void {
    this.deselectionner();this.journal([]);this.globale();
  }
  globale(): void {
    Object.assign(this.cible,cameraInitiale(this.canvas.clientWidth/Math.max(1,this.canvas.clientHeight)));
    this.actualiser();
  }
  zoom(facteur: number): void {
    this.cible.distance=limite(this.cible.distance*facteur,.045,7);
    this.actualiser();
  }
  orienter(dx: number,dy: number,translation=false): void {
    if(translation){
      const [a,b]=axes(this.cible), k=this.cible.distance*2/(1.85*this.canvas.clientHeight);
      for(let i=0;i<3;i++) this.cible.centre[i]+=(-dx*a[i]+dy*b[i])*k;
    }else{
      this.cible.longitude-=dx*.006;
      this.cible.latitude=limite(this.cible.latitude+dy*.006,-1.54,1.54);
    }
    this.actualiser();
  }
  selection(i: number, distance: number): void {
    if(i!==this.choix){
      this.choix=i;
      const points=this.carte.positions;
      const centre=points.subarray(i*3,i*3+3);
      // Les repères de proximité utilisent les positions de la scène. Les arcs utilisent les vecteurs du modèle.
      const region: {id:number; distance:number}[]=[];
      for(let j=0;j<this.carte.index.size;j++){
        const distance=(points[j*3]-centre[0])**2+(points[j*3+1]-centre[1])**2+(points[j*3+2]-centre[2])**2;
        if(j!==i && distance<.08**2)region.push({id:j,distance});
      }
      this.proches=region.sort((a,b)=>a.distance-b.distance).slice(0,96).map(p=>p.id);
      this.arcs.mettreEnValeur(this.choix,this.joues,this.attenuer);
    }
    this.cible.centre=Array.from(this.carte.positions.subarray(i*3,i*3+3)) as Point;
    this.cible.distance=distance; this.actualiser();
  }
  pointer(x: number,y: number): number {
    const w=this.canvas.clientWidth,h=this.canvas.clientHeight,m=cadre(this.camera,w,h);
    let meilleur=-1, seuil=14**2;
    for(let i=0;i<this.carte.index.size;i++){
      const [px,py,d]=projeter(m,this.carte.positions,i,w,h), dist=(px-x)**2+(py-y)**2;
      if(d>.003 && dist<seuil){meilleur=i;seuil=dist;}
    }
    return meilleur;
  }
  journal(essais: Observation[], grilleReelle=false): void {
    this.essais=essais.map(o=>({...o,mot:cleMot(o.mot)}));
    this.resultats=new Map(this.essais.map(o=>[o.mot,o]));
    this.meilleur=this.essais.reduce<Observation|undefined>((a,b)=>b.temperature!==null &&
      (b.statut==="victoire" || b.temperature>(a?.temperature??-Infinity))?b:a,undefined);
    this.joues.clear();
    for(const mot of this.resultats.keys()){
      const i=this.carte.index.get(mot);
      if(i!==undefined)this.joues.add(i);
    }
    this.attenuer=grilleReelle && this.joues.size>0;
    const masque=new Uint8Array(this.carte.index.size);
    for(const i of this.joues)masque[i]=255;
    this.gl.bindBuffer(this.gl.ARRAY_BUFFER,this.masque);
    this.gl.bufferSubData(this.gl.ARRAY_BUFFER,0,masque);
    this.arcs.mettreEnValeur(this.choix,this.joues,this.attenuer);
    this.actualiser();
  }
  actualiser(): void {
    if(!this.frame) this.frame=requestAnimationFrame(t=>this.afficher(t));
  }
  private afficher(t: number): void {
    this.frame=0;
    const w=this.canvas.clientWidth,h=this.canvas.clientHeight;
    if(!w || !h || this.gl.isContextLost()) return;
    const intervalle=t-this.dernier, dt=intervalle<150?intervalle:16;
    this.lents=intervalle>25 && intervalle<150?this.lents+1:0;
    if(this.lents>=6){this.qualite=Math.max(.75,this.qualite-.25);this.lents=0;}
    const k=this.mouvement.matches?1:1-Math.exp(-Math.min(dt,64)/100);
    let suite=false;
    const avancer=(a:number,b:number)=>{
      if(Math.abs(b-a)<.00015) return b;
      suite ||= k<1; return a+(b-a)*k;
    };
    for(const champ of ["distance","longitude","latitude"] as const)
      this.camera[champ]=avancer(this.camera[champ],this.cible[champ]);
    this.camera.centre=this.camera.centre.map((a,i)=>avancer(a,this.cible.centre[i])) as Point;
    const m=cadre(this.camera,w,h), gl=this.gl;
    const ratio=this.qualite;
    for(const c of [this.canvas,this.dessin.canvas]){
      const largeur=Math.round(w*ratio),hauteur=Math.round(h*ratio);
      if(c.width!==largeur || c.height!==hauteur){c.width=largeur;c.height=hauteur;}
    }
    gl.viewport(0,0,this.canvas.width,this.canvas.height); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.uniformMatrix4fv(this.matrice,false,m);
    gl.uniform1i(this.modeArcs,1);
    gl.disableVertexAttribArray(this.joue);
    const budget=Math.round((w<600?950:2200)*Math.min(1,ratio/devicePixelRatio));
    this.arcs.dessiner(m,this.camera.centre,this.camera.distance,budget,this.attenuer);
    gl.uniform1i(this.modeArcs,0);
    for(const {attribut,tampon,type,normalise} of this.points){
      gl.bindBuffer(gl.ARRAY_BUFFER,tampon);
      gl.vertexAttribPointer(attribut,3,type,normalise,0,0);
    }
    gl.enableVertexAttribArray(this.joue);
    gl.uniform1f(this.resolution,ratio);
    gl.uniform1f(this.diametre,limite(h*.0045,2,4.8));
    gl.uniform1f(this.modeEssais,Number(this.attenuer));
    gl.drawArrays(gl.POINTS,0,this.carte.index.size);
    this.annotations(m,w,h,ratio);
    this.niveau(this.camera.distance<.36?"Vue immersive":this.camera.distance<1.35?"Vue régionale":"Vue globale");
    this.dernier=t;
    if(suite) this.actualiser();
  }
  private annotations(m: Float32Array,w: number,h: number,ratio: number): void {
    const ctx=this.dessin; ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,w,h);
    const ecran=(i:number)=>projeter(m,this.carte.positions,i,w,h);
    const visible=([x,y,d]:Point)=>d>.005 && x>0 && x<w && y>0 && y<h;
    let precedent: Point|undefined;
    for(const o of this.essais){
      const i=this.carte.index.get(o.mot), p=i===undefined?undefined:ecran(i);
      if(p && p[2]>.005){
        const repereVisible=visible(p);
        if(precedent && precedent[2]>.005 && (repereVisible || visible(precedent))){
          ctx.strokeStyle=this.attenuer?"rgba(245,184,109,.87)":"rgba(240,235,222,.55)";
          ctx.lineWidth=1.2;ctx.setLineDash([4,4]);courbe(ctx,precedent,p,-1);ctx.setLineDash([]);
        }
        if(repereVisible){
          ctx.strokeStyle=o.statut==="refus"?"#a7a9ad":o.temperature!<0?"#96d2ff":"#ffc079";
          ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(p[0],p[1],o===this.meilleur?8:5,0,2*Math.PI);ctx.stroke();ctx.lineWidth=1;
        }
      }
      precedent=p;
    }
    const meilleur=this.meilleur?this.carte.index.get(this.meilleur.mot):undefined;
    const proximite=limite((1.65-this.camera.distance)/.6,0,1);
    if(this.choix>=0){
      const p=ecran(this.choix);
      if(visible(p)){
        ctx.strokeStyle="#fff6d8";ctx.lineWidth=1;
        ctx.beginPath();ctx.arc(p[0],p[1],6,0,Math.PI*2);ctx.stroke();
      }
    }
    const reperes=this.attenuer?[...this.joues].reverse():
      [...this.proches.slice(0,Math.ceil(96*proximite)),...this.carte.atlas.reperes];
    const candidats=[this.choix,meilleur??-1,...reperes];
    const zones:number[][]=[];
    for(const i of new Set(candidats)){
      if(i<0) continue;
      const p=ecran(i); if(!visible(p))continue;
      const prioritaire=i===this.choix || i===meilleur || (this.attenuer && this.joues.has(i));
      const mot=this.carte.atlas.mots[i][0];
      const resultat=this.resultats.get(mot);
      const marque=resultat?.statut==="victoire"?"✓ ":i===meilleur?"★ ":"";
      const score=resultat?.temperature;
      const libelle=marque+mot+(prioritaire && resultat?
        (score==null?" · refus":" · "+score.toLocaleString("fr-FR")+" °C"):"");
      ctx.font=(prioritaire?"600 14px":"12px")+" Consolas, monospace";
      const largeur=ctx.measureText(libelle).width+12, x=limite(p[0]+9,5,w-largeur-5), y=limite(p[1]-20,5,h-24);
      if((y<62 && (x<120 || x+largeur>w-220)) || (y>h-72 && (x<155 || x+largeur>w-150)))continue;
      if(zones.some(([a,b,c,d])=>x<a+c+12 && x+largeur+12>a && y<b+d+9 && y+28>b))continue;
      zones.push([x,y,largeur,20]);
      ctx.globalAlpha=prioritaire || this.carte.atlas.reperes.includes(i)?1:proximite;
      ctx.fillStyle=prioritaire?"#181b1f":"rgba(10,12,15,.75)";ctx.fillRect(x,y,largeur,20);
      ctx.fillStyle=prioritaire?"#fff6d8":"#d0d6d8";ctx.fillText(libelle,x+6,y+14);
      if(zones.length >= (w<560?3:this.camera.distance<1.35?10:5))break;
    }
    ctx.globalAlpha=1;
  }
}

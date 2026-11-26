import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {readFile} from "node:fs/promises";
import test from "node:test";
import {cadre, cameraInitiale, indexer, projeter, type Atlas} from "../interface/projection.ts";

test("l’atlas livre chaque mot du lexique réduit à sa ligne d’origine",async()=>{
  const contenu=await readFile(new URL("../interface/atlas.json",import.meta.url));
  const atlas=JSON.parse(contenu.toString("utf8")) as Atlas;
  const carte=indexer(atlas);
  assert.equal(carte.index.size,55402);
  assert.equal(atlas.dimensions,500);
  const lexique=Array.from(carte.index.keys()).join("\n")+"\n";
  assert.equal(createHash("sha256").update(lexique).digest("hex"),
    "8fb690c1c296a3c4345dd77e7dc67bf0f881de6d90f38e286f14b582ec8ba3b8");
  assert.ok(carte.positions.every(v=>Number.isFinite(v) && Math.abs(v)<=1));
  assert.ok(atlas.reperes.every((id,groupe)=>atlas.mots[id][4]===groupe));
  assert.ok(atlas.voisins);
  assert.equal(atlas.voisins.length, atlas.mots.length);
  const chien = carte.index.get("chien")!;
  assert.ok(atlas.voisins[chien].some(i => atlas.mots[i][0] === "chiens"));
  const ancienAtlas = {...atlas, voisins: undefined};
  assert.equal(indexer(ancienAtlas).index.size, carte.index.size);
  const voisinsInvalides = atlas.voisins.slice();
  voisinsInvalides[chien] = [chien, ...atlas.voisins[chien].slice(1)];
  assert.throws(() => indexer({...atlas, voisins: voisinsInvalides}), /Liens de projection incohérents/);
  const id=carte.index.get("piano")!, camera=cameraInitiale(1.5);
  camera.centre=[carte.positions[id*3],carte.positions[id*3+1],carte.positions[id*3+2]];
  const [x,y,z]=projeter(cadre(camera,1200,800),carte.positions,id,1200,800);
  assert.ok(Math.abs(x-600)<.001 && Math.abs(y-400)<.001 && z>0);
});

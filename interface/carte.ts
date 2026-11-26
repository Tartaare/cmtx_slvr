import {ouvrirGalaxie} from "./galaxie.js";
import {animerLentille} from "./lentille.js";

void ouvrirGalaxie();
const dock = document.querySelector<HTMLElement>(".dock");
if (dock) animerLentille(dock);

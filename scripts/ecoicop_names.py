"""Write econpulse/ecoicop_es.json: the Spanish names of the HICP basket's categories and items, by ECOICOP code.

Eurostat names the items in English only; INE publishes the same ECOICOP ver. 2 classification in Spanish, with
the codes ("01.1.1.1" is Eurostat's CP01111). Run again if the classification changes:

    python scripts/ecoicop_names.py
"""

import json
from pathlib import Path

from econpulse import http

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "econpulse" / "ecoicop_es.json"
BASE = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA"
TABLES = {76156: "Grupos ECOICOP", 76159: "Subclases ECOICOP"}    # the 2026 weights: groups (13), subclasses
# Items Eurostat lists that INE folds into others, named here in INE's style.
FILL = {
    "CP01137": "Hígados, huevas y otros despojos de pescado y marisco",
    "CP01153": "Margarina y preparados similares",
    "CP01167": "Frutas secas y deshidratadas",
    "CP03131": "Otros artículos de vestir",
    "CP03132": "Accesorios de vestir",
    "CP03141": "Limpieza de prendas de vestir",
    "CP03220": "Limpieza, reparación y alquiler de calzado",
    "CP05329": "Otros pequeños electrodomésticos",
    "CP05402": "Cubertería y platería",
    "CP05510": "Herramientas y equipos motorizados",
    "CP06121": "Productos de diagnóstico médico",
    "CP07224": "Lubricantes",
    "CP07412": "Servicios de mensajería y paquetería",
    "CP07491": "Servicios de mudanza y almacenamiento",
    "CP08132": "Equipos periféricos y sus consumibles",
    "CP08150": "Soportes de grabación vírgenes",
    "CP09111": "Cámaras",
    "CP09129": "Otros bienes duraderos importantes para el ocio",
    "CP09222": "Equipo de camping y ocio al aire libre",
    "CP09311": "Productos de jardinería",
    "CP09520": "Soportes audiovisuales",
    "CP09722": "Revistas y publicaciones periódicas",
    "CP12130": "Seguros relacionados con la vivienda",
    "CP13301": "Servicios de guardería",
}


def eurostat_code(ine: str) -> str:
    return "CP" + ine.replace(".", "")


def names() -> dict[str, str]:
    out = {}
    for table, variable in TABLES.items():
        for row in http.get(f"{BASE}/{table}", params={"nult": 1, "tip": "AM"}).json():
            for meta in row.get("MetaData", []):
                if meta.get("T3_Variable", "").strip() == variable and meta.get("Codigo"):
                    out[eurostat_code(meta["Codigo"])] = " ".join(meta["Nombre"].split())
    return dict(sorted({**FILL, **out}.items()))


if __name__ == "__main__":
    found = names()
    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(found)} names -> {OUT}")

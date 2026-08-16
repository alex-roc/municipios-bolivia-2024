#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["geopandas>=1.0", "pyogrio>=0.9"]
# ///
"""Genera los formatos derivados que ofrece el sitio: shapefile y GeoPackage.

Las fuentes de verdad son los GeoJSON/TopoJSON de la raíz; esto solo los traduce.
Se ejecuta solo, sin instalar nada a mano:

    ./build/generar-descargas.py

Por qué existe en vez de un `ogr2ogr` suelto: shapefile trunca los nombres de
campo a 10 caracteres, y si se deja que la librería improvise, `nombre_prov` y
`superficie_km2` salen con nombres distintos según la versión de GDAL. Aquí el
renombrado es explícito y queda documentado en el README.
"""

import shutil
import zipfile
from pathlib import Path

import geopandas as gpd

RAIZ = Path(__file__).resolve().parent.parent
TMP = RAIZ / "build" / ".tmp"

# Nombres largos -> el nombre que tendrán dentro del shapefile (máx. 10 car.).
RENOMBRAR = {"nombre_prov": "nombre_pro", "superficie_km2": "superficie"}

# Orden de columnas en las salidas de municipios.
COLUMNAS = [
    "codigo_ine", "idep", "nombre_dep", "iprov", "nombre_prov",
    "imun", "nombre_mun", "capital", "superficie_km2",
]


def leer(nombre: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(RAIZ / nombre)
    if gdf.crs is None:                       # el TopoJSON no declara CRS
        gdf = gdf.set_crs(4326)
    return gdf


def con_codigo_ine(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Asegura la columna codigo_ine, que el GeoJSON general no trae."""
    if "codigo_ine" not in gdf.columns:
        gdf = gdf.assign(codigo_ine=gdf.idep + gdf.iprov + gdf.imun)
    orden = [c for c in COLUMNAS if c in gdf.columns] + ["geometry"]
    return gdf[orden]


def a_shapefile(gdf: gpd.GeoDataFrame, capa: str) -> Path:
    carpeta = TMP / capa
    carpeta.mkdir(parents=True, exist_ok=True)
    gdf.rename(columns=RENOMBRAR).to_file(
        carpeta / f"{capa}.shp", driver="ESRI Shapefile", encoding="utf-8"
    )
    destino = RAIZ / f"{capa}_shp.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for parte in sorted(carpeta.iterdir()):
            z.write(parte, parte.name)
    return destino


def peso(p: Path) -> str:
    mb = p.stat().st_size / 1e6
    return f"{mb:.1f} MB" if mb >= 1 else f"{p.stat().st_size / 1e3:.0f} KB"


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)

    mun = con_codigo_ine(leer("municipios_bolivia_2024.geojson"))
    det = con_codigo_ine(leer("municipios_bolivia_2024_detalle.topojson"))
    dep = leer("departamentos_bolivia.geojson")

    print("shapefiles:")
    salidas = [
        (a_shapefile(mun, "municipios_bolivia_2024"), len(mun)),
        (a_shapefile(det, "municipios_bolivia_2024_detalle"), len(det)),
        (a_shapefile(dep, "departamentos_bolivia"), len(dep)),
    ]
    for ruta, n in salidas:
        print(f"  {ruta.name:<42} {peso(ruta):>8}  {n} rasgos")

    print("geopackage:")
    gpkg = RAIZ / "municipios_bolivia_2024.gpkg"
    gpkg.unlink(missing_ok=True)
    mun.to_file(gpkg, layer="municipios", driver="GPKG")
    dep.to_file(gpkg, layer="departamentos", driver="GPKG")
    print(f"  {gpkg.name:<42} {peso(gpkg):>8}  2 capas")

    esperado = {"municipios_bolivia_2024": 343,
                "municipios_bolivia_2024_detalle": 343,
                "departamentos_bolivia": 9}
    for ruta, n in salidas:
        capa = ruta.name.removesuffix("_shp.zip")
        assert n == esperado[capa], f"{capa}: {n} rasgos, se esperaban {esperado[capa]}"
    print("\nconteos verificados: 343 / 343 / 9")

    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

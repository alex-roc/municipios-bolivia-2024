#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["geopandas>=1.0", "pyogrio>=0.9", "matplotlib>=3.8", "pillow>=10"]
# ///
"""Genera el mapa de cabecera (claro y oscuro) y la imagen social del sitio.

    ./build/generar-imagenes.py

Salidas: img/mapa-light.png, img/mapa-dark.png, img/og.png
"""

from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
IMG = RAIZ / "img"

# Las cuatro unidades territoriales creadas entre 2016 y 2023.
NUEVAS = {"031304", "050405", "051204", "080901"}

PIE = "343 municipios del CPV-2024  ·  en azul, las cuatro unidades creadas desde 2016"

TEMAS = {
    "light": dict(fondo="#f7f6f2", relleno="#d6d3cd", borde_mun="#ffffff",
                  borde_dep="#5a5a5a", nuevo="#1a73c8", texto="#4a4a46"),
    "dark":  dict(fondo="#14171a", relleno="#2b3138", borde_mun="#14171a",
                  borde_dep="#8b949e", nuevo="#4a9eff", texto="#8b949e"),
}


def cargar():
    mun = gpd.read_file(RAIZ / "municipios_bolivia_2024.geojson")
    dep = gpd.read_file(RAIZ / "departamentos_bolivia.geojson")
    mun["codigo_ine"] = mun.idep + mun.iprov + mun.imun
    return mun, dep


def dibujar(mun, dep, tema, ruta, con_pie=True, ancho=9.0):
    t = TEMAS[tema]
    fig, ax = plt.subplots(figsize=(ancho, ancho * 1.12), dpi=125)
    fig.patch.set_facecolor(t["fondo"])
    ax.set_facecolor(t["fondo"])

    mun.plot(ax=ax, color=t["relleno"], edgecolor=t["borde_mun"], linewidth=0.45)
    nuevas = mun[mun.codigo_ine.isin(NUEVAS)]
    nuevas.plot(ax=ax, color=t["nuevo"], edgecolor=t["borde_mun"], linewidth=0.45)
    dep.boundary.plot(ax=ax, color=t["borde_dep"], linewidth=1.15)

    ax.set_axis_off()
    ax.margins(0.01)
    if con_pie:
        fig.text(0.5, 0.022, PIE, ha="center", va="bottom",
                 fontsize=10.5, color=t["texto"])
    fig.savefig(ruta, facecolor=t["fondo"], bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(f"  {ruta.relative_to(RAIZ)}  {ruta.stat().st_size / 1e3:.0f} KB")


def social(mun, dep):
    """Imagen 1200x630 para Open Graph: mapa a la derecha, titular a la izquierda."""
    t = TEMAS["light"]
    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor(t["fondo"])

    ax = fig.add_axes([0.60, 0.02, 0.38, 0.96])
    ax.set_facecolor(t["fondo"])
    mun.plot(ax=ax, color=t["relleno"], edgecolor="#ffffff", linewidth=0.35)
    mun[mun.codigo_ine.isin(NUEVAS)].plot(ax=ax, color=t["nuevo"],
                                          edgecolor="#ffffff", linewidth=0.35)
    dep.boundary.plot(ax=ax, color=t["borde_dep"], linewidth=0.9)
    ax.set_axis_off()

    fig.text(0.06, 0.70, "343 municipios\nde Bolivia", fontsize=44,
             fontweight="bold", color="#22252a", linespacing=1.15, va="top")
    fig.text(0.06, 0.40, "Geografía municipal del Censo 2024\n"
                         "GeoJSON · TopoJSON · Shapefile\nGeoPackage · CSV",
             fontsize=16, color="#5c6068", linespacing=1.5, va="top")
    fig.text(0.06, 0.11, "Lab TecnoSocial", fontsize=15,
             color="#0f9d58", fontweight="bold", va="bottom")

    ruta = IMG / "og.png"
    fig.savefig(ruta, facecolor=t["fondo"])
    plt.close(fig)
    Image.open(ruta).convert("RGB").resize((1200, 630), Image.LANCZOS).save(
        ruta, optimize=True)
    print(f"  {ruta.relative_to(RAIZ)}  {ruta.stat().st_size / 1e3:.0f} KB  1200x630")


def main():
    IMG.mkdir(exist_ok=True)
    mun, dep = cargar()
    faltan = NUEVAS - set(mun.codigo_ine)
    assert not faltan, f"códigos no encontrados: {faltan}"
    print("mapas:")
    dibujar(mun, dep, "light", IMG / "mapa-light.png")
    dibujar(mun, dep, "dark", IMG / "mapa-dark.png")
    print("social:")
    social(mun, dep)


if __name__ == "__main__":
    main()

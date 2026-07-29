# Municipios de Bolivia — 343 unidades (CPV-2024)

Geografía municipal lista para usar, con los **343 municipios** que reconoce el
Censo de Población y Vivienda 2024 y los códigos del INE que usan los microdatos
censales.

> **Uso referencial.** Estos polígonos sirven para mapear y agregar datos, no para
> dirimir cuestiones de jurisdicción. Bolivia tiene procesos de delimitación
> abiertos entre municipios y departamentos, y esta capa no es una fuente
> autoritativa sobre ellos.

## Archivos

| Archivo | Detalle | Peso | Para qué |
|---|---|---|---|
| `municipios_bolivia_2024.geojson` | 55.605 vértices | 1,6 MB | **El de uso general.** Mapas nacionales y departamentales, web, coropletas |
| `municipios_bolivia_2024_detalle.topojson` | 741.926 vértices | 10,8 MB (3,3 MB gzip) | Zoom fino de bordes, recortes, análisis espacial preciso |
| `departamentos_bolivia.geojson` | 9 polígonos | 0,3 MB | Contorno departamental para superponer |
| `municipios_bolivia_2024.csv` | 343 filas | 28 KB | La tabla sin geometría, para joins rápidos |

**CRS:** WGS84 / EPSG:4326 en todos. Geometrías válidas y topológicamente limpias
(0 inválidas en los cuatro archivos).

Los departamentos salen de disolver los municipios, así que sus bordes caen
exactamente sobre los municipales: se pueden superponer sin desajustes.

### Notas sobre el TopoJSON

- **No declara CRS**, porque la especificación de TopoJSON asume WGS84. Algunas
  herramientas lo reportan como `NA`; asígnale EPSG:4326 y listo
  (`sf::st_crs(x) <- 4326`).
- **Sin cuantización**, a propósito. La cuantización es lo que suele hacer pequeño
  a un TopoJSON, pero en una capa con 742.000 vértices tan densos colapsa vértices
  contiguos y deja aristas degeneradas. Sin cuantizar queda limpio y aun así
  pesa la mitad que el GeoJSON equivalente (22,2 MB).
- Trae el código INE como `id` del objeto, además de la columna `codigo_ine`.

## Columnas

| Columna | Ejemplo | Nota |
|---|---|---|
| `idep` | `"01"` | Departamento, 2 dígitos con cero a la izquierda |
| `nombre_dep` | `"Chuquisaca"` | |
| `iprov` | `"01"` | Provincia |
| `nombre_prov` | `"Oropeza"` | |
| `imun` | `"01"` | Municipio dentro de la provincia |
| `nombre_mun` | `"Sucre"` | Nombre del INE |
| `capital` | `"Sucre"` | Capital municipal |
| `superficie_km2` | `1671.1` | |
| `codigo_ine` | `"010101"` | Solo en el CSV y el TopoJSON: los tres códigos concatenados |

La clave para unir con datos censales es **`idep + iprov + imun`**. Ojo con los
ceros a la izquierda: si tu herramienta lee los códigos como número, `"01"` se
vuelve `1` y el join falla en silencio. Léelos como texto.

## Cómo se construyó

Ninguna fuente pública tiene a la vez la geometría de las 343 unidades y la
codificación que usan los microdatos del censo, así que la capa cruza tres fuentes:

1. **Municipios de GeoBolivia** de 2015
2. **Códigos `idep`/`iprov`/`imun` y nombres** — INE Bolivia (Redatam, CPV-2024),
   para que coincidan exactamente con los microdatos censales.
3. **Geometría, capital y superficie** — [SDSN
   Bolivia](https://sdsnbolivia.org/datos-espaciales/), capa del Atlas Municipal de los ODS (junio 2025). Es la única pública que cubre las 343 unidades: los 339 municipios más los cuatro GAIOC creados entre 2016 y 2023. A su vez se armó
   sobre el archivo oficial del Ministerio de Autonomías (2015, publicado en
   GeoBolivia) y las leyes de creación de esas cuatro unidades.
4. **El emparejamiento** — los ~21.000 puntos de comunidades del
   CPV-2024 del geoportal del INE, que llevan el código del INE y sirven de árbitro
   para asignarle a cada polígono el suyo. Hizo falta porque el `Codigo_INE` del
   shapefile de SDSN parece desalineado en 7 municipios de Omasuyos (La Paz) y
   Ñuflo de Chávez (Santa Cruz) — le pone a San Ramón el código de San Julián, y
   así. Los nombres sí van con el polígono correcto; solo la columna de código está
   mal pegada. Aquí ya está corregido.

La versión simplificada se hizo con [mapshaper](https://github.com/mbloch/mapshaper) (Visvalingam sobre arcos compartidos, `keep = 0.05`), que **preserva la topología**: los bordes entre vecinos quedan idénticos y no aparecen franjas vacías. Si necesitas simplificar más, usa mapshaper y no un simplificador por polígono (`st_simplify` de sf,
`shapely.simplify`): esos tratan cada polígono por separado, rompen los bordes
compartidos y dejan huecos.

Los únicos huecos interiores del país son cuerpos de agua fuera de la división
municipal: el Salar de Uyuni (9.476 km²) y los lagos Poopó (1.285) y Uru Uru (116).

## Validación

- **Puntos del CPV-2024 dentro de su municipio:** 97,53% en la versión de detalle,
  97,30% en la simplificada. El resto son puntos prácticamente sobre el borde.
- La **población municipal** de la fuente coincide **exactamente en los 343
  municipios** con el conteo de los microdatos del CPV-2024: 11.365.333 personas.
  (Con el `Codigo_INE` sin corregir coincidía en 336 — es lo que delató el error.)

## Los cuatro municipios que suelen faltar

Casi toda la cartografía municipal boliviana que circula tiene 339 polígonos y le
faltan estos cuatro. Y no es un hueco visible: su territorio aparece **dentro** del
municipio madre, así que los datos salen mal atribuidos sin que se note.

| Municipio | Código | Departamento | Territorio que suele estar dentro de |
|---|---|---|---|
| TIOC-Raqaypampa | 031304 | Cochabamba | Mizque |
| San Pedro de Macha | 050405 | Potosí | Colquechaca |
| TIOC-Jatun Ayllu Yura | 051204 | Potosí | Tomave |
| TIOC-Territorio Indígena Multiétnico | 080901 | Beni | San Ignacio y Santa Ana |

Son 7.599 km². Para dar una idea de lo que cambia: en Raqaypampa el alfabetismo de
15 años o más es del 75,0%, y con una capa de 339 esos 562 km² se pintan con el
87,2% de Mizque.

Si vas a comparar con el **Censo 2012**, ten en cuenta que estos cuatro no existían
entonces: saldrán sin dato.

## Origen y actualización

Esta capa es la que trae el paquete de R
[**censosbo**](https://lab-tecnosocial.github.io/censosbo/) en su objeto
`geo_municipios` (desde la versión 1.6.0):

```r
library(censosbo)
geo_municipios   # sf con los 343
```

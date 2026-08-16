/* Visor de los 343 municipios. Leaflet sin teselas: la capa es el mapa.
   Los colores viven aquí y no en el CSS a propósito — Leaflet escribe atributos
   SVG (stroke, fill) y var() no se resuelve dentro de un atributo. */

(function () {
  "use strict";

  var CODIGOS_AIOC = {
    "011002": "Autonomía Guaraní Chaqueño de Huacaya",
    "031304": "Autonomía Indígena Originaria de Raqaypampa",
    "040801": "Autonomía Indígena Originaria de Salinas",
    "040903": "Nación Originaria Uru Chipaya",
    "051204": "Autonomía Originaria Jatun Ayllu Yura",
    "070702": "Autonomía Guaraní Charagua Iyambae",
    "070705": "Autonomía Indígena Kereimba Iyaambae",
    "080901": "Territorio Indígena Multiétnico",
  };

  var PALETA = {
    claro: {
      dep: ["#cfe3f5", "#d7ecd9", "#f6e5c8", "#e6dcef", "#f7d9d6",
            "#d3ece9", "#f9e9c4", "#dfe3ef", "#e9dfd2"],
      borde: "#ffffff",
      bordeDep: "#8b8f96",
      resalte: "#0f9d58",
      seleccion: "#0b7d45",
      aioc: "#1a73c8",
    },
    oscuro: {
      dep: ["#2b3a4a", "#2c4038", "#443a2a", "#3a3348", "#452f2f",
            "#28403f", "#463f27", "#333846", "#3d3830"],
      borde: "#14171a",
      bordeDep: "#767d86",
      resalte: "#34c77b",
      seleccion: "#4ad98d",
      aioc: "#4a9eff",
    },
  };

  var oscuro = window.matchMedia("(prefers-color-scheme: dark)");
  var tono = function () { return oscuro.matches ? PALETA.oscuro : PALETA.claro; };

  var mapa = L.map("mapa", {
    zoomControl: true,
    attributionControl: false,
    zoomSnap: 0.25,
    zoomDelta: 1,
    wheelPxPerZoomLevel: 40,
    minZoom: 4,
    maxZoom: 12,
  });

  // Un solo canvas para toda la capa, creado una vez: si se recrea en cada
  // repintado quedan canvas huérfanos suscritos a zoom/move.
  var lienzo = L.canvas({ padding: 0.4 });

  var capaMun = null, capaDep = null, seleccionado = null, rasgos = [];
  var elFicha = document.getElementById("ficha");
  var elBusca = document.getElementById("busca");
  var elLista = document.getElementById("municipios-lista");

  var codigoDe = function (f) {
    return f && f.properties
      ? f.properties.idep + f.properties.iprov + f.properties.imun
      : "";
  };

  function estilo(f) {
    var c = tono();
    var cod = codigoDe(f);
    var i = parseInt((f && f.properties && f.properties.idep) || "1", 10) - 1;
    if (cod === seleccionado) {
      return { color: c.seleccion, weight: 2.2, fillColor: c.dep[i], fillOpacity: 0.95,
               renderer: lienzo };
    }
    return {
      color: CODIGOS_AIOC[cod] ? c.aioc : c.borde,
      weight: CODIGOS_AIOC[cod] ? 1.1 : 0.5,
      fillColor: c.dep[i],
      fillOpacity: 0.9,
      renderer: lienzo,
    };
  }

  function estiloDep() {
    return { color: tono().bordeDep, weight: 1.4, fill: false, renderer: lienzo };
  }

  var nf = new Intl.NumberFormat("es-BO", { maximumFractionDigits: 1 });

  function pintarFicha(p) {
    if (!p) {
      elFicha.innerHTML = '<p class="pista">Pasa el cursor por un municipio, o búscalo por nombre.</p>';
      return;
    }
    var cod = p.idep + p.iprov + p.imun;
    var aioc = CODIGOS_AIOC[cod];
    elFicha.innerHTML =
      "<h3>" + p.nombre_mun + "</h3>" +
      '<p class="dep">' + p.nombre_dep + " · prov. " + p.nombre_prov + "</p>" +
      "<dl>" +
      "<dt>Código INE</dt><dd class=\"mono\">" + cod + "</dd>" +
      "<dt>Capital</dt><dd>" + (p.capital || "—") + "</dd>" +
      "<dt>Superficie</dt><dd>" + nf.format(p.superficie_km2) + " km²</dd>" +
      "</dl>" +
      (aioc ? '<p class="aioc">' + aioc + "</p>" : "");
  }

  function seleccionar(cod, encuadrar) {
    seleccionado = cod;
    if (capaMun) capaMun.setStyle(estilo);
    var capa = null;
    capaMun.eachLayer(function (l) { if (codigoDe(l.feature) === cod) capa = l; });
    if (capa) {
      pintarFicha(capa.feature.properties);
      if (encuadrar) mapa.fitBounds(capa.getBounds(), { padding: [60, 60], maxZoom: 9 });
    }
  }

  function alCargar(mun, dep) {
    rasgos = mun.features;

    capaMun = L.geoJSON(mun, {
      style: estilo,
      onEachFeature: function (f, capa) {
        capa.bindTooltip(f.properties.nombre_mun, { sticky: true, direction: "top" });
        capa.on({
          mouseover: function () { if (codigoDe(f) !== seleccionado) pintarFicha(f.properties); },
          mouseout: function () {
            if (!seleccionado) pintarFicha(null);
            else seleccionar(seleccionado, false);
          },
          click: function () { seleccionar(codigoDe(f), true); },
        });
      },
    }).addTo(mapa);

    capaDep = L.geoJSON(dep, { style: estiloDep, interactive: false }).addTo(mapa);

    // invalidateSize antes de encuadrar: el panel lateral es un grid y el mapa
    // puede haberse creado con un ancho que ya no es el definitivo.
    mapa.invalidateSize({ animate: false });
    mapa.fitBounds(capaMun.getBounds(), { padding: [14, 14], animate: false });

    var reencuadrar = null;
    window.addEventListener("resize", function () {
      clearTimeout(reencuadrar);
      reencuadrar = setTimeout(function () {
        mapa.invalidateSize({ animate: false });
      }, 180);
    });

    // Lista para el autocompletado del buscador.
    var nombres = rasgos
      .map(function (f) { return f.properties.nombre_mun; })
      .sort(function (a, b) { return a.localeCompare(b, "es"); });
    elLista.innerHTML = nombres
      .map(function (n) { return '<option value="' + n.replace(/"/g, "&quot;") + '">'; })
      .join("");

    pintarFicha(null);
    document.getElementById("cuenta-mapa").textContent = rasgos.length + " municipios";
  }

  var normaliza = function (s) {
    return s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
  };

  elBusca.addEventListener("input", function () {
    var q = normaliza(elBusca.value);
    if (q.length < 3) return;
    // Exacto, luego por prefijo, luego por subcadena: los nombres del INE llevan
    // prefijos ("TIOC-Raqaypampa") y coletillas ("Charagua (Autonomía…)"), así que
    // solo con prefijo no se encuentra lo que la gente teclea.
    var hallado =
      rasgos.find(function (f) { return normaliza(f.properties.nombre_mun) === q; }) ||
      rasgos.find(function (f) { return normaliza(f.properties.nombre_mun).startsWith(q); }) ||
      rasgos.find(function (f) { return normaliza(f.properties.nombre_mun).indexOf(q) !== -1; });
    if (hallado) seleccionar(codigoDe(hallado), true);
  });

  // Repintar al cambiar el tema del sistema, sin reconstruir la capa.
  var alCambiarTema = function () {
    if (capaMun) capaMun.setStyle(estilo);
    if (capaDep) capaDep.setStyle(estiloDep);
  };
  if (oscuro.addEventListener) oscuro.addEventListener("change", alCambiarTema);
  else if (oscuro.addListener) oscuro.addListener(alCambiarTema);

  Promise.all([
    fetch("municipios_bolivia_2024.geojson").then(function (r) { return r.json(); }),
    fetch("departamentos_bolivia.geojson").then(function (r) { return r.json(); }),
  ])
    .then(function (d) { alCargar(d[0], d[1]); })
    .catch(function (e) {
      document.getElementById("mapa").innerHTML =
        '<p style="padding:28px;color:#85888f">No se pudo cargar la capa. ' +
        'Puedes descargarla igualmente desde la sección de descargas.</p>';
      console.error(e);
    });

  // Pestañas de los ejemplos de código.
  var pestanas = Array.prototype.slice.call(document.querySelectorAll(".pestanas button"));
  pestanas.forEach(function (b) {
    b.addEventListener("click", function () {
      pestanas.forEach(function (o) {
        var activa = o === b;
        o.setAttribute("aria-selected", activa ? "true" : "false");
        document.getElementById(o.getAttribute("aria-controls")).hidden = !activa;
      });
    });
  });
})();

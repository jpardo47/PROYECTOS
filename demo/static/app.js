"use strict";
// Demo local de reportes técnicos. Sin dependencias. Todo el contenido del usuario se inserta como texto.

const app = document.getElementById("app");
let PLANTILLA = null;

// ---------- utilidades ----------
function el(etiqueta, atributos = {}, hijos = []) {
  const nodo = document.createElement(etiqueta);
  for (const [clave, valor] of Object.entries(atributos)) {
    if (valor === false || valor === null || valor === undefined) continue;
    if (clave === "texto") nodo.textContent = valor;
    else if (clave.startsWith("on")) nodo.addEventListener(clave.slice(2), valor);
    else nodo.setAttribute(clave, valor === true ? "" : valor);
  }
  for (const hijo of [].concat(hijos)) if (hijo) nodo.append(hijo);
  return nodo;
}

async function pedir(url, opciones = {}) {
  let respuesta;
  try {
    respuesta = await fetch(url, opciones);
  } catch (e) {
    throw { mensaje: "No se pudo conectar con el servidor local. Verifique que siga en ejecución." };
  }
  let cuerpo = null;
  try { cuerpo = await respuesta.json(); } catch (e) { /* respuesta sin JSON */ }
  if (!respuesta.ok) throw { mensaje: (cuerpo && cuerpo.error) || `Error ${respuesta.status}.`, errores: cuerpo && cuerpo.errores };
  return cuerpo;
}

function errorGeneral(mensaje) {
  return el("p", { class: "error-general", role: "alert", texto: mensaje });
}

function formatoValor(campo, valor) {
  if (campo.tipo === "casilla") return valor ? "Sí" : "No";
  if (valor === null || valor === undefined || valor === "") return "—";
  const texto = typeof valor === "number" ? valor.toLocaleString("es-CO") : String(valor);
  return campo.unidad ? `${texto} ${campo.unidad}` : texto;
}

// ---------- listado ----------
async function vistaListado() {
  const parametros = new URLSearchParams(location.hash.split("?")[1] || "");
  const q = el("input", { type: "search", id: "filtro-q", value: parametros.get("q") || "", placeholder: "Cliente o número", maxlength: 120 });
  const desde = el("input", { type: "date", id: "filtro-desde", value: parametros.get("desde") || "" });
  const hasta = el("input", { type: "date", id: "filtro-hasta", value: parametros.get("hasta") || "" });
  const resultados = el("div", { id: "resultados" }, el("p", { texto: "Cargando reportes…" }));
  const filtrar = (evento) => {
    evento.preventDefault();
    const p = new URLSearchParams();
    if (q.value.trim()) p.set("q", q.value.trim());
    if (desde.value) p.set("desde", desde.value);
    if (hasta.value) p.set("hasta", hasta.value);
    location.hash = "#/" + (p.toString() ? "?" + p : "");
  };
  app.replaceChildren(
    el("h1", { texto: "Reportes guardados" }),
    el("form", { class: "tarjeta filtros", onsubmit: filtrar }, [
      el("div", { class: "campo" }, [el("label", { for: "filtro-q", texto: "Buscar" }), q]),
      el("div", { class: "campo" }, [el("label", { for: "filtro-desde", texto: "Desde" }), desde]),
      el("div", { class: "campo" }, [el("label", { for: "filtro-hasta", texto: "Hasta" }), hasta]),
      el("button", { type: "submit", texto: "Filtrar" }),
    ]),
    resultados);
  try {
    const consulta = new URLSearchParams();
    for (const clave of ["q", "desde", "hasta"]) if (parametros.get(clave)) consulta.set(clave, parametros.get(clave));
    const { reportes } = await pedir("/api/reportes?" + consulta);
    if (!reportes.length) {
      resultados.replaceChildren(el("p", { class: "tarjeta", texto: "No hay reportes con esos criterios. Cree uno con «Nuevo reporte»." }));
      return;
    }
    resultados.replaceChildren(el("ul", { class: "lista" }, reportes.map((r) => el("li", {}, el("a", { href: `#/reporte/${r.id}` }, [
      el("span", { class: "numero", texto: `${r.numero} · ` }), el("span", { texto: r.cliente }),
      el("div", { class: "meta", texto: `${r.fecha_servicio} · ${r.tipo_equipo || "—"} · ${r.estado_final || "—"} · ${r.n_fotos} foto(s)` }),
    ])))));
  } catch (e) {
    resultados.replaceChildren(errorGeneral(e.mensaje));
  }
}

// ---------- formulario ----------
function controlCampo(campo) {
  const id = `campo-${campo.id}`;
  const comun = { id, name: campo.id, "aria-describedby": `error-${campo.id}` };
  if (campo.tipo === "casilla") {
    return el("div", { class: "campo" }, [
      el("label", { class: "casilla", for: id }, [el("input", { ...comun, type: "checkbox" }), el("span", { texto: campo.etiqueta })]),
      el("p", { class: "error", id: `error-${campo.id}`, "aria-live": "polite" }),
    ]);
  }
  let control;
  if (campo.tipo === "opcion") {
    control = el("select", comun, [el("option", { value: "", texto: "Seleccione…" }), ...campo.opciones.map((o) => el("option", { value: o, texto: o }))]);
  } else if (campo.tipo === "textolargo") {
    control = el("textarea", { ...comun, maxlength: campo.max, rows: 4 });
  } else if (campo.tipo === "fecha") {
    control = el("input", { ...comun, type: "date", max: new Date(Date.now() + 864e5).toISOString().slice(0, 10) });
  } else if (campo.tipo === "entero" || campo.tipo === "decimal") {
    control = el("input", { ...comun, type: "number", inputmode: "decimal", min: campo.min, max: campo.max, step: campo.tipo === "entero" ? 1 : "any" });
  } else {
    control = el("input", { ...comun, type: "text", maxlength: campo.max, autocomplete: "off" });
  }
  if (campo.obligatorio) control.setAttribute("aria-required", "true");
  const ayuda = campo.unidad ? `Unidad: ${campo.unidad}` + (campo.min !== undefined ? ` (de ${campo.min} a ${campo.max})` : "") :
    (campo.max && campo.tipo !== "fecha" ? `Máximo ${campo.max} caracteres` : "");
  return el("div", { class: "campo" }, [
    el("label", { for: id }, [campo.etiqueta, campo.obligatorio ? el("span", { class: "oblig", texto: " *" }) : null,
      ayuda ? el("span", { class: "ayuda", texto: ayuda }) : null]),
    control,
    el("p", { class: "error", id: `error-${campo.id}`, "aria-live": "polite" }),
  ]);
}

function blobABase64(blob) {
  return new Promise((resolver, rechazar) => {
    const lector = new FileReader();
    lector.onload = () => resolver(String(lector.result).split(",")[1]);
    lector.onerror = () => rechazar(new Error("lectura"));
    lector.readAsDataURL(blob);
  });
}

async function procesarFoto(archivo, limites) {
  if (!limites.origen_tipos.includes(archivo.type)) throw new Error(`«${archivo.name}»: formato no admitido. Use JPEG o PNG.`);
  if (archivo.size > limites.origen_bytes_max) throw new Error(`«${archivo.name}» supera 15 MB.`);
  const url = URL.createObjectURL(archivo);
  try {
    const imagen = new Image();
    imagen.src = url;
    try { await imagen.decode(); } catch (e) { throw new Error(`«${archivo.name}» no se pudo leer como imagen.`); }
    const escala = Math.min(1, limites.lado_max / Math.max(imagen.naturalWidth, imagen.naturalHeight));
    const ancho = Math.max(1, Math.round(imagen.naturalWidth * escala));
    const alto = Math.max(1, Math.round(imagen.naturalHeight * escala));
    const lienzo = document.createElement("canvas");
    lienzo.width = ancho; lienzo.height = alto;
    const ctx = lienzo.getContext("2d");
    ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, ancho, alto);   // fondo blanco para PNG con transparencia
    ctx.drawImage(imagen, 0, 0, ancho, alto);
    let calidad = 0.85, blob = null;
    do {
      blob = await new Promise((r) => lienzo.toBlob(r, "image/jpeg", calidad));
      calidad -= 0.15;
    } while (blob && blob.size > limites.bytes_max && calidad > 0.3);
    if (!blob || blob.size > limites.bytes_max) throw new Error(`«${archivo.name}» no se pudo reducir por debajo de 2 MB.`);
    return { nombre: archivo.name.slice(0, 100), datos: await blobABase64(blob), vista: URL.createObjectURL(blob) };
  } finally {
    URL.revokeObjectURL(url);
  }
}

function vistaNuevo() {
  const limites = PLANTILLA.fotos;
  const fotos = [];
  const general = el("div", { id: "mensaje-general" });
  const miniaturas = el("div", { class: "miniaturas", id: "miniaturas" });
  const contador = el("span", { class: "contador", id: "contador-fotos" });
  const errorFotos = el("p", { class: "error", id: "error-fotos", "aria-live": "polite" });
  const entradaFotos = el("input", { type: "file", id: "campo-fotos", accept: limites.origen_tipos.join(","), multiple: true });

  const pintarFotos = () => {
    contador.textContent = `${fotos.length} de ${limites.maximo} fotografías`;
    miniaturas.replaceChildren(...fotos.map((f, i) => el("div", { class: "miniatura" }, [
      el("img", { src: f.vista, alt: `Vista previa de ${f.nombre}` }),
      el("span", { texto: f.nombre }),
      el("button", { type: "button", texto: "Quitar", onclick: () => { URL.revokeObjectURL(f.vista); fotos.splice(i, 1); pintarFotos(); } }),
    ])));
  };

  entradaFotos.addEventListener("change", async () => {
    errorFotos.textContent = "";
    const elegidos = Array.from(entradaFotos.files);
    entradaFotos.value = "";
    const problemas = [];
    for (const archivo of elegidos) {
      if (fotos.length >= limites.maximo) { problemas.push(`Máximo ${limites.maximo} fotografías por reporte.`); break; }
      try { fotos.push(await procesarFoto(archivo, limites)); } catch (e) { problemas.push(e.message); }
    }
    errorFotos.textContent = problemas.join(" ");
    pintarFotos();
  });

  const guardar = async (evento) => {
    evento.preventDefault();
    const boton = evento.target.querySelector("button[type=submit]");
    general.replaceChildren();
    for (const nodo of app.querySelectorAll(".error")) if (nodo.id !== "error-fotos" || !nodo.textContent) nodo.textContent = "";
    for (const nodo of app.querySelectorAll(".invalido")) nodo.classList.remove("invalido");
    const campos = {};
    for (const s of PLANTILLA.secciones) for (const c of s.campos) {
      const control = document.getElementById(`campo-${c.id}`);
      campos[c.id] = c.tipo === "casilla" ? control.checked : control.value;
    }
    boton.disabled = true; boton.textContent = "Guardando…";
    try {
      const creado = await pedir("/api/reportes", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ campos, fotos: fotos.map((f) => ({ nombre: f.nombre, datos: f.datos })) }),
      });
      fotos.forEach((f) => URL.revokeObjectURL(f.vista));
      location.hash = `#/reporte/${creado.id}?nuevo=1`;
    } catch (e) {
      general.replaceChildren(errorGeneral(e.mensaje));
      let primero = null;
      for (const [campo, mensaje] of Object.entries(e.errores || {})) {
        const destino = document.getElementById(`error-${campo}`);
        if (destino) destino.textContent = mensaje;
        const control = document.getElementById(`campo-${campo}`);
        if (control) { control.classList.add("invalido"); control.setAttribute("aria-invalid", "true"); primero = primero || control; }
      }
      (primero || general).scrollIntoView({ behavior: "smooth", block: "center" });
      if (primero) primero.focus({ preventScroll: true });
    } finally {
      boton.disabled = false; boton.textContent = "Guardar reporte";
    }
  };

  app.replaceChildren(
    el("h1", { texto: PLANTILLA.titulo }),
    el("p", { class: "contador", texto: `${PLANTILLA.empresa}. Los campos con * son obligatorios.` }),
    general,
    el("form", { id: "formulario", novalidate: true, onsubmit: guardar }, [
      ...PLANTILLA.secciones.map((s) => el("section", { class: "tarjeta" }, [el("h2", { texto: s.titulo }), ...s.campos.map(controlCampo)])),
      el("section", { class: "tarjeta" }, [
        el("h2", { texto: "Fotografías" }),
        el("div", { class: "campo" }, [
          el("label", { for: "campo-fotos" }, ["Agregar fotografías",
            el("span", { class: "ayuda", texto: `JPEG o PNG, hasta 15 MB cada una y ${limites.maximo} por reporte. Se reducen a ${limites.lado_max} px en el navegador.` })]),
          entradaFotos, contador, errorFotos, miniaturas,
        ]),
      ]),
      el("div", { class: "acciones" }, [el("button", { type: "submit", texto: "Guardar reporte" }), el("a", { class: "boton secundario", href: "#/", texto: "Cancelar" })]),
    ]));
  pintarFotos();
}

// ---------- detalle ----------
async function vistaDetalle(id, nuevo) {
  app.replaceChildren(el("p", { texto: "Cargando reporte…" }));
  try {
    const r = await pedir(`/api/reportes/${id}`);
    const bloques = PLANTILLA.secciones.map((s) => el("section", { class: "tarjeta" }, [
      el("h2", { texto: s.titulo }),
      el("dl", { class: "detalle" }, s.campos.flatMap((c) => [el("dt", { texto: c.etiqueta }), el("dd", { texto: formatoValor(c, r.campos[c.id]) })])),
    ]));
    const galeria = r.fotos.length
      ? el("div", { class: "galeria" }, r.fotos.map((f) => el("figure", {}, [
          el("img", { src: f.url, alt: `Fotografía ${f.orden}: ${f.nombre}`, loading: "lazy" }),
          el("figcaption", { texto: `Foto ${f.orden} — ${f.nombre}` })])))
      : el("p", { texto: "Este reporte no tiene fotografías." });
    app.replaceChildren(
      nuevo ? el("p", { class: "exito", role: "status", texto: `Reporte ${r.numero} guardado correctamente.` }) : "",
      el("h1", { id: "titulo-reporte", texto: `Reporte ${r.numero}` }),
      el("p", { class: "contador", texto: `Creado: ${r.creado}` }),
      el("div", { class: "acciones tarjeta" }, [
        el("a", { class: "boton", id: "enlace-pdf", href: r.pdf_url, target: "_blank", rel: "noopener", texto: "Generar PDF (borrador)" }),
        el("a", { class: "boton secundario", href: "#/", texto: "Volver al listado" }),
      ]),
      ...bloques,
      el("section", { class: "tarjeta" }, [el("h2", { texto: `Fotografías (${r.fotos.length})` }), galeria]));
  } catch (e) {
    app.replaceChildren(errorGeneral(e.mensaje), el("a", { class: "boton secundario", href: "#/", texto: "Volver al listado" }));
  }
}

// ---------- enrutador ----------
async function enrutar() {
  const [ruta, consulta] = location.hash.replace(/^#/, "").split("?");
  window.scrollTo(0, 0);
  if (ruta === "/nuevo") return vistaNuevo();
  const m = /^\/reporte\/(\d+)$/.exec(ruta || "");
  if (m) return vistaDetalle(m[1], new URLSearchParams(consulta || "").has("nuevo"));
  return vistaListado();
}

(async function iniciar() {
  try {
    PLANTILLA = await pedir("/api/plantilla");
  } catch (e) {
    app.replaceChildren(errorGeneral(e.mensaje));
    return;
  }
  window.addEventListener("hashchange", enrutar);
  enrutar();
})();

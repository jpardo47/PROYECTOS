// Prueba de extremo a extremo en Chromium con vista móvil (iPhone 13), usando Playwright ya instalado.
// Uso, desde la raíz del repositorio:  node demo/tests/e2e_navegador.js [carpeta_de_salida]
// Arranca el servidor con una carpeta de datos temporal, recorre el flujo completo, reinicia el
// servidor para comprobar la persistencia y guarda capturas y el PDF en la carpeta de salida.
const { chromium, devices } = require("playwright");
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..", "..");
const SALIDA = path.resolve(process.argv[2] || path.join(os.tmpdir(), "demo-e2e"));
const DATOS = fs.mkdtempSync(path.join(os.tmpdir(), "demo-datos-"));
const PUERTO = 8765;
const BASE = `http://127.0.0.1:${PUERTO}`;
const EJEMPLOS = path.join(RAIZ, "demo", "ejemplos");
fs.mkdirSync(SALIDA, { recursive: true });

let servidor = null;
const pasos = [];
function ok(paso) { pasos.push(paso); console.log(`  ✔ ${paso}`); }
function exigir(condicion, mensaje) { if (!condicion) throw new Error(mensaje); }

async function arrancar() {
  servidor = spawn("python3", ["-m", "demo", "--puerto", String(PUERTO), "--datos", DATOS], { cwd: RAIZ, stdio: ["ignore", "pipe", "pipe"] });
  servidor.stderr.on("data", () => {});
  for (let i = 0; i < 100; i++) {
    try { if ((await fetch(`${BASE}/api/plantilla`)).ok) return; } catch (e) { /* aún no escucha */ }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("El servidor no arrancó");
}
async function detener() {
  if (!servidor) return;
  const proceso = servidor; servidor = null;
  await new Promise((r) => { proceso.once("exit", r); proceso.kill("SIGTERM"); });
}

(async () => {
  const navegador = await chromium.launch();
  const erroresConsola = [];
  try {
    await arrancar();
    const contexto = await navegador.newContext({ ...devices["iPhone 13"], locale: "es-CO" });
    const pagina = await contexto.newPage();
    pagina.on("pageerror", (e) => erroresConsola.push(String(e)));
    pagina.on("console", (m) => { if (m.type() === "error" && !/status of 400/.test(m.text())) erroresConsola.push(m.text()); });

    // 1. Formulario vacío: errores comprensibles
    await pagina.goto(`${BASE}/#/nuevo`);
    await pagina.waitForSelector("#formulario");
    await pagina.click("button[type=submit]");
    await pagina.waitForSelector(".error-general");
    exigir((await pagina.textContent("#error-cliente")) === "Este campo es obligatorio.", "falta el error de cliente");
    exigir((await pagina.textContent(".error-general")).includes("Revise los campos marcados"), "falta el error general");
    await pagina.screenshot({ path: path.join(SALIDA, "1-errores-movil.png"), fullPage: false });
    ok("formulario vacío muestra errores por campo y mensaje general");

    // 2. Archivo no válido rechazado en el navegador
    await pagina.setInputFiles("#campo-fotos", { name: "nota.txt", mimeType: "text/plain", buffer: Buffer.from("no es una imagen") });
    await pagina.waitForFunction(() => document.getElementById("error-fotos").textContent.includes("formato no admitido"));
    ok("archivo de texto rechazado con mensaje «formato no admitido»");

    // 3. Completar el reporte y adjuntar JPEG + PNG (el PNG se convierte a JPEG en el navegador)
    const hoy = new Date().toISOString().slice(0, 10);
    await pagina.fill("#campo-fecha_servicio", hoy);
    await pagina.fill("#campo-cliente", "Cliente Ficticio E2E");
    await pagina.fill("#campo-tecnico", "Técnico de Prueba");
    await pagina.selectOption("#campo-tipo_servicio", "Preventivo");
    await pagina.selectOption("#campo-tipo_equipo", "Cassette");
    await pagina.fill("#campo-serial", "E2E-0001");
    await pagina.fill("#campo-voltaje_v", "221.4");
    await pagina.check("#campo-limpieza_filtros");
    await pagina.selectOption("#campo-estado_final", "Operativo con observaciones");
    await pagina.fill("#campo-observaciones", "Prueba de extremo a extremo con fotografías JPEG y PNG.");
    await pagina.setInputFiles("#campo-fotos", [path.join(EJEMPLOS, "foto_ejemplo_1.jpg"), path.join(EJEMPLOS, "foto_ejemplo.png")]);
    await pagina.waitForFunction(() => document.querySelectorAll(".miniatura").length === 2);
    exigir((await pagina.textContent("#contador-fotos")).startsWith("2 de 10"), "contador de fotos incorrecto");
    const desborde = await pagina.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    exigir(desborde <= 0, `la vista móvil tiene desplazamiento horizontal (${desborde}px)`);
    await pagina.screenshot({ path: path.join(SALIDA, "2-formulario-movil.png"), fullPage: true });
    ok("formulario completado en vista móvil, 2 fotos procesadas, sin desplazamiento horizontal");

    // 4. Guardar y ver el detalle
    await pagina.click("button[type=submit]");
    await pagina.waitForSelector("#titulo-reporte");
    exigir((await pagina.textContent("#titulo-reporte")) === "Reporte RT-0001", "número de reporte inesperado");
    exigir((await pagina.textContent(".exito")).includes("guardado correctamente"), "falta el mensaje de éxito");
    await pagina.waitForFunction(() => [...document.querySelectorAll(".galeria img")].every((i) => i.complete && i.naturalWidth > 0));
    exigir((await pagina.locator(".galeria img").count()) === 2, "el detalle no muestra 2 fotos");
    await pagina.screenshot({ path: path.join(SALIDA, "3-detalle-movil.png"), fullPage: true });
    ok("reporte guardado; el detalle muestra RT-0001 y las 2 fotos");

    // 5. PDF
    const enlace = await pagina.getAttribute("#enlace-pdf", "href");
    const respuesta = await pagina.request.get(BASE + enlace);
    const pdf = await respuesta.body();
    exigir(respuesta.status() === 200 && respuesta.headers()["content-type"] === "application/pdf", "el PDF no se generó");
    exigir(pdf.subarray(0, 5).toString() === "%PDF-", "el contenido no es un PDF");
    fs.writeFileSync(path.join(SALIDA, "borrador-RT-0001.pdf"), pdf);
    ok(`PDF generado (${pdf.length} bytes) y guardado para revisión`);

    // 6. Listado y búsqueda
    await pagina.goto(`${BASE}/#/`);
    await pagina.waitForSelector(".lista li");
    exigir((await pagina.textContent(".lista")).includes("RT-0001"), "el listado no muestra el reporte");
    await pagina.fill("#filtro-q", "no-coincide");
    await pagina.click(".filtros button");
    await pagina.waitForFunction(() => document.getElementById("resultados").textContent.includes("No hay reportes"));
    ok("listado muestra el reporte y la búsqueda sin coincidencias informa correctamente");

    // 7. Persistencia tras reiniciar el servidor
    await detener();
    await arrancar();
    await pagina.goto(`${BASE}/#/`);
    await pagina.waitForSelector(".lista li");
    await pagina.click(".lista li a");
    await pagina.waitForSelector("#titulo-reporte");
    exigir((await pagina.textContent("#titulo-reporte")) === "Reporte RT-0001", "el reporte no sobrevivió al reinicio");
    await pagina.waitForFunction(() => [...document.querySelectorAll(".galeria img")].every((i) => i.complete && i.naturalWidth > 0));
    ok("tras reiniciar el servidor, el reporte y sus fotos siguen disponibles");

    // 8. Vista de escritorio del listado
    const escritorio = await navegador.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1, locale: "es-CO" });
    await escritorio.goto(`${BASE}/#/`);
    await escritorio.waitForSelector(".lista li");
    await escritorio.screenshot({ path: path.join(SALIDA, "4-listado-escritorio.png") });
    ok("listado en escritorio capturado");

    exigir(erroresConsola.length === 0, `errores de JavaScript en consola: ${erroresConsola.join(" | ")}`);
    ok("sin errores de JavaScript en la consola");
    console.log(`\nE2E OK: ${pasos.length} comprobaciones. Salida: ${SALIDA}`);
  } catch (e) {
    console.error(`\nE2E FALLÓ: ${e.message}`);
    process.exitCode = 1;
  } finally {
    await navegador.close();
    await detener();
    fs.rmSync(DATOS, { recursive: true, force: true });
  }
})();

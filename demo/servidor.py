"""Servidor HTTP local de la demostración (solo biblioteca estándar).

Escucha únicamente en 127.0.0.1 y rechaza solicitudes cuyo encabezado Host no sea local, para no exponer
datos sin protección. La demo no tiene usuarios ni roles.
"""
import argparse
import datetime
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from demo.almacen import Almacen
from demo.pdf import generar_pdf
from demo.plantilla import PLANTILLA, validar_campos, validar_fotos

RAIZ = Path(__file__).resolve().parent
ESTATICOS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/static/app.css": ("app.css", "text/css; charset=utf-8"),
}
CUERPO_MAX = 30_000_000
CSP = ("default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; "
       "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
RUTA_REPORTE = re.compile(r"^/api/reportes/(\d{1,9})$")
RUTA_FOTO = re.compile(r"^/api/reportes/(\d{1,9})/fotos/(\d{1,2})$")
RUTA_PDF = re.compile(r"^/api/reportes/(\d{1,9})/pdf$")


class Manejador(BaseHTTPRequestHandler):
    server_version = "DemoReportes/1.0"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    # ---------- utilidades ----------
    def log_message(self, formato, *args):
        if not self.server.silencioso:
            sys.stderr.write(f"[{self.log_date_time_string()}] {formato % args}\n")

    def _enviar(self, codigo, cuerpo, tipo, extra=None):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cache-Control", "no-store")
        for clave, valor in (extra or {}).items():
            self.send_header(clave, valor)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)

    def _json(self, codigo, objeto):
        self._enviar(codigo, json.dumps(objeto, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, codigo, mensaje, errores=None):
        cuerpo = {"error": mensaje}
        if errores:
            cuerpo["errores"] = errores
        self._json(codigo, cuerpo)

    def _host_local(self):
        puerto = self.server.server_address[1]
        return self.headers.get("Host", "") in {f"127.0.0.1:{puerto}", f"localhost:{puerto}"}

    # ---------- métodos HTTP ----------
    def do_GET(self):
        if not self._host_local():
            return self._error(403, "Acceso permitido solo desde este equipo (127.0.0.1).")
        url = urlsplit(self.path)
        ruta = url.path
        try:
            if ruta in ESTATICOS:
                archivo, tipo = ESTATICOS[ruta]
                return self._enviar(200, (RAIZ / "static" / archivo).read_bytes(), tipo)
            if ruta == "/api/plantilla":
                return self._json(200, PLANTILLA)
            if ruta == "/api/reportes":
                return self._listar(parse_qs(url.query))
            if m := RUTA_REPORTE.match(ruta):
                reporte = self.server.almacen.obtener(int(m[1]))
                if reporte is None:
                    return self._error(404, "No existe el reporte solicitado.")
                reporte["pdf_url"] = f"/api/reportes/{reporte['id']}/pdf"
                for f in reporte["fotos"]:
                    f["url"] = f"/api/reportes/{reporte['id']}/fotos/{f['orden']}"
                return self._json(200, reporte)
            if m := RUTA_FOTO.match(ruta):
                datos = self.server.almacen.foto(int(m[1]), int(m[2]))
                if datos is None:
                    return self._error(404, "No existe la fotografía solicitada.")
                return self._enviar(200, datos, "image/jpeg")
            if m := RUTA_PDF.match(ruta):
                return self._pdf(int(m[1]))
            return self._error(404, "La dirección solicitada no existe.")
        except Exception as e:  # error inesperado: mensaje claro, sin exponer detalles internos
            self.log_message("Error interno: %r", e)
            return self._error(500, "Ocurrió un error interno. Revise la consola del servidor.")

    do_HEAD = do_GET

    def do_POST(self):
        # Si se rechaza sin leer el cuerpo, no se reutiliza la conexión (evita interpretar ese cuerpo como otra solicitud).
        self.close_connection = True
        if not self._host_local():
            return self._error(403, "Acceso permitido solo desde este equipo (127.0.0.1).")
        if urlsplit(self.path).path != "/api/reportes":
            return self._error(404, "La dirección solicitada no existe.")
        if not self.headers.get("Content-Type", "").lower().startswith("application/json"):
            return self._error(415, "El contenido debe enviarse en formato JSON.")
        try:
            longitud = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._error(411, "Falta indicar el tamaño de la solicitud.")
        if longitud > CUERPO_MAX:
            self.close_connection = True
            return self._error(413, "La solicitud supera el tamaño máximo permitido (30 MB).")
        try:
            cuerpo = json.loads(self.rfile.read(longitud).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._error(400, "El contenido no es JSON válido.")
        if not isinstance(cuerpo, dict):
            return self._error(400, "El contenido no tiene el formato esperado.")
        campos, errores = validar_campos(cuerpo.get("campos"))
        fotos, error_fotos = validar_fotos(cuerpo.get("fotos"))
        if error_fotos:
            errores["fotos"] = error_fotos
        if errores:
            return self._error(400, "Revise los campos marcados.", errores)
        try:
            creado = self.server.almacen.crear(PLANTILLA["id"], campos, fotos)
        except Exception as e:
            self.log_message("Error al guardar: %r", e)
            return self._error(500, "No se pudo guardar el reporte. Revise la consola del servidor.")
        return self._json(201, creado)

    def do_PUT(self):
        self._error(405, "Método no permitido.")

    do_DELETE = do_PATCH = do_PUT

    # ---------- operaciones ----------
    def _listar(self, consulta):
        texto = (consulta.get("q", [""])[0] or "").strip()[:120]
        fechas = {}
        for clave in ("desde", "hasta"):
            valor = (consulta.get(clave, [""])[0] or "").strip()
            if valor:
                try:
                    fechas[clave] = datetime.date.fromisoformat(valor).isoformat()
                except ValueError:
                    return self._error(400, f"La fecha «{clave}» no es válida (AAAA-MM-DD).")
        return self._json(200, {"reportes": self.server.almacen.listar(texto or None, fechas.get("desde"), fechas.get("hasta"))})

    def _pdf(self, rid):
        reporte = self.server.almacen.obtener(rid)
        if reporte is None:
            return self._error(404, "No existe el reporte solicitado.")
        datos = generar_pdf(reporte, PLANTILLA, self.server.almacen.fotos_completas(rid))
        nombre = f"borrador-{reporte['numero']}.pdf"
        return self._enviar(200, datos, "application/pdf", {"Content-Disposition": f'inline; filename="{nombre}"'})


class ServidorDemo(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, carpeta_datos, puerto=8000, silencioso=False):
        self.almacen = Almacen(Path(carpeta_datos) / "reportes.sqlite3")
        self.silencioso = silencioso
        super().__init__(("127.0.0.1", puerto), Manejador)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m demo", description="Demostración local de reportes técnicos.")
    parser.add_argument("--puerto", type=int, default=8000, help="puerto local (predeterminado: 8000)")
    parser.add_argument("--datos", default=str(RAIZ / "datos"), help="carpeta de la base de datos local")
    parser.add_argument("--datos-ejemplo", action="store_true", help="carga reportes ficticios si la base está vacía")
    args = parser.parse_args(argv)
    servidor = ServidorDemo(args.datos, args.puerto)
    if args.datos_ejemplo:
        from demo.ejemplo import cargar_ejemplos
        creados = cargar_ejemplos(servidor.almacen)
        print(f"Datos de ejemplo: {creados} reporte(s) ficticio(s) cargado(s)." if creados else
              "Datos de ejemplo: la base ya tenía reportes; no se cargó nada.")
    print(f"Demo disponible en http://127.0.0.1:{servidor.server_address[1]}/  (solo este equipo; Ctrl+C para salir)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()

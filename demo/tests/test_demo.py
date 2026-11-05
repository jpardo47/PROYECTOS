"""Pruebas de la demo: servidor real en un puerto efímero y carpeta de datos temporal.

Ejecutar desde la raíz del repositorio:  python3 -m unittest discover -s demo/tests -t . -v
"""
import base64
import datetime
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from demo.jpeg import inspeccionar
from demo.servidor import ServidorDemo

EJEMPLOS = Path(__file__).resolve().parent.parent / "ejemplos"
JPEG = (EJEMPLOS / "foto_ejemplo_1.jpg").read_bytes()
JPEG2 = (EJEMPLOS / "foto_ejemplo_2.jpg").read_bytes()
PNG = (EJEMPLOS / "foto_ejemplo.png").read_bytes()

try:
    import pypdfium2  # lector de PDF independiente, si está instalado en el sistema
except ImportError:  # pragma: no cover
    pypdfium2 = None


def b64(datos):
    return base64.b64encode(datos).decode()


def campos_validos(**cambios):
    campos = {
        "fecha_servicio": datetime.date.today().isoformat(), "cliente": "Cliente Ficticio de Prueba",
        "sede": "Sede de prueba", "tecnico": "Técnico de Prueba", "tipo_servicio": "Preventivo",
        "tipo_equipo": "Split de muro", "marca": "Marca X", "modelo": "M-1", "serial": "PRUEBA-001",
        "ubicacion_equipo": "Oficina", "capacidad_btu": "12000", "voltaje_v": "220,5", "corriente_a": 4.2,
        "presion_psi": "", "temp_suministro_c": "13", "limpieza_filtros": True, "limpieza_serpentines": False,
        "revision_drenaje": True, "revision_electrica": True, "estado_final": "Operativo",
        "observaciones": "Limpieza realizada y equipo operativo. Ñandú, tildes: áéíóú.", "recomendaciones": "",
    }
    campos.update(cambios)
    return campos


class ServidorEnPrueba:
    def __init__(self, carpeta):
        self.servidor = ServidorDemo(carpeta, puerto=0, silencioso=True)
        self.puerto = self.servidor.server_address[1]
        self.hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.hilo.start()

    def pedir(self, metodo, ruta, cuerpo=None, encabezados=None):
        con = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=20)
        enc = {"Host": f"127.0.0.1:{self.puerto}"}
        if isinstance(cuerpo, (dict, list)):
            cuerpo = json.dumps(cuerpo).encode()
            enc["Content-Type"] = "application/json"
        enc.update(encabezados or {})
        con.request(metodo, ruta, body=cuerpo, headers=enc)
        r = con.getresponse()
        datos = r.read()
        tipo = r.getheader("Content-Type", "")
        con.close()
        return r.status, (json.loads(datos) if tipo.startswith("application/json") else datos), tipo

    def detener(self):
        self.servidor.shutdown()
        self.servidor.server_close()


class BaseDemo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = self._tmp.name
        self.srv = ServidorEnPrueba(self.carpeta)

    def tearDown(self):
        self.srv.detener()
        self._tmp.cleanup()

    def crear(self, campos=None, fotos=None):
        cuerpo = {"campos": campos or campos_validos(),
                  "fotos": fotos if fotos is not None else [{"nombre": "antes.jpg", "datos": b64(JPEG)}]}
        return self.srv.pedir("POST", "/api/reportes", cuerpo)


class CrearYConsultar(BaseDemo):
    def test_crear_y_recuperar_reporte(self):
        estado, cuerpo, _ = self.crear(fotos=[{"nombre": "antes.jpg", "datos": b64(JPEG)},
                                              {"nombre": "despues.jpg", "datos": b64(JPEG2)}])
        self.assertEqual(estado, 201, cuerpo)
        self.assertEqual(cuerpo["numero"], "RT-0001")
        estado, reporte, _ = self.srv.pedir("GET", f"/api/reportes/{cuerpo['id']}")
        self.assertEqual(estado, 200)
        self.assertEqual(reporte["campos"]["cliente"], "Cliente Ficticio de Prueba")
        self.assertEqual(reporte["campos"]["capacidad_btu"], 12000)
        self.assertEqual(reporte["campos"]["voltaje_v"], 220.5)        # coma decimal aceptada
        self.assertIsNone(reporte["campos"]["presion_psi"])             # opcional vacío
        self.assertIs(reporte["campos"]["limpieza_serpentines"], False)
        self.assertEqual([f["nombre"] for f in reporte["fotos"]], ["antes.jpg", "despues.jpg"])
        estado, foto, tipo = self.srv.pedir("GET", reporte["fotos"][1]["url"])
        self.assertEqual((estado, tipo), (200, "image/jpeg"))
        self.assertEqual(foto, JPEG2)                                   # la foto se guarda sin alterarse

    def test_listado_y_filtros(self):
        self.crear(campos_validos(cliente="Cliente Uno"))
        ayer = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        self.crear(campos_validos(cliente="Cliente Dos", fecha_servicio=ayer))
        _, todos, _ = self.srv.pedir("GET", "/api/reportes")
        self.assertEqual(len(todos["reportes"]), 2)
        _, filtrado, _ = self.srv.pedir("GET", "/api/reportes?q=dos")
        self.assertEqual([r["cliente"] for r in filtrado["reportes"]], ["Cliente Dos"])
        _, por_fecha, _ = self.srv.pedir("GET", f"/api/reportes?desde={datetime.date.today().isoformat()}")
        self.assertEqual([r["cliente"] for r in por_fecha["reportes"]], ["Cliente Uno"])
        estado, cuerpo, _ = self.srv.pedir("GET", "/api/reportes?desde=05-11-2026")
        self.assertEqual(estado, 400)
        self.assertIn("no es válida", cuerpo["error"])

    def test_interfaz_y_plantilla(self):
        estado, html, tipo = self.srv.pedir("GET", "/")
        self.assertEqual(estado, 200)
        self.assertIn("text/html", tipo)
        self.assertIn(b"/static/app.js", html)
        _, plantilla, _ = self.srv.pedir("GET", "/api/plantilla")
        campos = [c for s in plantilla["secciones"] for c in s["campos"]]
        self.assertLessEqual(len(campos), 25)
        self.assertEqual(plantilla["fotos"]["maximo"], 10)


class Validaciones(BaseDemo):
    def errores_de(self, campos=None, fotos=None):
        estado, cuerpo, _ = self.crear(campos, fotos)
        self.assertEqual(estado, 400, cuerpo)
        self.assertEqual(cuerpo["error"], "Revise los campos marcados.")
        return cuerpo["errores"]

    def test_rechaza_campos_invalidos(self):
        manana2 = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        errores = self.errores_de(campos_validos(
            cliente="", tecnico="X", tipo_servicio="Otro inventado", serial="#$%", capacidad_btu="12.5",
            voltaje_v="900", corriente_a="abc", fecha_servicio=manana2, observaciones="a" * 2001))
        self.assertEqual(errores["cliente"], "Este campo es obligatorio.")
        self.assertEqual(errores["tecnico"], "Debe tener al menos 2 caracteres.")
        self.assertEqual(errores["tipo_servicio"], "Seleccione una opción de la lista.")
        self.assertIn("Use solo letras", errores["serial"])
        self.assertEqual(errores["capacidad_btu"], "Ingrese un número entero válido.")
        self.assertEqual(errores["voltaje_v"], "Debe estar entre 0 y 600 V.")
        self.assertEqual(errores["corriente_a"], "Ingrese un número válido.")
        self.assertEqual(errores["fecha_servicio"], "La fecha no puede ser posterior a hoy.")
        self.assertIn("Máximo 2000 caracteres", errores["observaciones"])
        _, lista, _ = self.srv.pedir("GET", "/api/reportes")
        self.assertEqual(lista["reportes"], [])                         # nada se guardó

    def test_rechaza_archivos_invalidos(self):
        casos = {
            "no es JPEG (PNG directo)": ([{"nombre": "x.png", "datos": b64(PNG)}], "no es una imagen JPEG válida"),
            "texto renombrado": ([{"nombre": "x.jpg", "datos": b64(b"hola, no soy una imagen")}], "no es una imagen JPEG válida"),
            "base64 inválido": ([{"nombre": "x.jpg", "datos": "%%%no-base64%%%"}], "no se pudo leer"),
            "más de 10": ([{"nombre": f"{i}.jpg", "datos": b64(JPEG)} for i in range(11)], "Máximo 10 fotografías"),
            "más de 2 MB": ([{"nombre": "g.jpg", "datos": b64(JPEG[:-2] + b"\x00" * 2_000_001 + b"\xff\xd9")}], "supera 2 MB"),
            "más de 1600 px": ([{"nombre": "g.jpg", "datos": b64(_cambiar_tamano(JPEG, 2400, 1800))}], "supera 1600 píxeles"),
            "formato inesperado": ("no-es-lista", "no tienen el formato esperado"),
        }
        for nombre, (fotos, esperado) in casos.items():
            with self.subTest(nombre):
                errores = self.errores_de(fotos=fotos)
                self.assertIn(esperado, errores["fotos"])

    def test_errores_de_solicitud_comprensibles(self):
        estado, cuerpo, _ = self.srv.pedir("POST", "/api/reportes", b"{mal json", {"Content-Type": "application/json"})
        self.assertEqual((estado, cuerpo["error"]), (400, "El contenido no es JSON válido."))
        estado, cuerpo, _ = self.srv.pedir("POST", "/api/reportes", b"campos=1", {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual((estado, cuerpo["error"]), (415, "El contenido debe enviarse en formato JSON."))
        estado, cuerpo, _ = self.srv.pedir("POST", "/api/reportes", b"{}", {"Content-Type": "application/json", "Content-Length": "40000000"})
        self.assertEqual(estado, 413)
        self.assertIn("30 MB", cuerpo["error"])
        estado, cuerpo, _ = self.srv.pedir("GET", "/api/reportes/999")
        self.assertEqual((estado, cuerpo["error"]), (404, "No existe el reporte solicitado."))
        estado, cuerpo, _ = self.srv.pedir("GET", "/no-existe")
        self.assertEqual(estado, 404)
        estado, cuerpo, _ = self.srv.pedir("GET", "/api/reportes", encabezados={"Host": "atacante.example:80"})
        self.assertEqual(estado, 403)
        self.assertIn("solo desde este equipo", cuerpo["error"])


class PdfYPersistencia(BaseDemo):
    def test_genera_pdf_borrador_legible(self):
        _, creado, _ = self.crear(fotos=[{"nombre": "antes.jpg", "datos": b64(JPEG)}, {"nombre": "despues.jpg", "datos": b64(JPEG2)}])
        estado, pdf, tipo = self.srv.pedir("GET", f"/api/reportes/{creado['id']}/pdf")
        self.assertEqual((estado, tipo), (200, "application/pdf"))
        self.assertTrue(pdf.startswith(b"%PDF-1.4"))
        self.assertTrue(pdf.rstrip().endswith(b"%%EOF"))
        if pypdfium2 is None:
            self.skipTest("pypdfium2 no está disponible: se comprobó solo la estructura del PDF")
        doc = pypdfium2.PdfDocument(pdf)
        texto = "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
        self.assertIn("BORRADOR PARA REVISIÓN", texto)
        self.assertIn("RT-0001", texto)
        self.assertIn("Cliente Ficticio de Prueba", texto)
        self.assertIn("Ñandú, tildes: áéíóú", texto)
        imagenes = sum(1 for i in range(len(doc)) for o in doc[i].get_objects() if o.type == pypdfium2.raw.FPDF_PAGEOBJ_IMAGE)
        self.assertEqual(imagenes, 2)

    def test_pdf_con_10_fotos_y_texto_largo_usa_varias_paginas(self):
        largo = ("Observación extensa de prueba con muchas palabras para forzar saltos de línea y de página. " * 20)[:2000]
        _, creado, _ = self.crear(campos_validos(observaciones=largo, recomendaciones=largo),
                                  [{"nombre": f"foto-{i}.jpg", "datos": b64(JPEG)} for i in range(10)])
        estado, pdf, _ = self.srv.pedir("GET", f"/api/reportes/{creado['id']}/pdf")
        self.assertEqual(estado, 200)
        if pypdfium2 is None:
            self.skipTest("pypdfium2 no está disponible")
        doc = pypdfium2.PdfDocument(pdf)
        self.assertGreaterEqual(len(doc), 3)
        ultima = doc[len(doc) - 1].get_textpage().get_text_range()
        self.assertIn(f"Página {len(doc)} de {len(doc)}", ultima)

    def test_datos_se_conservan_al_reiniciar(self):
        _, creado, _ = self.crear()
        self.srv.detener()
        self.srv = ServidorEnPrueba(self.carpeta)                       # nuevo proceso de servidor, misma carpeta
        estado, reporte, _ = self.srv.pedir("GET", f"/api/reportes/{creado['id']}")
        self.assertEqual(estado, 200)
        self.assertEqual(reporte["numero"], "RT-0001")
        _, foto, _ = self.srv.pedir("GET", reporte["fotos"][0]["url"])
        self.assertEqual(foto, JPEG)
        _, segundo, _ = self.crear()
        self.assertEqual(segundo["numero"], "RT-0002")                  # la numeración continúa


class SeguridadLocal(BaseDemo):
    def test_enlace_local_y_cabeceras(self):
        # El servidor se enlaza a la interfaz de bucle local, no a todas las interfaces.
        self.assertEqual(self.srv.servidor.server_address[0], "127.0.0.1")
        con = http.client.HTTPConnection("127.0.0.1", self.srv.puerto, timeout=10)
        con.request("GET", "/", headers={"Host": f"localhost:{self.srv.puerto}"})
        r = con.getresponse()
        r.read()
        con.close()
        self.assertEqual(r.status, 200)                                 # localhost:<puerto> también se acepta
        self.assertIn("default-src 'self'", r.getheader("Content-Security-Policy"))
        self.assertEqual(r.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(r.getheader("X-Frame-Options"), "DENY")


class InspectorJpeg(unittest.TestCase):
    def test_inspector(self):
        self.assertEqual(inspeccionar(JPEG), (800, 600, 3))
        self.assertIsNone(inspeccionar(PNG))
        self.assertIsNone(inspeccionar(JPEG[:-2]))                      # sin marcador final
        self.assertIsNone(inspeccionar(b""))


def _cambiar_tamano(jpeg, ancho, alto):
    """Reescribe las dimensiones declaradas en el encabezado SOF (para probar el límite de píxeles)."""
    datos = bytearray(jpeg)
    i = 2
    while i < len(datos):
        marcador, longitud = datos[i + 1], int.from_bytes(datos[i + 2:i + 4], "big")
        if marcador in (0xC0, 0xC1, 0xC2):
            datos[i + 5:i + 7] = alto.to_bytes(2, "big")
            datos[i + 7:i + 9] = ancho.to_bytes(2, "big")
            return bytes(datos)
        i += 2 + longitud
    raise ValueError("sin SOF")


if __name__ == "__main__":
    unittest.main()

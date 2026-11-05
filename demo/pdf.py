"""Generador de PDF mínimo (sin dependencias) para el borrador del reporte.

Usa las fuentes estándar Helvetica con codificación WinAnsi (admite tildes y ñ) e inserta las
fotografías JPEG tal cual mediante el filtro DCTDecode, sin recomprimirlas.
"""
import math

from demo.jpeg import inspeccionar

ANCHO, ALTO = 595.28, 841.89          # A4 en puntos
MARGEN = 40
ZONA_SUPERIOR = ALTO - 92              # debajo de la franja de borrador
ZONA_INFERIOR = 60                     # encima del pie de página
MARCA = "BORRADOR PARA REVISIÓN"

# Anchos de Helvetica (unidades /1000) para ASCII 32-126.
_ANCHOS = [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
           556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
           1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
           667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
           333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
           556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584]
_BASE = str.maketrans("áéíóúÁÉÍÓÚñÑüÜ", "aeiouAEIOUnNuU")


def ancho_texto(texto, tam, negrita=False):
    total = 0
    for ch in texto.translate(_BASE):
        o = ord(ch)
        total += _ANCHOS[o - 32] if 32 <= o <= 126 else 556
    return total * tam / 1000 * (1.08 if negrita else 1.0)


def partir(texto, tam, ancho_max, negrita=False):
    """Divide el texto en líneas que caben en `ancho_max`, respetando saltos de línea."""
    lineas = []
    for parrafo in (texto or "").split("\n"):
        actual = ""
        for palabra in parrafo.split(" "):
            prueba = f"{actual} {palabra}" if actual else palabra
            if ancho_texto(prueba, tam, negrita) <= ancho_max:
                actual = prueba
                continue
            if actual:
                lineas.append(actual)
            while ancho_texto(palabra, tam, negrita) > ancho_max:   # palabra más larga que la línea
                corte = len(palabra)
                while corte > 1 and ancho_texto(palabra[:corte], tam, negrita) > ancho_max:
                    corte -= 1
                lineas.append(palabra[:corte])
                palabra = palabra[corte:]
            actual = palabra
        lineas.append(actual)
    return lineas


def _cadena(texto):
    datos = str(texto).replace("\t", " ").replace("\r", "").encode("cp1252", errors="replace")
    return b"(" + datos.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


class _Pagina:
    def __init__(self):
        self.ops = []

    def texto(self, x, y, s, tam=10, negrita=False, gris=0.0):
        fuente = b"/F2" if negrita else b"/F1"
        self.ops.append(b"BT %b %.2f Tf %.3f g %.2f %.2f Td %b Tj ET" % (fuente, tam, gris, x, y, _cadena(s)))

    def rect(self, x, y, w, h, gris):
        self.ops.append(b"%.3f g %.2f %.2f %.2f %.2f re f" % (gris, x, y, w, h))

    def linea(self, x1, y1, x2, y2, gris=0.6, grosor=0.6):
        self.ops.append(b"%.3f G %.2f w %.2f %.2f m %.2f %.2f l S" % (gris, grosor, x1, y1, x2, y2))

    def imagen(self, nombre, x, y, w, h):
        self.ops.append(b"q %.2f 0 0 %.2f %.2f %.2f cm /%b Do Q" % (w, h, x, y, nombre.encode()))


class _Maquetador:
    def __init__(self):
        self.paginas = [_Pagina()]
        self.y = ZONA_SUPERIOR

    @property
    def pagina(self):
        return self.paginas[-1]

    def asegurar(self, alto):
        if self.y - alto < ZONA_INFERIOR:
            self.paginas.append(_Pagina())
            self.y = ZONA_SUPERIOR

    def parrafo(self, x, ancho, texto, tam=9.5, negrita=False, interlineado=1.35):
        for linea in partir(texto, tam, ancho, negrita):
            self.asegurar(tam * interlineado)
            self.y -= tam * interlineado
            self.pagina.texto(x, self.y, linea, tam, negrita)

    def titulo_seccion(self, texto):
        self.asegurar(40)
        self.y -= 22
        self.pagina.rect(MARGEN, self.y - 5, ANCHO - 2 * MARGEN, 19, 0.92)
        self.pagina.texto(MARGEN + 6, self.y, texto, 11, True)
        self.y -= 8

    def fila(self, etiqueta, valor):
        col = 165
        lineas = partir(valor, 9.5, ANCHO - 2 * MARGEN - col - 6)
        lineas_etq = partir(etiqueta, 9, col - 8, True)
        alto = max(len(lineas), len(lineas_etq)) * 13 + 4
        self.asegurar(alto)
        y0 = self.y
        for i, linea in enumerate(lineas_etq):
            self.pagina.texto(MARGEN + 6, y0 - 12 - 13 * i, linea, 9, True, 0.25)
        for i, linea in enumerate(lineas):
            self.pagina.texto(MARGEN + col, y0 - 12 - 13 * i, linea, 9.5)
        self.y = y0 - alto
        self.pagina.linea(MARGEN, self.y, ANCHO - MARGEN, self.y, 0.85, 0.4)


def _valor(campo, valor):
    if campo["tipo"] == "casilla":
        return "Sí" if valor else "No"
    if valor is None or valor == "":
        return "—"
    if campo["tipo"] == "decimal":
        texto = f"{valor:g}".replace(".", ",")
    elif campo["tipo"] == "entero":
        texto = f"{valor:,}".replace(",", ".")
    else:
        texto = str(valor)
    return f"{texto} {campo['unidad']}" if campo.get("unidad") else texto


def generar_pdf(reporte, plantilla, fotos):
    """Devuelve los bytes del PDF del reporte, marcado como borrador para revisión."""
    m = _Maquetador()
    p = m.pagina
    p.texto(MARGEN, m.y - 4, plantilla["titulo"], 15, True)
    m.y -= 22
    p.texto(MARGEN, m.y, plantilla["empresa"], 9.5, False, 0.3)
    m.y -= 15
    p.texto(MARGEN, m.y, f"Reporte N.º {reporte['numero']}  ·  Creado: {reporte['creado']}", 9.5, True)
    m.y -= 4

    campos = reporte["campos"]
    for seccion in plantilla["secciones"]:
        m.titulo_seccion(seccion["titulo"])
        for campo in seccion["campos"]:
            if campo["tipo"] == "textolargo":
                m.asegurar(30)
                m.y -= 14
                m.pagina.texto(MARGEN + 6, m.y, campo["etiqueta"], 9, True, 0.25)
                m.parrafo(MARGEN + 6, ANCHO - 2 * MARGEN - 12, _valor(campo, campos.get(campo["id"])))
                m.y -= 4
            else:
                m.fila(campo["etiqueta"], _valor(campo, campos.get(campo["id"])))

    imagenes = []
    if fotos:
        celda_w, celda_h, sep = (ANCHO - 2 * MARGEN - 14) / 2, 190, 14
        m.asegurar(celda_h + 70)            # el título nunca queda solo al final de una página
        m.titulo_seccion(f"Registro fotográfico ({len(fotos)})")
        for i, foto in enumerate(fotos):
            nombre = f"Im{i + 1}"
            imagenes.append((nombre, foto))
            if i % 2 == 0:
                m.asegurar(celda_h + 30)
                m.y -= celda_h + 8
            escala = min(celda_w / foto["ancho"], celda_h / foto["alto"])
            w, h = foto["ancho"] * escala, foto["alto"] * escala
            x0 = MARGEN + (i % 2) * (celda_w + sep)
            m.pagina.imagen(nombre, x0 + (celda_w - w) / 2, m.y + (celda_h - h), w, h)
            pie = f"Foto {foto['orden']} — {foto['nombre']}"
            m.pagina.texto(x0, m.y - 11, partir(pie, 8, celda_w)[0], 8, False, 0.3)
            if i % 2 == 1 or i == len(fotos) - 1:
                m.y -= 18

    m.titulo_seccion("Revisión y aprobación")
    m.parrafo(MARGEN + 6, ANCHO - 2 * MARGEN - 12,
              "Este documento es un borrador generado a partir de los datos y fotografías registrados. "
              "No tiene validez hasta que la empresa lo revise y lo apruebe.", 9)
    m.asegurar(60)
    m.y -= 40
    for x, etiqueta in ((MARGEN + 6, "Revisado por"), (MARGEN + 280, "Fecha y firma")):
        m.pagina.linea(x, m.y, x + 220, m.y, 0.4, 0.6)
        m.pagina.texto(x, m.y - 12, etiqueta, 8.5, False, 0.35)

    return _ensamblar(m.paginas, imagenes, reporte["numero"])


def _ensamblar(paginas, imagenes, numero):
    objetos = {}
    total = len(paginas)
    n_img = len(imagenes)
    # 1 catálogo, 2 páginas, 3-4 fuentes, 5 info, imágenes desde 6, luego (contenido, página) por cada página.
    primera_img = 6
    primera_pag = primera_img + n_img
    objetos[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    hijos = b" ".join(b"%d 0 R" % (primera_pag + 2 * i + 1) for i in range(total))
    objetos[2] = b"<< /Type /Pages /Kids [%b] /Count %d >>" % (hijos, total)
    objetos[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    objetos[4] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    objetos[5] = b"<< /Title %b /Producer (Demo local de reportes tecnicos) >>" % _cadena(f"Borrador {numero}")
    xobjetos = []
    for k, (nombre, foto) in enumerate(imagenes):
        info = inspeccionar(foto["jpeg"])
        espacio = b"/DeviceGray" if info and info[2] == 1 else b"/DeviceRGB"
        cabecera = (b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace %b "
                    b"/BitsPerComponent 8 /Filter /DCTDecode /Length %d >>" % (foto["ancho"], foto["alto"], espacio, len(foto["jpeg"])))
        objetos[primera_img + k] = cabecera + b"\nstream\n" + foto["jpeg"] + b"\nendstream"
        xobjetos.append(b"/%b %d 0 R" % (nombre.encode(), primera_img + k))
    recursos = b"<< /Font << /F1 3 0 R /F2 4 0 R >> /XObject << %b >> >>" % b" ".join(xobjetos)
    cos, sen = math.cos(math.radians(35)), math.sin(math.radians(35))
    tam_marca = 44
    w_marca = ancho_texto(MARCA, tam_marca, True)
    x_marca, y_marca = ANCHO / 2 - w_marca / 2 * cos, ALTO / 2 - w_marca / 2 * sen
    for i, pagina in enumerate(paginas):
        fondo = [b"q 0.9 g BT /F2 %d Tf %.4f %.4f %.4f %.4f %.2f %.2f Tm %b Tj ET Q"
                 % (tam_marca, cos, sen, -sen, cos, x_marca, y_marca, _cadena(MARCA))]
        franja = _Pagina()
        franja.rect(0, ALTO - 58, ANCHO, 58, 0.15)
        franja.texto(MARGEN, ALTO - 34, MARCA, 13, True, 1.0)
        franja.texto(MARGEN, ALTO - 49, "Documento no válido hasta su revisión y aprobación por la empresa.", 8.5, False, 0.85)
        franja.texto(MARGEN, 32, f"Demostración local con datos ficticios · Reporte {numero}", 8, False, 0.4)
        franja.texto(ANCHO - MARGEN - 70, 32, f"Página {i + 1} de {total}", 8, False, 0.4)
        flujo = b"\n".join(fondo + pagina.ops + franja.ops)
        objetos[primera_pag + 2 * i] = b"<< /Length %d >>\nstream\n" % len(flujo) + flujo + b"\nendstream"
        objetos[primera_pag + 2 * i + 1] = (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] "
                                            b"/Resources %b /Contents %d 0 R >>" % (ANCHO, ALTO, recursos, primera_pag + 2 * i))
    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    desplazamientos = {}
    for num in sorted(objetos):
        desplazamientos[num] = len(salida)
        salida += b"%d 0 obj\n" % num + objetos[num] + b"\nendobj\n"
    inicio_xref = len(salida)
    cantidad = max(objetos) + 1
    salida += b"xref\n0 %d\n0000000000 65535 f \n" % cantidad
    for num in range(1, cantidad):
        salida += b"%010d 00000 n \n" % desplazamientos[num]
    salida += b"trailer\n<< /Size %d /Root 1 0 R /Info 5 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (cantidad, inicio_xref)
    return bytes(salida)

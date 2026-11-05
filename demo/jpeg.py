"""Inspección mínima de archivos JPEG sin dependencias externas."""


def inspeccionar(datos):
    """Devuelve (ancho, alto, componentes) si `datos` es un JPEG con estructura válida; si no, None.

    Recorre los marcadores hasta el encabezado de cuadro (SOF0, SOF1 o SOF2) y exige el marcador final (EOI).
    """
    if not isinstance(datos, (bytes, bytearray)) or len(datos) < 12 or datos[:2] != b"\xff\xd8":
        return None
    if not datos.endswith(b"\xff\xd9"):
        return None
    i = 2
    while i + 4 <= len(datos):
        if datos[i] != 0xFF:
            return None
        marcador = datos[i + 1]
        if marcador == 0xFF:                       # bytes de relleno
            i += 1
            continue
        if marcador == 0x01 or 0xD0 <= marcador <= 0xD7:
            i += 2
            continue
        if marcador in (0xD8, 0xD9, 0xDA):         # SOI repetido, EOI o datos antes del encabezado
            return None
        longitud = int.from_bytes(datos[i + 2:i + 4], "big")
        if longitud < 2 or i + 2 + longitud > len(datos):
            return None
        if marcador in (0xC0, 0xC1, 0xC2):
            if longitud < 8:
                return None
            alto = int.from_bytes(datos[i + 5:i + 7], "big")
            ancho = int.from_bytes(datos[i + 7:i + 9], "big")
            componentes = datos[i + 9]
            if ancho == 0 or alto == 0:
                return None
            return ancho, alto, componentes
        i += 2 + longitud
    return None

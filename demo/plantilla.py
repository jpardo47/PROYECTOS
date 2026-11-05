"""Plantilla ficticia de mantenimiento técnico y su validación.

Es la fuente única de la estructura del reporte: el servidor la usa para validar y el formulario del
navegador la recibe en /api/plantilla para dibujar los campos. Todos los mensajes de error están en español.
"""
import base64
import binascii
import datetime
import re

from demo.jpeg import inspeccionar

LIMITES_FOTOS = {
    "maximo": 10,                    # fotografías por reporte
    "bytes_max": 2_000_000,          # tamaño de cada foto ya comprimida (lo que guarda el servidor)
    "lado_max": 1600,                # píxeles del lado mayor
    "origen_bytes_max": 15_000_000,  # tamaño del archivo que el usuario elige en el navegador
    "origen_tipos": ["image/jpeg", "image/png"],
}

PLANTILLA = {
    "id": "mantenimiento-aire-acondicionado",
    "titulo": "Reporte de mantenimiento de aire acondicionado",
    "empresa": "Empresa Demo de Climatización (ficticia)",
    "secciones": [
        {"id": "servicio", "titulo": "Datos del servicio", "campos": [
            {"id": "fecha_servicio", "etiqueta": "Fecha del servicio", "tipo": "fecha", "obligatorio": True},
            {"id": "cliente", "etiqueta": "Cliente", "tipo": "texto", "obligatorio": True, "min": 2, "max": 120},
            {"id": "sede", "etiqueta": "Sede o dirección", "tipo": "texto", "max": 160},
            {"id": "tecnico", "etiqueta": "Técnico responsable", "tipo": "texto", "obligatorio": True, "min": 2, "max": 80},
            {"id": "tipo_servicio", "etiqueta": "Tipo de servicio", "tipo": "opcion", "obligatorio": True,
             "opciones": ["Preventivo", "Correctivo", "Diagnóstico"]},
        ]},
        {"id": "equipo", "titulo": "Equipo", "campos": [
            {"id": "tipo_equipo", "etiqueta": "Tipo de equipo", "tipo": "opcion", "obligatorio": True,
             "opciones": ["Split de muro", "Piso-techo", "Cassette", "Ductos", "Chiller", "Otro"]},
            {"id": "marca", "etiqueta": "Marca", "tipo": "texto", "max": 60},
            {"id": "modelo", "etiqueta": "Modelo", "tipo": "texto", "max": 60},
            {"id": "serial", "etiqueta": "Serial", "tipo": "texto", "obligatorio": True, "min": 3, "max": 60,
             "patron": r"^[A-Za-z0-9][A-Za-z0-9 ._/-]*$",
             "mensaje_patron": "Use solo letras, números, espacios y . _ / -"},
            {"id": "ubicacion_equipo", "etiqueta": "Ubicación del equipo", "tipo": "texto", "max": 100},
            {"id": "capacidad_btu", "etiqueta": "Capacidad", "tipo": "entero", "min": 1000, "max": 1_000_000, "unidad": "BTU/h"},
        ]},
        {"id": "mediciones", "titulo": "Mediciones", "campos": [
            {"id": "voltaje_v", "etiqueta": "Voltaje", "tipo": "decimal", "min": 0, "max": 600, "unidad": "V"},
            {"id": "corriente_a", "etiqueta": "Corriente", "tipo": "decimal", "min": 0, "max": 500, "unidad": "A"},
            {"id": "presion_psi", "etiqueta": "Presión de succión", "tipo": "decimal", "min": 0, "max": 1000, "unidad": "psi"},
            {"id": "temp_suministro_c", "etiqueta": "Temperatura de suministro", "tipo": "decimal", "min": -30, "max": 60, "unidad": "°C"},
        ]},
        {"id": "actividades", "titulo": "Actividades realizadas", "campos": [
            {"id": "limpieza_filtros", "etiqueta": "Limpieza de filtros", "tipo": "casilla"},
            {"id": "limpieza_serpentines", "etiqueta": "Limpieza de serpentines", "tipo": "casilla"},
            {"id": "revision_drenaje", "etiqueta": "Revisión de drenaje", "tipo": "casilla"},
            {"id": "revision_electrica", "etiqueta": "Revisión eléctrica", "tipo": "casilla"},
        ]},
        {"id": "cierre", "titulo": "Resultado", "campos": [
            {"id": "estado_final", "etiqueta": "Estado final del equipo", "tipo": "opcion", "obligatorio": True,
             "opciones": ["Operativo", "Operativo con observaciones", "Fuera de servicio"]},
            {"id": "observaciones", "etiqueta": "Observaciones", "tipo": "textolargo", "obligatorio": True, "min": 5, "max": 2000},
            {"id": "recomendaciones", "etiqueta": "Recomendaciones", "tipo": "textolargo", "max": 2000},
        ]},
    ],
    "fotos": LIMITES_FOTOS,
}

CAMPOS = [c for s in PLANTILLA["secciones"] for c in s["campos"]]
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CONTROL_LINEA = re.compile(r"[\x00-\x1f\x7f]")
OBLIGATORIO = "Este campo es obligatorio."


def _numero(valor, campo):
    if isinstance(valor, bool):
        raise ValueError
    if isinstance(valor, (int, float)):
        numero = float(valor)
    else:
        texto = str(valor).strip().replace(",", ".")
        if not re.fullmatch(r"-?\d+(\.\d+)?", texto):
            raise ValueError
        numero = float(texto)
    if campo["tipo"] == "entero":
        if numero != int(numero):
            raise ValueError
        return int(numero)
    return round(numero, 2)


def _validar_campo(campo, valor, hoy):
    """Devuelve (valor_limpio, error). Un valor vacío y opcional se guarda como None."""
    tipo = campo["tipo"]
    if tipo == "casilla":
        return (valor is True or valor in ("true", "on", "1", 1)), None
    vacio = valor is None or (isinstance(valor, str) and valor.strip() == "")
    if vacio:
        return None, (OBLIGATORIO if campo.get("obligatorio") else None)
    if tipo in ("texto", "textolargo"):
        if not isinstance(valor, str):
            return None, "Ingrese un texto."
        texto = valor.replace("\r\n", "\n").strip()
        if (_CONTROL if tipo == "textolargo" else _CONTROL_LINEA).search(texto):
            return None, "Contiene caracteres no permitidos."
        if "min" in campo and len(texto) < campo["min"]:
            return None, f"Debe tener al menos {campo['min']} caracteres."
        if "max" in campo and len(texto) > campo["max"]:
            return None, f"Máximo {campo['max']} caracteres (tiene {len(texto)})."
        if "patron" in campo and not re.fullmatch(campo["patron"], texto):
            return None, campo.get("mensaje_patron", "Formato no válido.")
        return texto, None
    if tipo == "fecha":
        try:
            fecha = datetime.date.fromisoformat(str(valor).strip())
        except ValueError:
            return None, "Ingrese una fecha válida (AAAA-MM-DD)."
        if fecha > hoy + datetime.timedelta(days=1):
            return None, "La fecha no puede ser posterior a hoy."
        if fecha < datetime.date(2000, 1, 1):
            return None, "La fecha debe ser posterior al año 2000."
        return fecha.isoformat(), None
    if tipo == "opcion":
        if valor not in campo["opciones"]:
            return None, "Seleccione una opción de la lista."
        return valor, None
    if tipo in ("entero", "decimal"):
        try:
            numero = _numero(valor, campo)
        except (ValueError, OverflowError):
            return None, "Ingrese un número entero válido." if tipo == "entero" else "Ingrese un número válido."
        if not campo["min"] <= numero <= campo["max"]:
            unidad = f" {campo['unidad']}" if campo.get("unidad") else ""
            return None, f"Debe estar entre {campo['min']} y {campo['max']}{unidad}."
        return numero, None
    return None, "Tipo de campo desconocido."


def validar_campos(datos, hoy=None):
    """Valida los campos del formulario. Devuelve (campos_limpios, errores_por_campo)."""
    hoy = hoy or datetime.date.today()
    if not isinstance(datos, dict):
        return {}, {"_general": "Los campos del reporte no tienen el formato esperado."}
    limpios, errores = {}, {}
    for campo in CAMPOS:
        valor, error = _validar_campo(campo, datos.get(campo["id"]), hoy)
        if error:
            errores[campo["id"]] = error
        else:
            limpios[campo["id"]] = valor
    return limpios, errores


def validar_fotos(fotos):
    """Valida la lista de fotos enviada como [{"nombre", "datos" (base64 de un JPEG)}].

    Devuelve (fotos_limpias, error). El navegador ya reduce y convierte a JPEG; aquí se comprueba de nuevo.
    """
    if fotos is None:
        return [], None
    if not isinstance(fotos, list):
        return [], "Las fotografías no tienen el formato esperado."
    if len(fotos) > LIMITES_FOTOS["maximo"]:
        return [], f"Máximo {LIMITES_FOTOS['maximo']} fotografías por reporte (se enviaron {len(fotos)})."
    limpias = []
    for n, foto in enumerate(fotos, 1):
        if not isinstance(foto, dict) or not isinstance(foto.get("datos"), str):
            return [], f"La fotografía {n} no tiene el formato esperado."
        try:
            contenido = base64.b64decode(foto["datos"], validate=True)
        except (binascii.Error, ValueError):
            return [], f"La fotografía {n} no se pudo leer."
        if len(contenido) > LIMITES_FOTOS["bytes_max"]:
            return [], f"La fotografía {n} supera 2 MB después de comprimirse."
        info = inspeccionar(contenido)
        if info is None:
            return [], f"La fotografía {n} no es una imagen JPEG válida. Use JPEG o PNG desde el formulario."
        ancho, alto, componentes = info
        if max(ancho, alto) > LIMITES_FOTOS["lado_max"]:
            return [], f"La fotografía {n} supera {LIMITES_FOTOS['lado_max']} píxeles en su lado mayor."
        if componentes not in (1, 3):
            return [], f"La fotografía {n} usa un formato de color no admitido."
        nombre = str(foto.get("nombre") or f"foto-{n}.jpg").replace("\\", "/").split("/")[-1]
        nombre = _CONTROL_LINEA.sub("", nombre)[:100] or f"foto-{n}.jpg"
        limpias.append({"nombre": nombre, "ancho": ancho, "alto": alto, "jpeg": contenido})
    return limpias, None

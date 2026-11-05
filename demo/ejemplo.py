"""Reportes ficticios para mostrar la demo. No contienen datos de clientes reales."""
import base64
import datetime
from pathlib import Path

from demo.plantilla import PLANTILLA, validar_campos, validar_fotos

CARPETA = Path(__file__).resolve().parent / "ejemplos"

EJEMPLOS = [
    {
        "campos": {
            "fecha_servicio": None, "cliente": "Cliente Ficticio A S.A.S.", "sede": "Sede de ejemplo, Calle 0 # 0-00",
            "tecnico": "Técnico Demo Uno", "tipo_servicio": "Preventivo", "tipo_equipo": "Split de muro",
            "marca": "Marca Genérica", "modelo": "MG-12", "serial": "DEMO-0001", "ubicacion_equipo": "Sala de reuniones",
            "capacidad_btu": 12000, "voltaje_v": 220.5, "corriente_a": 4.8, "presion_psi": 118, "temp_suministro_c": 13.5,
            "limpieza_filtros": True, "limpieza_serpentines": True, "revision_drenaje": True, "revision_electrica": True,
            "estado_final": "Operativo",
            "observaciones": "Equipo con filtros saturados. Se realizó limpieza completa y prueba de funcionamiento.",
            "recomendaciones": "Programar la siguiente limpieza en tres meses.",
        },
        "fotos": ["foto_ejemplo_1.jpg", "foto_ejemplo_2.jpg"],
    },
    {
        "campos": {
            "fecha_servicio": None, "cliente": "Cliente Ficticio B Ltda.", "sede": "",
            "tecnico": "Técnico Demo Dos", "tipo_servicio": "Correctivo", "tipo_equipo": "Cassette",
            "marca": "", "modelo": "", "serial": "DEMO-0002", "ubicacion_equipo": "Recepción",
            "capacidad_btu": 24000, "voltaje_v": 208, "corriente_a": 9.1, "presion_psi": None, "temp_suministro_c": None,
            "limpieza_filtros": True, "limpieza_serpentines": False, "revision_drenaje": True, "revision_electrica": True,
            "estado_final": "Operativo con observaciones",
            "observaciones": "Fuga leve en la bandeja de drenaje. Se ajustó la conexión; queda en observación.",
            "recomendaciones": "",
        },
        "fotos": ["foto_ejemplo_2.jpg"],
    },
]


def cargar_ejemplos(almacen):
    """Carga los reportes ficticios solo si la base está vacía. Devuelve cuántos creó."""
    if almacen.contar():
        return 0
    hoy = datetime.date.today()
    creados = 0
    for dias, ejemplo in zip((3, 1), EJEMPLOS):
        crudos = dict(ejemplo["campos"], fecha_servicio=(hoy - datetime.timedelta(days=dias)).isoformat())
        campos, errores = validar_campos(crudos)
        fotos, error = validar_fotos([{"nombre": n, "datos": base64.b64encode((CARPETA / n).read_bytes()).decode()}
                                      for n in ejemplo["fotos"]])
        if errores or error:
            raise ValueError(f"Ejemplo inválido: {errores or error}")
        almacen.crear(PLANTILLA["id"], campos, fotos)
        creados += 1
    return creados

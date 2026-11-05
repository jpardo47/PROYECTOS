"""Persistencia local en SQLite: reportes y fotografías (JPEG) en un único archivo."""
import datetime
import json
import sqlite3
import threading
import uuid
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS reportes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    plantilla TEXT NOT NULL,
    creado TEXT NOT NULL,
    fecha_servicio TEXT NOT NULL,
    cliente TEXT NOT NULL,
    datos TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fotos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporte_id INTEGER NOT NULL REFERENCES reportes(id) ON DELETE CASCADE,
    orden INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    ancho INTEGER NOT NULL,
    alto INTEGER NOT NULL,
    bytes INTEGER NOT NULL,
    jpeg BLOB NOT NULL,
    UNIQUE (reporte_id, orden)
);
CREATE INDEX IF NOT EXISTS idx_reportes_fecha ON reportes (fecha_servicio);
"""


class Almacen:
    def __init__(self, ruta_db):
        self.ruta = Path(ruta_db)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self._escritura = threading.Lock()
        with self._conectar() as con:
            con.executescript(ESQUEMA)

    def _conectar(self):
        con = sqlite3.connect(self.ruta, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def crear(self, plantilla_id, campos, fotos):
        creado = datetime.datetime.now().replace(microsecond=0).isoformat(sep=" ")
        with self._escritura, self._conectar() as con:
            cur = con.execute(
                "INSERT INTO reportes (numero, plantilla, creado, fecha_servicio, cliente, datos) VALUES (?, ?, ?, ?, ?, ?)",
                (f"pendiente-{uuid.uuid4()}", plantilla_id, creado, campos["fecha_servicio"], campos["cliente"],
                 json.dumps(campos, ensure_ascii=False)))
            rid = cur.lastrowid
            numero = f"RT-{rid:04d}"
            con.execute("UPDATE reportes SET numero = ? WHERE id = ?", (numero, rid))
            for orden, foto in enumerate(fotos, 1):
                con.execute(
                    "INSERT INTO fotos (reporte_id, orden, nombre, ancho, alto, bytes, jpeg) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (rid, orden, foto["nombre"], foto["ancho"], foto["alto"], len(foto["jpeg"]), foto["jpeg"]))
        return {"id": rid, "numero": numero}

    def listar(self, texto=None, desde=None, hasta=None, limite=200):
        condiciones, args = [], []
        if texto:
            condiciones.append("(r.cliente LIKE ? ESCAPE '\\' OR r.numero LIKE ? ESCAPE '\\')")
            patron = "%" + texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            args += [patron, patron]
        if desde:
            condiciones.append("r.fecha_servicio >= ?")
            args.append(desde)
        if hasta:
            condiciones.append("r.fecha_servicio <= ?")
            args.append(hasta)
        donde = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        with self._conectar() as con:
            filas = con.execute(
                f"""SELECT r.id, r.numero, r.creado, r.fecha_servicio, r.cliente, r.datos,
                           (SELECT COUNT(*) FROM fotos f WHERE f.reporte_id = r.id) AS n_fotos
                    FROM reportes r {donde} ORDER BY r.fecha_servicio DESC, r.id DESC LIMIT ?""",
                (*args, limite)).fetchall()
        resultado = []
        for f in filas:
            datos = json.loads(f["datos"])
            resultado.append({"id": f["id"], "numero": f["numero"], "creado": f["creado"],
                              "fecha_servicio": f["fecha_servicio"], "cliente": f["cliente"],
                              "tipo_equipo": datos.get("tipo_equipo"), "estado_final": datos.get("estado_final"),
                              "n_fotos": f["n_fotos"]})
        return resultado

    def obtener(self, rid):
        with self._conectar() as con:
            r = con.execute("SELECT * FROM reportes WHERE id = ?", (rid,)).fetchone()
            if r is None:
                return None
            fotos = con.execute(
                "SELECT orden, nombre, ancho, alto, bytes FROM fotos WHERE reporte_id = ? ORDER BY orden",
                (rid,)).fetchall()
        return {"id": r["id"], "numero": r["numero"], "plantilla": r["plantilla"], "creado": r["creado"],
                "campos": json.loads(r["datos"]), "fotos": [dict(f) for f in fotos]}

    def foto(self, rid, orden):
        with self._conectar() as con:
            fila = con.execute("SELECT jpeg FROM fotos WHERE reporte_id = ? AND orden = ?", (rid, orden)).fetchone()
        return bytes(fila["jpeg"]) if fila else None

    def fotos_completas(self, rid):
        with self._conectar() as con:
            filas = con.execute(
                "SELECT orden, nombre, ancho, alto, jpeg FROM fotos WHERE reporte_id = ? ORDER BY orden",
                (rid,)).fetchall()
        return [{"orden": f["orden"], "nombre": f["nombre"], "ancho": f["ancho"], "alto": f["alto"],
                 "jpeg": bytes(f["jpeg"])} for f in filas]

    def contar(self):
        with self._conectar() as con:
            return con.execute("SELECT COUNT(*) FROM reportes").fetchone()[0]

"""Genera y verifica dos respaldos en respaldos/ (carpeta ignorada por Git).

- Público: CLAUDE.md, README.md, .gitignore, docs/ y scripts/. Nunca incluye privado_comercial/.
- Privado: privado_comercial/, sin archivos .zip ni archivos con patrones de credenciales.

Cada zip incluye MANIFIESTO.txt con el SHA-256 de cada archivo. La verificación reabre el zip, comprueba su
integridad y el inventario, y revisa que el público no contenga correos, teléfonos ni rutas privadas.
Uso: python3 -I scripts/respaldo.py
"""
import hashlib
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "respaldos"
PUBLICO_ARCHIVOS = ["CLAUDE.md", "README.md", ".gitignore"]
PUBLICO_DIRS = ["docs", "scripts"]
PRIVADO_DIR = "privado_comercial"
EXCLUIR = re.compile(r"(\.zip$|\.env$|\.db$|\.sqlite3?$|__pycache__|node_modules|graphify-out|\.pyc$)")
CREDENCIAL = re.compile(r"(api[_-]?key|token|password|contraseña|secret)\s*[:=]\s*\S+", re.I)
CORREO = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TELEFONO = re.compile(r"\+?57\s?3\d{2}\s?\d{3}\s?\d{4}")
CORREO_PERMITIDO = re.compile(r"@users\.noreply\.github\.com$|@example\.invalid$")


def recolectar_publico():
    archivos = [RAIZ / f for f in PUBLICO_ARCHIVOS if (RAIZ / f).is_file()]
    for d in PUBLICO_DIRS:
        archivos += [p for p in sorted((RAIZ / d).rglob("*")) if p.is_file()]
    return [p for p in archivos if not EXCLUIR.search(str(p)) and PRIVADO_DIR not in p.relative_to(RAIZ).parts]


def recolectar_privado():
    base = RAIZ / PRIVADO_DIR
    if not base.is_dir():
        return []
    archivos = [p for p in sorted(base.rglob("*")) if p.is_file() and not EXCLUIR.search(str(p))]
    seguros = []
    for p in archivos:
        texto = p.read_text(encoding="utf-8", errors="ignore")
        if CREDENCIAL.search(texto):
            print(f"  excluido por posible credencial: {p.relative_to(RAIZ)}")
            continue
        seguros.append(p)
    return seguros


def escribir(nombre, archivos):
    DESTINO.mkdir(exist_ok=True)
    salida = DESTINO / nombre
    lineas = []
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for p in archivos:
            rel = p.relative_to(RAIZ).as_posix()
            z.write(p, rel)
            lineas.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel}")
        z.writestr("MANIFIESTO.txt", "\n".join(lineas) + "\n")
    return salida


def verificar(salida, archivos, publico):
    errores = []
    with zipfile.ZipFile(salida) as z:
        if z.testzip() is not None:
            errores.append("zip corrupto")
        nombres = set(z.namelist()) - {"MANIFIESTO.txt"}
        esperados = {p.relative_to(RAIZ).as_posix() for p in archivos}
        if nombres != esperados:
            errores.append(f"inventario distinto: {sorted(nombres ^ esperados)}")
        for n in nombres:
            if publico and n.startswith(PRIVADO_DIR + "/"):
                errores.append(f"archivo privado en respaldo público: {n}")
            if publico:
                t = z.read(n).decode("utf-8", errors="ignore")
                correos = [c for c in CORREO.findall(t) if not CORREO_PERMITIDO.search(c)]
                if correos:
                    errores.append(f"correo en {n}: {correos[:3]}")
                if TELEFONO.search(t):
                    errores.append(f"teléfono en {n}")
    return errores


def main():
    hoy = date.today().isoformat()
    resultado = 0
    for nombre, archivos, publico in (
        (f"respaldo_publico_{hoy}.zip", recolectar_publico(), True),
        (f"respaldo_privado_{hoy}.zip", recolectar_privado(), False),
    ):
        if not archivos:
            print(f"{nombre}: sin archivos (¿falta la carpeta privada?)")
            continue
        salida = escribir(nombre, archivos)
        errores = verificar(salida, archivos, publico)
        digest = hashlib.sha256(salida.read_bytes()).hexdigest()[:16]
        estado = "OK" if not errores else "ERROR"
        print(f"{salida.relative_to(RAIZ)}: {len(archivos)} archivos, {salida.stat().st_size} bytes, sha256 {digest}…, {estado}")
        for e in errores:
            print(f"  - {e}")
        resultado |= bool(errores)
    sys.exit(resultado)


if __name__ == "__main__":
    main()

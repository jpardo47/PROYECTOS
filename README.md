# PROYECTOS

Proyecto comercial de Juan Sebastián Pardo Quispe, desarrollador de software independiente. La guía de
sesión está en `CLAUDE.md` y el estado actual en `docs/ESTADO_ACTUAL.md`.

## Demo local: paquete de reportes técnicos

Demostración del flujo **crear reporte → registrar datos y fotos → guardar → consultar → generar PDF**. El
PDF sale marcado como **borrador para revisión**. Usa una plantilla ficticia de mantenimiento de aire
acondicionado y datos de ejemplo sin clientes reales.

**No es el producto contratado completo**: no tiene usuarios, roles, permisos ni despliegue (ver "Límites").

### Requisitos

- Python 3 (probado con 3.13). Usa solo la biblioteca estándar, sin dependencias que instalar.
- Opcional, para la prueba en navegador: Node.js con el paquete `playwright` y Chromium disponibles.
- Opcional, para que las pruebas lean el contenido del PDF: `pypdfium2`. Si no está, esa comprobación se
  omite y se avisa.

### Instalar

No requiere instalación: basta con clonar el repositorio.

### Ejecutar

```bash
python3 -m demo --datos-ejemplo
```

Abra <http://127.0.0.1:8000/>. La opción `--datos-ejemplo` carga 2 reportes ficticios solo si la base
está vacía.

Otras opciones:
- `--puerto 8080` cambia el puerto.
- `--datos <carpeta>` usa otra carpeta de datos (por defecto `demo/datos/`, ignorada por Git).

Detener con Ctrl+C.

### Probar

```bash
python3 -m unittest discover -s demo/tests -t . -v
```

```bash
node demo/tests/e2e_navegador.js /tmp/demo-e2e
```

- La primera orden (11 pruebas) arranca un servidor real en un puerto efímero con datos temporales.
  Comprueba la creación y la consulta, las validaciones de campos y archivos, los errores, el PDF (abierto
  con un lector independiente), la persistencia tras reiniciar, el enlace local y las cabeceras de seguridad.
- La segunda (9 comprobaciones) recorre el flujo completo en Chromium con vista móvil de iPhone 13, reinicia el servidor y deja
  capturas y el PDF en la carpeta indicada.

### Qué incluye

- Formulario de 22 campos en 5 secciones, utilizable desde el navegador del celular.
- Validación en el navegador y en el servidor, con mensajes en español.
- Fotos JPEG o PNG, hasta 10 por reporte y hasta 15 MB cada una al elegirlas. El navegador las reduce a
  1.600 px y las convierte a JPEG; el servidor acepta hasta 2 MB por foto y verifica que sea un JPEG válido.
- Persistencia en SQLite (`demo/datos/reportes.sqlite3`).
- Listado con búsqueda por cliente o número y filtro por fechas.
- PDF A4 con los datos, las fotos, la marca "BORRADOR PARA REVISIÓN" y un espacio de revisión y firma.

### Seguridad: qué se comprobó

- **Enlace solo local:** el servidor se enlaza a `127.0.0.1`. Se comprobó en la tabla de sockets del
  sistema (`/proc/net/tcp`) y con una prueba automática. Una conexión a la IP no local del equipo fue
  rechazada por el sistema operativo.
- **Encabezado `Host`:** solo se aceptan `127.0.0.1:<puerto>` y `localhost:<puerto>`; cualquier otro valor
  recibe 403 (prueba automática). Protege frente a ataques de *DNS rebinding* desde el navegador. **No es
  autenticación**: el cliente controla ese encabezado.
- **Otros controles probados:** solicitudes limitadas a 30 MB (413), JSON obligatorio en POST (415) y
  cabeceras `Content-Security-Policy`, `X-Content-Type-Options` y `X-Frame-Options`.
- **Revisado en el código, sin prueba dedicada:** el contenido del usuario se inserta en la página como
  texto, no como HTML.

La demo **no tiene autenticación, usuarios ni roles**. Estos controles no la hacen apta para red ni para
internet: úsela solo en su equipo.

### Límites

- No es el paquete comercial completo ni un sistema listo para producción. Faltan usuarios, roles y
  permisos (el paquete contempla 10 técnicos y 2 administradores) y no hay despliegue.
- Una sola plantilla, fija en el código. Sin edición ni borrado de reportes, sin modo sin conexión, sin
  exportaciones ni integraciones.
- Sin pruebas en un celular físico ni en Safari o iOS real (solo emulación en Chromium).

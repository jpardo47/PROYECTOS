# Estado actual

Última comprobación: 2026-11-05, en esta sesión. Lo que proviene de otros entornos o del usuario se marca
como tal y no se presenta como verificado aquí.

| Componente | Estado | Evidencia | Ubicación | Siguiente acción |
|---|---|---|---|---|
| **Demo de reportes técnicos** | Funciona en local; solo para demostración | 11 pruebas automáticas y 9 comprobaciones en Chromium (emulación de iPhone 13) en verde | `demo/`, `README.md` | Usarla en videollamadas; prueba en un celular físico pendiente |
| Oferta comercial remota | Lista | Sin horas, costes ni márgenes | `docs/comercial/OFERTA.md` | Completar el contacto en la copia que se envíe |
| Plantilla de cotización | Lista | Ocho apartados más licencia, confidencialidad y responsabilidad | `docs/comercial/PLANTILLA_COTIZACION.md` | Revisión legal |
| Propuestas específicas | Listas, pendientes de aprobación | Archivo privado | `privado_comercial/PROPUESTAS_PROSPECTOS.md` | Aprobación del usuario |
| Mensajes de primer contacto | 13 con la firma completa. **No enviados** | Archivo privado | `privado_comercial/BORRADORES_CONTACTO.md` | Aprobación y envío manual |
| Cartera de prospectos | 23 empresas únicas | Verificadas con el buscador restringido al dominio oficial | `privado_comercial/prospectos_2026-11-05.csv` | Confirmar el canal antes de cada envío |
| Datos tributarios y de cobro | RUT tramitado **según el usuario**; sin verificar | Información del usuario | — | Verificación con un contador |
| Harvey | **No operativo**: no instalado ni ejecutado | Instalación bloqueada por el control de permisos | `docs/comercial/ESTADO_HARVEY.md` | Ninguna en esta fase |
| MVP de analítica de video | Ausente en la sesión y en el repositorio | Búsqueda en archivos y en GitHub | — | No se reconstruye (decisión del usuario) |
| Graphify | Evaluado: solo código, local y sin modelos | `graphifyy` 0.9.102 instalado de forma aislada (temporal); 164 nodos y 315 relaciones; 3 consultas verificadas contra el código. Sin `install`, hooks, MCP ni Cloud | `docs/GRAPHIFY.md` | Opcional. El índice no se conserva: regenerarlo en cada sesión y tras cambios de código |
| Respaldos | Comerciales (público y privado) y de la demo, verificados | Integridad, inventario y revisión de privacidad | `respaldos/` (local, ignorada por Git) | Descargarlos; el entorno es efímero |
| Git | `fcc343c` (documentación), `460bd8b` (demo) y el commit de continuidad de Graphify (ver `git log`) publicados en `claude/trusting-franklin-ulwkkt`. `main` incluye `fcc343c` por la fusión del PR #1, hecha en GitHub con la cuenta del usuario; `460bd8b` no está en `main` | `git ls-remote` y `git log origin/main` | — | Cualquier commit nuevo requiere autorización |

## Demo: funciones reales

- Crear un reporte desde el navegador (también móvil): 22 campos en 5 secciones y hasta 10 fotos.
- Validación en el navegador y en el servidor: obligatorios, longitudes, rangos, opciones, fechas, formato,
  cantidad y tamaño de fotos, y JPEG válido. Mensajes de error en español.
- Las fotos JPEG o PNG se reducen a 1.600 px y se convierten a JPEG en el navegador. El servidor acepta hasta
  2 MB por foto.
- Persistencia en SQLite, verificada tras reiniciar el servidor.
- Listado con búsqueda y filtro por fechas, y detalle del reporte con sus fotos.
- PDF A4 con la marca "BORRADOR PARA REVISIÓN" y un espacio de revisión y firma. Verificado con pypdfium2.

## Seguridad: qué se comprobó exactamente

- Enlace a `127.0.0.1`: se comprobó en `/proc/net/tcp` y con una prueba automática. Una conexión a la IP no
  local del contenedor (`192.0.2.2`) fue rechazada por el sistema operativo.
- Encabezado `Host`: solo se aceptan `127.0.0.1:<puerto>` y `localhost:<puerto>`; otro valor recibe 403
  (prueba automática). Es una defensa contra *DNS rebinding*, **no autenticación**.
- Límite de 30 MB (413), JSON obligatorio (415) y cabeceras CSP, `nosniff` y `X-Frame-Options`: con prueba
  automática.
- La inserción del contenido del usuario como texto, no como HTML, se revisó en el código, sin prueba dedicada.
- **Sin autenticación, usuarios, roles ni despliegue.** No apta para red ni para internet.

## Pendientes y limitaciones

- No es el paquete comercial completo ni un sistema listo para producción: faltan usuarios, roles y
  permisos (10 técnicos y 2 administradores) y no hay despliegue.
- No probada en un celular físico ni en Safari o iOS real; no evaluada con lector de pantalla ni con un
  volumen alto de reportes.
- Una plantilla fija. Sin edición ni borrado, sin modo sin conexión y sin copias de seguridad automáticas
  de la base.
- Horas reales de la demo frente a la estimación del paquete: no se midieron.

## Discrepancias registradas

- La versión publicada en `460bd8b` decía "`main` sin cambios". Después, `main` recibió la fusión del PR #1
  (con `fcc343c`), hecha desde GitHub y no desde esta sesión.

- Una respuesta anterior de la sesión calificó de ambigua la fuente oficial de Graphify. El usuario la
  identificó como `Graphify-Labs/graphify` (paquete `graphifyy`), y el repositorio existe.
- La tarea inicial suponía una instalación existente de Harvey. No había ninguna.
- El usuario indica que existe un MVP de analítica de video. No se encontró aquí.
- Umbral del margen del 35%: se corrigió de "51 h" a 50,96 h. El punto de equilibrio (78,4 h) va aparte.
- `docs/comercial/PLAN_7_DIAS.md` se trasladó a `docs/PLAN_7_DIAS.md`.

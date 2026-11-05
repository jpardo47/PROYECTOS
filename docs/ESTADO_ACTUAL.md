# Estado actual

Última comprobación: 2026-11-05, en esta sesión. Lo que proviene de otros entornos o del usuario se marca
como tal y no se presenta como verificado aquí.

| Componente | Estado | Evidencia | Ubicación | Siguiente acción |
|---|---|---|---|---|
| Oferta comercial remota | Lista | Archivo revisado; sin horas, costes ni márgenes | `docs/comercial/OFERTA.md` | Completar el contacto en la copia que se envíe |
| Plantilla de cotización | Lista | Ocho apartados más licencia, confidencialidad y responsabilidad | `docs/comercial/PLANTILLA_COTIZACION.md` | Revisión legal (plan de 7 días, sección A) |
| Propuestas específicas | Listas, pendientes de aprobación | 5 propuestas, un anexo común del paquete y una tabla de la ronda 2 | `privado_comercial/PROPUESTAS_PROSPECTOS.md` | Aprobación del usuario |
| Mensajes de primer contacto | 13 preparados con la firma completa. **No enviados** | Archivo privado | `privado_comercial/BORRADORES_CONTACTO.md` | Aprobación y envío manual |
| Cartera de prospectos | 23 empresas únicas, sin duplicados | Verificadas con el buscador restringido al dominio oficial, no abriendo las páginas | `privado_comercial/prospectos_2026-11-05.csv` | Confirmar el canal antes de cada envío |
| Modelo interno de costes | Reproducible | El script regenera el CSV con el mismo hash | `privado_comercial/herramientas/modelo_costos.py` | Sustituir los supuestos por facturas reales |
| Datos tributarios y de cobro | RUT tramitado **según el usuario**; sin verificar | Información del usuario | — | Verificación con un contador; definir las instrucciones de pago |
| Harvey | **No instalado ni ejecutado** | La instalación fue bloqueada por el control de permisos | `docs/comercial/ESTADO_HARVEY.md`; perfil en `privado_comercial/harvey/` | Ninguna en esta fase |
| Código del MVP | **Ausente** en esta sesión y en el repositorio | Búsqueda en el sistema de archivos; `main` solo tiene `README.md`; sin coincidencias en los repositorios de GitHub indexados | — | Si existe en otro equipo, subirlo a un repositorio |
| Graphify | No disponible y no instalado | Sin binario, paquete ni skill; no hay código que indexar | — | Reevaluar cuando exista código |
| Respaldos | Público y privado, generados y verificados con `scripts/respaldo.py` | Integridad, inventario y revisión de privacidad en verde; manifiesto SHA-256 dentro de cada zip | `respaldos/` (local, ignorada por Git) | Descargarlos; el entorno es efímero |
| Git | Cambios **sin commit ni push** | `git status`: archivos públicos sin seguimiento | Rama `claude/trusting-franklin-ulwkkt` | Autorización del usuario |

## Discrepancias registradas

- La tarea inicial suponía una instalación existente de Harvey. No había ninguna en este entorno.
- El usuario indica que existe un MVP. No se encontró aquí, así que no se trata como verificado.
- En la política privada, el umbral del margen del 35% se corrigió de "51 h" a 50,96 h. El punto de
  equilibrio (78,4 h) se registra por separado.
- `docs/comercial/PLAN_7_DIAS.md` se trasladó a `docs/PLAN_7_DIAS.md`.
- Se retiraron copias intermedias duplicadas de la carpeta privada. Siguen en los respaldos descargados antes.

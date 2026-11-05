# Estado de Harvey — 2026-11-05

Harvey = agente de prospección de código abierto `ethanplusai/harvey` (Python 3.11+, SQLite local,
dashboard FastAPI). Revisado en el commit `6b6a23a` (2026-11-01).

## Resumen

| Elemento | Estado |
|---|---|
| Instalación previa en este entorno | **No existe** (ni paquete, ni skill, ni MCP, ni carpeta compartida del ordenador) |
| Código fuente | Clonado **solo para lectura** en el scratchpad de la sesión (no en el repo) |
| Instalación (`pip install -e .`) | **Bloqueada** por el control de permisos del sandbox (ejecución de código externo). No se intentó rodear. |
| Comandos ejecutados con Harvey | **Ninguno** |
| Perfil comercial | **Preparado para importar**: `harvey.local.yaml` (en carpeta privada ignorada por Git) |
| Empresas | **Preparadas para importar** en CSV con columnas del registro de Harvey. Harvey **no documenta** un comando de importación. |
| Envíos, bucles, cuentas externas | Ninguno activado. En el perfil preparado: `channels.email.enabled: false`, `require_approval: true`, LinkedIn apagado. |

## Comandos revisados y sus efectos

| Comando | Efecto | ¿Seguro para ejecutar? |
|---|---|---|
| `harvey signals` / `--confirm CODES` | Escribe en SQLite local qué señales recolectar | Sí. **Confirmar solo señales de empresa**; ver abajo |
| `harvey discover --providers` | Muestra proveedores y precios | Sí (solo lectura) |
| `harvey discover --estimate` | Calcula coste y sale | Sí |
| `harvey discover --provider osm --city "Popayán, Colombia" --no-profile` | Consulta Overpass/OpenStreetMap (gratis) y guarda empresas | Sí, ejecución única; respeta límites de Overpass |
| `harvey profile` | 3+ peticiones HTTP por empresa a su web pública (robots, sitemap, home) | Sí, gratis; sin modelo |
| `harvey companies` / `harvey export` | Exporta CSV | Sí |
| `harvey status` / `harvey usage` | Lectura | Sí |
| `harvey train <url>` | **Llama al modelo** vía CLI de Claude con su suscripción | Solo en su equipo, con su sesión de Claude |
| `harvey run` | **Bucle continuo** (heartbeat cada 15 min): prospecta, escribe y envía | **No ejecutar** en esta fase |
| `harvey dashboard` | Servidor web local | Opcional, solo `127.0.0.1` |
| `harvey gmail auth` / `microsoft auth` | **Login OAuth** a cuenta de correo | No sin su decisión explícita |
| `harvey outbox --approve*` | Aprueba envíos | No en esta fase |

Señales que **no** deben confirmarse (identifican personas o deducen correos):
`CONTACT_FOUND`, `DECISION_MAKER_TITLE`, `LIKELY_OWNER`, `REGISTRY_VERIFIED`, `EMAIL_PATTERN`, `EMAIL_STATUS`.
Evite `harvey signals --confirm free`, porque las incluye. Confirme explícitamente, por ejemplo:
`TECH_STACK,SITE_PAGE_COUNT,NO_ONLINE_BOOKING,CONTACT_FORM_URL,HIRING_ROLE,OPEN_ROLES,NO_SCHEMA_MARKUP,BLOG_STALE`
(revise la lista exacta con `harvey signals` antes de confirmar).

Limitación relevante: el proveedor gratuito OpenStreetMap solo mapea términos como `hvac`, `electric`
y `distribuidora`; **no** cubre integradores de seguridad electrónica. Para ese segmento Harvey exige un
proveedor de búsqueda con clave (Serper, DataForSEO, Scavio: tienen coste o crédito inicial).

## Bloqueos concretos en esta sesión

1. Instalación de Harvey denegada por el control de permisos (código externo).
2. La política de red solo deja abrir dominios autorizados: no se pudieron abrir directamente los
   sitios de las empresas ni Overpass/Nominatim. La investigación se hizo con el buscador web, restringido
   al dominio oficial de cada empresa.
3. Harvey usa la CLI de Claude con suscripción para escribir: no se usaron credenciales de esta sesión.

## Instrucciones para continuar en su equipo (fuera del sandbox)

```bash
git clone https://github.com/ethanplusai/harvey.git && cd harvey
python3.13 -m venv .venv && source .venv/bin/activate && pip install -e .
cp /ruta/a/PROYECTOS/privado_comercial/harvey/harvey.local.yaml ./harvey.local.yaml
harvey signals                    # revisar catálogo; NO usar --confirm free
harvey signals --confirm TECH_STACK,SITE_PAGE_COUNT,CONTACT_FORM_URL,HIRING_ROLE,OPEN_ROLES
harvey discover --providers
harvey discover --provider osm --city "Popayán, Colombia" --estimate
harvey discover --provider osm --city "Popayán, Colombia" --no-profile --limit 50
harvey discover --provider osm --city "Cali, Colombia" --no-profile --limit 50
harvey companies --out data/exports/registro.csv
```

No ejecute `harvey run`, `harvey gmail auth` ni `harvey outbox --approve-all` hasta definir buzón,
dominio de envío, calentamiento y aprobación de mensajes.

Sobre las empresas ya investigadas: Harvey no tiene importación documentada. Opciones: (a) dejarlas en
el CSV privado y contactarlas manualmente (recomendado para estos primeros contactos), o (b) añadirlas
a `compliance.do_not_contact` para que Harvey no las vuelva a contactar por su cuenta.

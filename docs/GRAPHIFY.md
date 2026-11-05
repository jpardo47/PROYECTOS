# Graphify: uso local complementario

Evaluado el 2026-11-05. **Opcional**: no sustituye a `CLAUDE.md` ni a `docs/REANUDAR.md`, su ausencia no
bloquea el trabajo y no ofrece memoria permanente.

## Datos de la prueba

| Dato | Valor |
|---|---|
| Fuente oficial | Repositorio `Graphify-Labs/graphify`, revisado en el commit `59b5ab1` del 2026-11-03. Documentación: docs.graphify.com (no consultada: la red del entorno no lo permite) |
| Paquete y versión probados | `graphifyy` **0.9.102** (con doble «y»); comandos `graphify` y `graphify-mcp`. No se instaló ningún otro paquete `graphify*` |
| Instalación | **Aislada y temporal**, dentro del scratchpad de la sesión. No es permanente: desaparece con el entorno. HOME, `~/.local` y `~/.cache` sin cambios (verificado) |
| Commit indexado | `460bd8b27de28c1e0ee4a98e179acc8ac62d25a1` (demo) |
| Resultado | 13 archivos de código, 164 nodos, 315 relaciones y 10 comunidades, en unos 2 s y sin conexión |

## Requisitos para repetirlo

- `uv` (probado con 0.11.32) y acceso a PyPI para la instalación. uv instala `graphifyy` y sus gramáticas
  tree-sitter.
- Python 3.10 o superior según el README (probado con el Python 3.13.18 del sistema), `git` y `tar`.
- No hacen falta claves de API: el modo `--code-only` no usa modelos.

## Comandos ejecutados exactamente

En la sesión de prueba,
`SP=/tmp/claude-0/-home-user-PROYECTOS/b32875a7-022d-52a3-ad44-dd390cd20d9b/scratchpad/graphify-local` y
`GF=$SP/bin/graphify`. En otra máquina, sustituya `SP` por cualquier carpeta temporal fuera del repositorio.

1. Instalar de forma aislada:

```bash
export UV_TOOL_DIR=$SP/uv-tools UV_TOOL_BIN_DIR=$SP/bin UV_CACHE_DIR=$SP/uv-cache UV_PYTHON_INSTALL_DIR=$SP/uv-python UV_NO_MODIFY_PATH=1 && uv tool install --python 3.13 graphifyy
```

2. Copiar solo el commit publicado, desde la raíz del repositorio:

```bash
git archive 460bd8b | tar -x -C $SP/fuente
```

3. Extraer el índice solo de código, sin modelos, desde `$SP/fuente`:

```bash
HOME=$SP/home-aislado GRAPHIFY_BACKEND=none GRAPHIFY_QUERY_LOG_DISABLE=1 $GF extract . --code-only --no-viz
```

4. Generar el informe y consultar, desde `$SP/fuente` y en la misma terminal:

```bash
export HOME=$SP/home-aislado GRAPHIFY_BACKEND=none GRAPHIFY_QUERY_LOG_DISABLE=1
```

```bash
$GF cluster-only . --no-viz
```

```bash
$GF explain "validar_fotos()"
```

```bash
$GF path ".do_POST()" "inspeccionar()"
```

```bash
$GF query "dónde se validan las fotos jpeg y su tamaño"
```

Las carpetas `$SP/fuente` y `$SP/home-aislado` se crearon vacías antes del paso 2 (`mkdir -p`).

**No se ejecutaron:** `graphify install`, `graphify claude install` (instala un hook PreToolUse),
`graphify hook install`, el servidor MCP ni Graphify Cloud.

## Resultados verificados contra el código

| Consulta | Resultado | Comprobación |
|---|---|---|
| `explain "validar_fotos()"` | `demo/plantilla.py` L152. Llamada desde `.do_POST()` (`servidor.py:130`) y `cargar_ejemplos()` (`ejemplo.py:49`). Llama a `inspeccionar()` (L173) | Coincide exactamente |
| `path ".do_POST()" "inspeccionar()"` | `.do_POST()` → `validar_fotos()` → `inspeccionar()`, 2 saltos | Coincide |
| `query "…"` | Encuentra `jpeg.py` y `validar_fotos()`, pero devuelve 62 nodos | Útil solo para orientarse |

## Salidas, privacidad y conservación

- **Salidas:** en `$SP/fuente/graphify-out/`: `graph.json`, `GRAPH_REPORT.md`, `manifest.json`, `cache/` y
  archivos `.graphify_*`. En el repositorio, `graphify-out/` está en `.gitignore`.
- **Privacidad:** `git archive` copia solo lo versionado, así que `privado_comercial/`, `respaldos/`,
  `demo/datos/` y las credenciales quedan fuera por construcción. `--code-only` además omitió los 14
  documentos y las 3 imágenes. Con `GRAPHIFY_BACKEND=none` no se llamó a ningún modelo, y con el HOME
  aislado y el registro de consultas desactivado no se escribió fuera de `$SP`.
- **Conservación:** el índice **no se publica ni se incluye en ningún respaldo**. Vive en el scratchpad
  temporal y debe **regenerarse** en cada sesión nueva con los pasos 1 a 4.
- **Advertencia:** el índice refleja solo el commit indexado. Cualquier cambio de código requiere repetir
  los pasos 2 a 4 con el nuevo commit. Los cambios solo de documentación no lo afectan.

## Valor para este proyecto

Con unas 1.800 líneas, `explain` y `path` responden con exactitud quién llama a quién, pero `grep` es casi
igual de rápido. Será más útil cuando el código crezca.

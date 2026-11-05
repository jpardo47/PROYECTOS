# Reanudar

## Último estado comprobado (2026-11-05)

- **Demo de reportes técnicos funcionando en local** (`demo/`) y publicada en la rama
  `claude/trusting-franklin-ulwkkt`. Pasan 11 pruebas automáticas y 9 comprobaciones en navegador. Sin
  autenticación, usuarios ni roles: es una demostración, no el producto completo.
- La documentación comercial y de continuidad está publicada en la misma rama.
- 13 mensajes y las propuestas, listos en la carpeta privada. **Nada enviado.**
- Harvey no está operativo. Graphify se evalúa aparte (ver `docs/ESTADO_ACTUAL.md`).

## Siguiente acción concreta

El usuario aprueba los mensajes de `privado_comercial/BORRADORES_CONTACTO.md` y envía a mano la primera
tanda, de 5 a 10, tras confirmar el canal en el sitio oficial. En las videollamadas que resulten, muestra la
demo compartiendo pantalla (`python3 -m demo --datos-ejemplo`) y la presenta como demostración.

## Después

1. Verificar con un contador la documentación tributaria y de cobro.
2. Probar la demo en un navegador móvil real, sin exponerla en red, por ejemplo con las herramientas de
   desarrollo del navegador o con un túnel autorizado y autenticado, si se aprueba.
3. Medir las horas reales de cualquier ajuste de la demo frente a la estimación del paquete.

## Bloqueos concretos

- Faltan la aprobación de los mensajes y la verificación tributaria y de cobro.
- La demo no tiene autenticación: no debe exponerse en red.
- La red del entorno solo permite consultar sitios externos mediante el buscador.
- El entorno es efímero: lo que no tenga commit ni respaldo descargado se pierde.

## Archivos que debe leer la siguiente sesión

`CLAUDE.md` → este archivo → `docs/ESTADO_ACTUAL.md`. Para la demo: `README.md` y luego solo el módulo de
`demo/` que se vaya a cambiar.

## Mensaje corto para reanudar

> Lee CLAUDE.md y docs/REANUDAR.md, verifica docs/ESTADO_ACTUAL.md contra los archivos reales y continúa
> con la siguiente acción concreta. No vuelvas a investigar empresas ni reconstruyas el historial.

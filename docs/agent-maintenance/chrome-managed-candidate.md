# Candidato gestionado de Chrome

Preparado en la rama feat/managed-chrome-skill desde a09d9a48a7a4e0fd274d9dbc60c1029d528e89f4. La implementación local está preparada; no se instaló, publicó ni modificó el global. Mario gestiona cualquier merge del PR en el remoto.

## Cambios

- [Skill](../../skills/chrome-devtools-axi/SKILL.md) con selección para trabajo de navegador y política automática propia en agents/openai.yaml. El global no recibe rutas de activación.
- [Referencia obligatoria de aislamiento](../../skills/chrome-devtools-axi/references/session-isolation.md), leída antes de conexión o interacción.
- Entrada de propiedad, procedencia y licencia en skills.json, UPSTREAM.md y THIRD_PARTY_NOTICES.md. El AGENTS del repositorio refleja esa propiedad; instructions/global/AGENTS.md conserva sus bytes.
- CLI AXI 0.1.35 y MCP 1.9.0, sin actualización de ejecutables.

Licencia MIT de Kun Chen comprobada en [upstream, revisión exacta](https://github.com/kunchenguid/chrome-devtools-axi/blob/06688b18adf5c0855fca6ed4efe2dbd0ad0e2ec6/LICENSE), junto con la skill en esa revisión. Coincide con el aviso ya conservado en licenses/MIT-Kun-Chen.txt. Las divergencias locales están documentadas.

## Conservación de requisitos

| Regla del global | Destino en referencia |
|---|---|
| Headless verificado y no reiniciar navegador ajeno | Headless browser and endpoint |
| Sesión única estable, sin default ni puerto global | Session, tabs and state |
| Tab propio y comandos seriales por sesión | Session, tabs and state; workflow de la skill |
| Cookies compartidas y perfiles independientes | Authentication and storage |
| Adjuntar no cambia visibilidad; helpers no garantizan headless | Headless browser and endpoint |
| MCP fijado, bridges conservan transporte, detener sólo el propio | Pinned executables; Close owned resources |

Es una revisión de conservación textual. No demuestra comportamiento correcto de un agente.

## Comprobaciones realizadas

- Dependencias del worktree instaladas desde el lockfile, con Bun 1.3.14 y caché local.
- bun run check: 29 skills y 56 archivos Markdown válidos.
- quick_validate.py: Skill is valid.
- bun test: 28 pass, 1 skip, 0 fail; 297 assertions. La prueba omitida es E2E opcional de dos entornos Portless, no una prueba de Chrome.
- fish install/verify.fish: instalación activa 90477dd5963302075cbf13789e4e7da6bc7c03a1 íntegra, 28 skills y 118 destinos. Esto verifica conservación de la instalación activa, no instalación del candidato.
- git diff --check: sin errores.
- Ejecutables locales informan AXI 0.1.35 y MCP 1.9.0. Se leyó help de la versión instalada; no se abrió navegador ni inició un bridge.
- Global activo/canónico y skill externa comparados contra las versiones registradas: sin cambios.

## Antes de despliegue

La instalación externa todavía pertenece al instalador upstream, según ~/.agents/.skill-lock.json. El instalador mstack rechaza doble propiedad. La promoción deberá transferir esa propiedad con respaldo y verificar todos los enlaces; este candidato no modifica el lock externo. No desplegar toda la rama sin revisar cambios respecto del snapshot activo, que es distinto de su base de desarrollo.

Quedan por ejecutar pruebas de selección natural positiva y negativa, lectura efectiva de la referencia, preflight con navegador visible, sesiones concurrentes, necesidad de aislamiento de cookies y cierre sin afectar recursos ajenos. Las pruebas existentes del repositorio no establecen esos resultados. Hasta comprobarlos, el bloque global de Chrome permanece activo.

El worktree sigue disponible para revisión; no cumple todavía la condición de limpieza posterior a merge.

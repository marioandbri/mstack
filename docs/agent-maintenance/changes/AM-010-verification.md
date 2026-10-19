# Comprobaciones de la propuesta AM-010

Fecha: 2026-10-09. Worktree: /Users/mario.brito/personal/mstack-chrome-skill, rama feat/managed-chrome-skill. Estado: candidato, sin instalación, push, PR o merge.

## Resultados

| Comprobación | Resultado | Qué demuestra |
|---|---|---|
| bun run check, Bun 1.3.14 | PASS: 30 skills, 59 archivos Markdown de skills | Inventario, frontmatter básico, nombres y enlaces de recursos. |
| bun test, Bun 1.3.14 | 28 pass, 1 skip, 0 fail; 297 assertions | Suite existente de validación, instalador y contratos. No cumplimiento conductual de los cambios de instrucciones. |
| fish install/verify.fish | PASS: commit activo 90477dd5963302075cbf13789e4e7da6bc7c03a1, 28 skills, 118 targets | Contenido/configuración activa intactos. No instalación de las 30 candidatas. |
| quick_validate.py de skill-creator | PASS repository-workflow | Estructura básica de la nueva skill original. |
| Ajv 8.17.1 / draft 2020-12 | Registro AM-010 válido | Cobertura completa y decisiones sin pendientes; promotion=none. No prueba autorización o calidad por sí solo. |
| git diff --check | PASS | Sin errores de whitespace en el diff. |
| git apply --check y aplicación sobre baseline desechable | PASS; resultado idéntico a ambas copias completas del candidato | Diff global aplicable a la baseline exacta. |
| Codex CLI 0.160.0, app-server skills/list | 16/16 candidatos/apoyos descubiertos, enabled=true, 0 errores en candidatos | Descubrimiento en un proyecto Git temporal con symlinks. Cero ejecuciones de modelos. |

La prueba omitida de Portless es opt-in y requiere proxy HTTP saludable; no se arrancaron servicios para esta revisión documental. Las pruebas del instalador usan fuentes Git y hogares temporales; no activan esta propuesta en el stack real.

La primera ejecución del verificador activo encontró una restricción de acceso a su caché uv; la repetición con acceso concedido pasó. La primera configuración de Ajv strict rechazó anotaciones opcionales de tipo en condiciones de un esquema válido: se comprobó con strict=true y strictTypes=false, sin modificar el esquema. No se contabilizan como fallos del agente ni se añaden reglas al global por ellos.

En la comprobación del catálogo, el primer arranque estuvo limitado por permisos. La primera selección de resultados tras conceder acceso no reconoció los symlinks porque Codex devuelve sus rutas reales. Se corrigió el filtro del comprobador, conservando sólo rutas del candidato; no fue un fallo de descubrimiento. La consulta final pasó y terminó su propia instancia. [Recibo sanitizado](AM-010-discovery.json).

## Invocación y límites

[OpenAI Docs: Build skills](https://learn.chatgpt.com/docs/build-skills) describe la política allow_implicit_invocation en agents/openai.yaml. El coordinador y Chrome la permiten. Implement y las skills visuales conservan sus entradas explícitas; las dos visuales ahora expresan esa restricción también para Codex. La descripción/cuerpo mantiene la aceptación como límite del trabajo visual.

La versión local de skills/list no expone la política de invocación en su respuesta. El catálogo no demuestra aplicación de esa política ni selección ante un prompt; ambas requieren los [casos conductuales preparados](AM-010-behavior-cases.md). Las configuraciones de otros harnesses tampoco quedaron evaluadas. La restricción de frontmatter de otro harness no se presenta como equivalente universal del YAML de Codex.

No se ejecutaron nuevos modelos, browser sessions, login Pi, consultas privadas Bitbucket ni experimentos T3/suspensión. El endpoint Bitbucket se contrastó con documentación oficial; Pi con help/docs locales 1.0.0; T3 con su guía oficial. Las referencias relocalizadas explicitan esos límites y requieren confirmar versión/síntoma antes de aplicar un antecedente.

## Versiones y promoción

Baseline activa y canonical main: SHA-256 9b9406a1036570535f7b5f391ae754bbcbc5c8ba8e5da04a66b873a45504ffe2. El global se propone de 107 a 43 líneas; la reducción no es una puntuación de calidad.

[Manifest de fuentes candidatas](AM-010-candidate-files.json) fija archivos y hashes, incluido Chrome previamente preparado en d0dc8081388f3b14d5dc4ac95ae390ce2e99b804. [Registro Reflect](AM-010-global-agents.review.json) conserva las decisiones y hashes revisados. El manifest no es un recibo de instalación.

Antes de integrar: evaluar selección/comportamiento en el harness objetivo y resolver la propiedad externa de Chrome mediante el instalador versionado. Conservar el global activo hasta comprobar los destinos del traslado y autorizar su activación. El PR requiere confirmación de la implementación presentada; Mario gestiona el merge remoto.

# Clasificación y destinos de AM-010

Estado: propuesta completa, sin despliegue. La petición de completar ajustes autoriza preparar estos candidatos y analizar su ubicación. No demuestra todavía su selección ni cumplimiento por un modelo.

[Global completo](AM-010-global-agents.proposed.md), [baseline conservada](AM-010-global-agents.baseline.md), [diff global](AM-010-global-agents.patch), [decisiones](AM-010-global-agents.review.json) y [comprobaciones](AM-010-verification.md).

## Qué merece una skill

Un procedimiento condicionado, con un objetivo y resultado reutilizables, puede justificar una skill. Una corrección de configuración o un hecho de una herramienta no demuestra por sí solo esa necesidad. Primero se revisan propietarios existentes, evidencia y vigencia; copias del mismo apunte no cuentan como recurrencias independientes.

`repository-workflow` cubre una responsabilidad que faltaba: coordinar el ciclo desde el worktree hasta el cierre tras un merge remoto. Ampliar `implement` obligaría a cambiar su entrada explícita basada en spec/tickets y también cubrir trabajo directo. El nuevo coordinador conserva esa entrada y reutiliza implementación, pruebas, entorno y revisión; no replica sus procedimientos.

Pi, Bitbucket y T3 no requieren tres skills nuevas con la evidencia disponible. Son distinciones de diagnóstico: se trasladan a una referencia de `diagnose`, leída sólo ante el fallo correspondiente. Se separan hechos comprobados, anotaciones históricas e hipótesis. Una futura necesidad recurrente de configurar u operar esos sistemas puede justificar otro propietario; no está establecida en esta revisión.

## Cobertura del global original

| Bloque revisado | Clasificación y destino | Evidencia o límite |
|---|---|---|
| General Guidelines | Idioma, calidad, archivos generados y autoría permanecen como invariantes. Memoria pendiente sale del global; reparación universal se limita a regresiones de la tarea. | Preferencias y límites confirmados; captura/reflexión ya tienen propietarios. |
| Agent Workflow | Alcance y autorizaciones permanecen. Cierre, ruta y entrega van a `grill-with-docs`, `to-spec`, `to-tickets` e `implement`. | Cierre separado de ruta; direct work tras entrevista sólo si Mario lo pide. |
| Visual Accompaniment | Se conserva ofrecer y esperar aceptación; se retiran selectores de skills. | Triggers de `lavish` ajustados; `visual-companion` conserva su entrada explícita. |
| Environment Considerations | Fish, bun y límites de persistencia permanecen. Inventario de herramientas y versiones queda con propietarios. | No cambio de configuración global ejecutado. |
| Knowledge Gathered | Se reemplaza promoción directa por revisión de observaciones. | `capture-observations` captura; `reflect` coordina la revisión solicitada. |
| Chrome DevTools AXI usage | Procedimiento al fork gestionado de `chrome-devtools-axi` y referencia obligatoria. | Licencia/procedencia comprobadas; pins y aislamiento conservados. Transferencia de propiedad e instalación pendientes. |
| Personal engineering skills | Instrucciones de mantenimiento en AGENTS del repo, README e instalador. | Lista autoritativa `skills.json`; no mantener un conteo global que envejece. |
| Pi MCP configuration | Hechos y antecedentes en `diagnose/references/environment-diagnostics.md`. | Pi local 1.0.0/help/docs; antiguo significado de auth queda histórico y requiere comprobar esquema actual. Sin prueba de login. |
| CLI paths and Portless | Guía de PATH/runtime en `local-env/references/operations.md`. | Preferencia por ajuste de proceso; versiones operativas ya pertenecen al entorno. |
| Storage and worktree cleanup | Consentimiento general y propiedad permanecen. Procedimiento y contabilidad en `repository-workflow/references/worktree-lifecycle.md`. | Cierre propio autorizado; revisión general no autoriza borrado. Preservar cambios, consumidores, config y evidencia. |
| Conventions-aware engineering | Procedimientos ya en sus skills; documentación de mantenimiento en repo. | Sin selector global; descripciones existentes definen preflight/setup/review. |
| Bitbucket Cloud API | Hecho de endpoint en referencia de diagnose. | Endpoint efectivo comprobado en documentación oficial; el 404 previo no se reproduce aquí. |
| Dependency Selection | Criterios transversales conservados y resumidos. | Se conserva excepción vigente de bunx skills y revisión deliberada de locks. |
| Lavish Feedback Sessions | Detalle ya en `lavish/references/codex-feedback-loop.md`; se retira duplicación global. | La skill exige esa referencia antes de decir que escucha. Owner único, handle vivo y envío conservados. Sin sesión visual iniciada. |
| T3 Code remote-access diagnostics | Distinciones e hipótesis en referencia de diagnose. | Guía oficial consultada; endpoints antiguos requieren comprobar versión. Sin experimento de conexión o suspensión. |

## Inventario que deja de ser instrucción global

- `jq` y `ctx7`: capacidades descubribles del entorno. Se consulta ayuda local cuando se necesiten; no hay un workflow demostrado que justifique una skill nueva.
- `gh-axi`, `bb`, Chrome y Lavish: comandos, versiones y uso pertenecen a sus propietarios o al procedimiento de delivery. No se elimina su funcionalidad.
- Funciones/aliases futuros: la autorización del entorno determina la persistencia. Ideas adicionales van a la bandeja.
- APFS y volúmenes Docker: conocimiento condicionado al cierre y contabilidad de almacenamiento, conservado en esa referencia.

No se descarta evidencia histórica por ser antigua: se conserva la baseline y se marca su vigencia en los destinos. No se presenta una hipótesis anterior como regla universal ni como un fallo nuevo reproducido.

## Condiciones para integración

Los triggers positivos y negativos están en los propios propietarios. `repository-workflow` declara invocación implícita permitida. `implement`, `lavish` y `visual-companion` conservan su entrada explícita; sus políticas Codex la expresan en agents/openai.yaml, sin confiar en que un frontmatter de otro harness controle Codex; el coordinador sólo los carga dentro del alcance autorizado. No se añaden selectores al global para forzar selección.

Antes de activar el traslado se debe comprobar descubrimiento y comportamiento en el harness objetivo. Los checks estructurales de esta propuesta no sustituyen esa evaluación. Chrome también requiere resolver su propiedad externa con el instalador, preservando rollback. El global activo y las otras instalaciones siguen intactos.

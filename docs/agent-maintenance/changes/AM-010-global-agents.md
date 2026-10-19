# Propuesta completa de AGENTS y destinos

Estado: lista para revisar; ajustes preparados en worktree, promotion=none. Las 15 secciones originales están revisadas y las decisiones del cuestionario conservadas. No hay otra pregunta pendiente sobre triggers, alcance o criterios de pruebas. La instalación activa sigue intacta.

- [AGENTS.md completo propuesto](AM-010-global-agents.proposed.md), [baseline](AM-010-global-agents.baseline.md) y [diff](AM-010-global-agents.patch).
- [Clasificación por bloque](AM-010-classification.md): invariantes globales, procedimientos en propietarios, hechos de diagnóstico y antecedentes temporales.
- [Registro estructurado](AM-010-global-agents.review.json), [verificaciones](AM-010-verification.md) y [casos conductuales pendientes](AM-010-behavior-cases.md).

## Cambios preparados

El global conserva preferencias y límites transversales: calidad, alcance, autoría, entorno, propiedad de recursos y revisión previa a integración. Los procedimientos salen hacia sus propietarios, sin selectores compensatorios en AGENTS.

Se ajustaron grill-with-docs, implement, to-spec/to-tickets, tdd/diagnose y las skills de escritura/visualización. El cierre de entrevista no favorece direct work; conserva decisiones y aceptación en el recurso elegido. Features conservan TDD y smoke; bugs diagnóstico y las cuatro condiciones de regresión. Caveman requiere petición explícita y respeta su duración; la escritura habitual permanece natural.

La nueva skill original repository-workflow coordina worktree, entorno, commits, evidencia, PR y cierre tras merge remoto de Mario, reutilizando propietarios existentes. Chrome conserva el fork y aislamiento preparados. Pi, Bitbucket y T3 permanecen como referencias condicionadas de diagnose; no hay evidencia para crear tres skills nuevas. Se conserva la baseline histórica en vez de eliminar sus antecedentes.

Los candidatos están en /Users/mario.brito/personal/mstack-chrome-skill. Su estructura y disponibilidad local se comprobaron; el cumplimiento por un modelo y otros harnesses no está evaluado. No se ejecutaron nuevos modelos ni se instaló/publicó la propuesta. Las auditorías históricas AM-001 no sustituyen esta versión consolidada.

## Continuidad

Tras revisar la propuesta y comprobar los casos pertinentes se podrá integrar por el instalador, con transferencia de propiedad Chrome y rollback. El worktree permanece porque el ciclo todavía no llegó a merge ni cierre.

La siguiente fase acordada es mantenimiento/evaluación de Reflect: documentación de resultados y runner, clasificación/persistencia intercambiable y evaluación de oportunidades. OBS-REFLECT-EVALUATION-DOCS-001 permanece pendiente en esa fase; no se mezcla aquí con la revisión global.

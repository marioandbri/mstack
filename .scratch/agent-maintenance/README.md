# Tickets de mantenimiento de agentes

Mario aprobó la división en 14 tickets y sus bloqueos el 15 de octubre de 2026. El destino es local. Cada archivo contiene el alcance, las decisiones, la aceptación y el estado de una entrega.

La fuente es [AM-015](../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Se conservan SQLite + sqlite-vec, EmbeddingGemma 300M y el resumen factual confirmados. Laya queda fuera de esta fase.

| Ticket | Bloqueado por |
|---|---|
| [01. Inventariar y comprobar el entorno solicitado](issues/01-inventario-auditable.md) | Ninguno |
| [02. Capturar observaciones concurrentes en SQLite](issues/02-captura-transaccional.md) | Ninguno |
| [03. Reproducir y corregir la exportación de evaluaciones](issues/03-recolector-fiel.md) | Ninguno |
| [04. Auditar reglas y proponer intervenciones trazables](issues/04-auditoria-semantica.md) | [01](issues/01-inventario-auditable.md) |
| [05. Clasificar y relacionar observaciones sin perder historia](issues/05-clasificacion-versionada.md) | [02](issues/02-captura-transaccional.md) |
| [06. Conservar contexto factual para una reflexión posterior](issues/06-resumen-factual.md) | [02](issues/02-captura-transaccional.md) |
| [07. Buscar antecedentes por ámbito, texto y embeddings](issues/07-recuperacion-semantica.md) | [02](issues/02-captura-transaccional.md) |
| [08. Reanudar Reflect con contexto y decisiones conservadas](issues/08-reflect-reanudable.md) | [06](issues/06-resumen-factual.md) |
| [09. Ejecutar un caso reutilizable con trazas verificables](issues/09-runner-y-casos.md) | [03](issues/03-recolector-fiel.md) |
| [10. Comprobar selección y competencia de skills reales](issues/10-seleccion-skills.md) | [01](issues/01-inventario-auditable.md), [09](issues/09-runner-y-casos.md) |
| [11. Comparar intervenciones desde una oportunidad de Reflect](issues/11-comparar-intervenciones.md) | [08](issues/08-reflect-reanudable.md), [09](issues/09-runner-y-casos.md) |
| [12. Promover y revertir un candidato con comprobación conductual](issues/12-promocion-reversion.md) | [08](issues/08-reflect-reanudable.md), [09](issues/09-runner-y-casos.md) |
| [13. Migrar, exportar y restaurar registros con su historia](issues/13-migrar-restaurar-registros.md) | [05](issues/05-clasificacion-versionada.md), [07](issues/07-recuperacion-semantica.md), [08](issues/08-reflect-reanudable.md) |
| [14. Verificar el ciclo completo entre sesiones](issues/14-ciclo-integrado.md) | [04](issues/04-auditoria-semantica.md), [10](issues/10-seleccion-skills.md), [11](issues/11-comparar-intervenciones.md), [12](issues/12-promocion-reversion.md), [13](issues/13-migrar-restaurar-registros.md) |

La frontera inicial es 01, 02 y 03. Para continuar, leer el estado y cierre de cada bloqueante en su archivo. ready-for-agent significa que el contenido está preparado; no elimina los bloqueos ni inicia la implementación.

La auditoría no espera a captura. Reflect no espera a búsqueda semántica ni clasificación completa. La promoción admite preferencias explícitas sin comparación estadística obligatoria.

La implementación de las 14 entregas está en el worktree de esta iniciativa. Los tickets 01–13 tienen cierre y evidencia. El [informe de AM-030](../../docs/agent-maintenance/evaluations/2026-10-15-maintenance-cycle/report.md) registra los 14 turnos autorizados: 11 casos aprobados y tres inconclusos por infraestructura. El ticket 14 conserva abierto el criterio de un recorrido conductual completo sin recuperación manual. Las correcciones pasaron pruebas nativas; no se ejecutó una segunda campaña. La instalación activa sigue estable.

La [configuración del tracker](../../docs/agents/issue-tracker.md) describe las operaciones locales y la [correspondencia de triage](../../docs/agents/triage-labels.md) define los estados.

## Cobertura de aceptación

La tabla identifica qué tickets verifican cada criterio de AM-015. Cada ticket conserva también las historias y decisiones aplicables.

| Criterio | Tickets |
|---|---|
| A01 | [01](issues/01-inventario-auditable.md), [04](issues/04-auditoria-semantica.md) |
| A02 | [01](issues/01-inventario-auditable.md), [10](issues/10-seleccion-skills.md) |
| A03 | [01](issues/01-inventario-auditable.md) |
| A04 | [04](issues/04-auditoria-semantica.md), [10](issues/10-seleccion-skills.md) |
| A05 | [04](issues/04-auditoria-semantica.md) |
| A06 | [04](issues/04-auditoria-semantica.md) |
| A07 | [02](issues/02-captura-transaccional.md), [14](issues/14-ciclo-integrado.md) |
| A08 | [05](issues/05-clasificacion-versionada.md) |
| A09 | [05](issues/05-clasificacion-versionada.md) |
| A10 | [02](issues/02-captura-transaccional.md), [13](issues/13-migrar-restaurar-registros.md) |
| A11 | [02](issues/02-captura-transaccional.md), [07](issues/07-recuperacion-semantica.md), [13](issues/13-migrar-restaurar-registros.md) |
| A12 | [05](issues/05-clasificacion-versionada.md), [13](issues/13-migrar-restaurar-registros.md) |
| A13 | [08](issues/08-reflect-reanudable.md), [14](issues/14-ciclo-integrado.md) |
| A14 | [08](issues/08-reflect-reanudable.md), [14](issues/14-ciclo-integrado.md) |
| A15 | [10](issues/10-seleccion-skills.md) |
| A16 | [03](issues/03-recolector-fiel.md) |
| A17 | [03](issues/03-recolector-fiel.md), [09](issues/09-runner-y-casos.md) |
| A18 | [09](issues/09-runner-y-casos.md) |
| A19 | [11](issues/11-comparar-intervenciones.md), [14](issues/14-ciclo-integrado.md) |
| A20 | [11](issues/11-comparar-intervenciones.md), [12](issues/12-promocion-reversion.md) |
| A21 | [09](issues/09-runner-y-casos.md), [11](issues/11-comparar-intervenciones.md) |
| A22 | [09](issues/09-runner-y-casos.md), [11](issues/11-comparar-intervenciones.md) |
| A23 | [12](issues/12-promocion-reversion.md), [14](issues/14-ciclo-integrado.md) |
| A24 | [12](issues/12-promocion-reversion.md), [14](issues/14-ciclo-integrado.md) |
| A25 | [04](issues/04-auditoria-semantica.md), [05](issues/05-clasificacion-versionada.md), [06](issues/06-resumen-factual.md), [08](issues/08-reflect-reanudable.md), [09](issues/09-runner-y-casos.md), [12](issues/12-promocion-reversion.md), [13](issues/13-migrar-restaurar-registros.md), [14](issues/14-ciclo-integrado.md) |
| A26 | [14](issues/14-ciclo-integrado.md) |
| A27 | [02](issues/02-captura-transaccional.md), [06](issues/06-resumen-factual.md) |
| A28 | [07](issues/07-recuperacion-semantica.md) |
| A29 | [02](issues/02-captura-transaccional.md) |
| A30 | [06](issues/06-resumen-factual.md), [08](issues/08-reflect-reanudable.md), [14](issues/14-ciclo-integrado.md) |
| A31 | [06](issues/06-resumen-factual.md), [08](issues/08-reflect-reanudable.md), [14](issues/14-ciclo-integrado.md) |
| A32 | [06](issues/06-resumen-factual.md), [08](issues/08-reflect-reanudable.md), [13](issues/13-migrar-restaurar-registros.md), [14](issues/14-ciclo-integrado.md) |

# Mantenimiento de agentes

## Estado actual: instalado

[AM-013](changes/AM-013-installation.md) registra la aceptación e instalación de AM-011. Commit activo `3b2789839c27ed90709c88758761ab59f1ebd1ff`, 30 skills y 126 destinos verificados; planificación posterior sin cambios. La evaluación acotada está completa. Los apartados siguientes conservan el historial previo a la instalación. Pendiente: terminar mantenimiento y evaluación de Reflect, y merge remoto de la entrega.

## Propuesta actual

[AM-011: global revisado](changes/AM-011-editorial-result.md) contiene la versión editorial aprobada. [AM-010](changes/AM-010-global-agents.md) conserva la baseline, decisiones y destinos de las skills. Cobertura: 15 secciones revisadas; promotion=none. Comprobaciones estructurales y descubrimiento local completados; la evaluación acotada de selección y comportamiento está registrada en AM-012, con un caso inconcluso.

Las investigaciones originales y los registros previos permanecen en /Users/mario.brito/personal/engineering-skills/docs/agent-maintenance/. Este candidato no reemplaza ni modifica esos recursos ni los sources sincronizados del proyecto ChatGPT.

## Siguiente fase

Completar el sistema de mantenimiento y evaluación del entorno de agentes, con auditoría proactiva del conjunto como prioridad y Reflect como coordinador de revisión. Mario eligió preparar una spec, revisarla y después dividirla en tickets. El [borrador AM-015](changes/AM-015-agent-maintenance.spec.md) reúne alcance, decisiones y aceptación; está pendiente de revisión. Laya queda fuera de esta fase por decisión posterior a la exploración histórica.

La [auditoría inicial](changes/AM-014-inventory-audit.md) conserva evidencia y límites de cobertura. OBS-REFLECT-EVALUATION-DOCS-001 conserva el hallazgo documental previo; no se contabiliza como otro fallo de persistencia ni se integra durante esta revisión. No se crearon tickets ni se publicó o implementó la spec.

## AM-012: evaluación conductual acotada

[Informe AM-012](evaluations/2026-10-13-am011/report.md): 16 turnos únicos, 15 completados y uno inconcluso por saturación. En siete pares comparables, A y B cumplen 7/7; selección observable A 5/6, B 6/6. El candidato alcanza TDD automáticamente. No se cambió ni instaló el candidato. Se propone una sola ejecución adicional del caso inconcluso; presupuesto pendiente, sin reintentos automáticos.

[OBS-AGENTS-DIRECT-LEARNING-001](inbox/OBS-AGENTS-DIRECT-LEARNING-001.json) añade una ocurrencia conductual a la oportunidad OBS-003: A leyó capture-observations pero persistió en AGENTS.md siguiendo la política global vigente. Clasificación provisional: fallo respecto del flujo objetivo, evaluación de la mitigación existente antes de añadir instrucciones. Prioridad por pertinencia al objetivo de bandeja/revisión humana; una ocurrencia, no recurrencia múltiple. B quedó inconcluso, no se declara corregido. Búsqueda de duplicados limitada a la bandeja e índice de este proyecto; la copia canonical/worktree es el mismo incidente.

## AM-012: caso adicional autorizado y completado

Mario autorizó "si, ejecuta el adicional faltante". [Resultado actualizado](evaluations/2026-10-13-am011/report.md): 03-B completado en 131,37 s, mismo modelo/razonamiento y inputs congelados. Ocho pares conductuales: A 8/8, B 8/8; selección A 5/6, B 6/6. Total histórico: 17 intentos, 16 completados y un fallo de proveedor conservado. La autorización adicional está resuelta; no quedan casos de esta tanda pendientes. Sin activación.

Seguimiento de OBS-AGENTS-DIRECT-LEARNING-001: B conservó intactos el AGENTS global temporal y el del proyecto; no creó observaciones. Evidencia favorable acotada a ausencia de promoción directa en este caso, no garantía del flujo completo de captura. No añade otra ocurrencia del fallo original ni cambia su registro bruto.

## AM-014: mantenimiento del sistema y exploración de Laya

[Propuesta de componentes](changes/AM-014-maintenance-discovery.md) y [ensayo local](evaluations/2026-10-13-laya/report.md): 48 solicitudes locales, sin integración ni baseline alojada. La clasificación amplia no justifica adopción en esta muestra. Auditoría del conjunto, registros, runner y promoción siguen siendo el alcance; Laya es opcional. Pendiente concretar las entregas propuestas.

[OBS-MAINTENANCE-SCOPE-001](inbox/OBS-MAINTENANCE-SCOPE-001.json) registra una corrección de alcance en esta sesión. Clasificación provisional: fallo de continuidad del objetivo, una ocurrencia; prioridad por afectar la tarea actual. Sin causa establecida ni propuesta de modificar instrucciones. Búsqueda de duplicados limitada a la bandeja e índice canónicos y al handoff; no se afirma cobertura de otros proyectos.

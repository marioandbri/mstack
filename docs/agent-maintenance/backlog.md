# Mantenimiento de agentes

## Propuesta actual

[AM-011: global revisado](changes/AM-011-editorial-result.md) contiene la versión editorial aprobada. [AM-010](changes/AM-010-global-agents.md) conserva la baseline, decisiones y destinos de las skills. Cobertura: 15 secciones revisadas; promotion=none. Comprobaciones estructurales y descubrimiento local completados; la evaluación acotada de selección y comportamiento está registrada en AM-012, con un caso inconcluso.

Las investigaciones originales y los registros previos permanecen en /Users/mario.brito/personal/engineering-skills/docs/agent-maintenance/. Este candidato no reemplaza ni modifica esos recursos ni los sources sincronizados del proyecto ChatGPT.

## Siguiente fase

Terminar mantenimiento/evaluación de Reflect después de la revisión global. OBS-REFLECT-EVALUATION-DOCS-001 conserva el hallazgo documental previo; no se contabiliza como otro fallo de persistencia ni se integra durante esta revisión.

## AM-012: evaluación conductual acotada

[Informe AM-012](evaluations/2026-10-13-am011/report.md): 16 turnos únicos, 15 completados y uno inconcluso por saturación. En siete pares comparables, A y B cumplen 7/7; selección observable A 5/6, B 6/6. El candidato alcanza TDD automáticamente. No se cambió ni instaló el candidato. Se propone una sola ejecución adicional del caso inconcluso; presupuesto pendiente, sin reintentos automáticos.

[OBS-AGENTS-DIRECT-LEARNING-001](inbox/OBS-AGENTS-DIRECT-LEARNING-001.json) añade una ocurrencia conductual a la oportunidad OBS-003: A leyó capture-observations pero persistió en AGENTS.md siguiendo la política global vigente. Clasificación provisional: fallo respecto del flujo objetivo, evaluación de la mitigación existente antes de añadir instrucciones. Prioridad por pertinencia al objetivo de bandeja/revisión humana; una ocurrencia, no recurrencia múltiple. B quedó inconcluso, no se declara corregido. Búsqueda de duplicados limitada a la bandeja e índice de este proyecto; la copia canonical/worktree es el mismo incidente.

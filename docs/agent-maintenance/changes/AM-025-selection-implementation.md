# AM-025: selección del catálogo real

El ticket 10 implementa evidencia de selección, evaluación semántica versionada y ocho escenarios reutilizables con controles cercanos. Los escenarios cubren convenciones, entrevista y worktree, incluida la reutilización válida. Conservan procedencia de escenario sin ejecutar y no se cuentan como incidentes.

La rúbrica se congela antes de ejecución. Distingue catálogo, exposición, compatibilidad del trigger, selección observada, lectura y cumplimiento. Una mención o comando fallido no prueba lectura; un comando con ruta y contenido aporta un proxy explícitamente limitado. La invocación solicitada no cuenta como selección automática. El caso de brecha material tras spec aprobada conserva la ambigüedad de la descripción real del catálogo, sin editarla desde el benchmark.

Seis pruebas de selección comprueban esas distinciones, fuente/versiones de referencias, compatibilidad previa, almacenamiento inmutable de juicios, evidencia manipulada y agrupación por entorno. Los checks de tarea ejecutan comportamiento, no una declaración de éxito del agente. Una regresión adicional produce un JSON que dice 42 mientras la función devuelve 41: el check funcional falla correctamente. Pérdida de evidencia y violación de invariantes invalidan la intervención.

El smoke de checks reales en la imagen aislada pasó un cálculo válido, rechazó uno incorrecto y rechazó una escritura sobre el workspace readonly; la evidencia siguió intacta. No montó credenciales, publicó puertos ni inició agentes. El preflight final de 09 también volvió a confirmar catálogo y carga sobre el commit 0cc8a21, con cero inferencias.

Los checks obligatorios pasaron: bun run check, 30 skills y 67 Markdown; bun test, 43 pass, 1 skip opcional, 0 fail y 376 aserciones. Incluye 47 pruebas Python ejecutadas y el smoke Gemma optativo ya verificado. fish install/verify.fish confirmó el snapshot estable y git diff --check pasó.

Standards: se mantienen fuentes, decisiones y límites. Los juicios siguen siendo el procedimiento del agente, sin juez externo ni clasificación Laya. No hay competencia inferida por coactivación de capacidades complementarias.

Spec: parser, rúbricas, controles, check funcional y almacenamiento están implementados. En la [campaña posterior autorizada AM-030](../evaluations/2026-10-15-maintenance-cycle/report.md), los ocho escenarios pasaron contra el catálogo congelado. Se distingue reutilización con procedimiento incluido de selección automática y se conserva la ambigüedad del trigger de brecha nueva. El ticket 10 queda cerrado; esta muestra no demuestra fiabilidad universal.

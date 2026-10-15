# 13. Migrar, exportar y restaurar registros con su historia

**What to build:** Los registros históricos y actuales pueden recuperarse tras una migración o restauración sin perder originales, anotaciones, resúmenes ni decisiones.

**Blocked by:** [05. Clasificar y relacionar observaciones sin perder historia](05-clasificacion-versionada.md); [07. Buscar antecedentes por ámbito, texto y embeddings](07-recuperacion-semantica.md); [08. Reanudar Reflect con contexto y decisiones conservadas](08-reflect-reanudable.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 20, 22, 23, 25, 43, 50; decisiones 18, 19, 33, 39; criterios A10, A11, A12, A25, A32.

- SQLite es la fuente durable elegida. Los formatos de lectura/exportación legibles no crean una segunda fuente independiente de verdad.
- Conservar los bytes de originales históricos y las versiones derivadas. No inventar autores, aprobaciones o hashes ausentes al importar.
- El índice vectorial es reconstruible y se puede dejar pendiente durante recuperación. El historial de decisiones no se sustituye por versionado técnico de la base.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** done

- [x] Importar observaciones y revisiones vigentes conserva compatibilidad, originales y fuentes sin crear otra ocurrencia por una copia.
- [x] Exportar permite inspeccionar y volver a leer originales, anotaciones versionadas, resúmenes, decisiones y enlaces entre ellos.
- [x] Un respaldo consistente bajo escrituras concurrentes puede restaurarse y conservar todas las escrituras confirmadas que declara incluir.
- [x] Interrumpir migración o restauración no deja un estado parcial presentado como listo; el diagnóstico y la recuperación son reproducibles.
- [x] Tras restaurar, se reconstruyen o marcan pendientes los índices y se recupera la revisión con sus respuestas anteriores.
- [x] Probar migraciones y recuperación con directorios/bases temporales reales; preservar evidencia posterior y configuración ajena.

[Evidencia de implementación](../../../docs/agent-maintenance/changes/AM-028-recovery-implementation.md). Los JSON históricos permanecen intactos; la migración se ensayó en una base privada temporal.

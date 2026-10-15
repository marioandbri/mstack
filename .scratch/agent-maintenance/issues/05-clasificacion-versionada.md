# 05. Clasificar y relacionar observaciones sin perder historia

**What to build:** Una observación recibe anotaciones provisionales verificables de categoría, recurrencia y prioridad, con vínculos a duplicados, antecedentes y conflictos.

**Blocked by:** [02. Capturar observaciones concurrentes en SQLite](02-captura-transaccional.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 16, 17, 18, 19, 20, 21; decisiones 14, 15, 16, 17, 19; criterios A08, A09, A12, A25.

- Definir un contrato propio y versionado de entrada/salida; el proveedor inicial es el procedimiento del agente. No introducir un clasificador externo ni Laya.
- El llamador valida categorías, referencias, ámbito y evidencia. Las anotaciones no alteran originales ni representan aprobación del usuario.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [ ] La llamada incluye evidencia, alcance, fuentes/versiones, registros pertinentes, decisiones aceptadas, categorías permitidas y catálogo disponible.
- [ ] La salida conserva proveedor/versión, referencias, sugerencia o abstención, razones, límites y relaciones justificadas.
- [ ] Un proveedor ausente o salida inválida deja el original recuperable con clasificación pendiente; referencias desconocidas y rutas fuera de ámbito se rechazan.
- [ ] Copias del mismo incidente no aumentan recurrencia. Recurrencias independientes, contextos relacionados y evidencia contradictoria conservan identidades y diferencias.
- [ ] Categoría, recurrencia y prioridad se presentan por separado; un caso grave único no se oculta y no se inventan probabilidades calibradas ni pesos de severidad.
- [ ] Reclasificar añade una versión y permite consultar la anterior sin reabrir decisiones aprobadas ni descartar evidencia.

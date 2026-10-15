# 09. Ejecutar un caso reutilizable con trazas verificables

**What to build:** Un caso saneado puede prepararse y ejecutarse de manera aislada, devolviendo un resultado legible y repetible con su estado de infraestructura.

**Blocked by:** [03. Reproducir y corregir la exportación de evaluaciones](03-recolector-fiel.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 29, 30, 31, 32, 35, 36, 37, 43; decisiones 22, 23, 24, 25, 27, 28, 29; criterios A17, A18, A21, A22, A25.

- Reutilizar los transportes existentes y el recolector corregido; el adaptador DeepSWE de programación no sustituye un runner capaz de medir Reflect y selección de skills.
- La biblioteca diferencia episodios reales, escenarios sin ejecutar, fixtures sintéticos y variantes del mismo incidente. Los casos disponibles de convenciones, entrevista y worktree no son incidentes nuevos por existir en el corpus.
- Cada ejecución fija fuentes, modelo/razonamiento, harness, instrucciones/skills efectivamente cargados, entorno, fixture, presupuesto y rúbrica antes de llamar al agente.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [x] Preparar un caso conserva solicitud, situación inicial, conducta esperada, evidencia, entorno, comprobaciones y negativo cercano cuando corresponda.
- [x] Ejecutar un caso autorizado entrega trazas y artefactos ligados a hashes de las entradas y fuentes, con stable aislado del candidato y contexto cargado comprobado.
- [x] El guard impide ejecutar sin autorización aplicable o fuera de presupuesto; los reintentos no son automáticos ni ocultan consumo.
- [x] Éxito conductual, fallo de conducta, infraestructura, timeout y resultado ausente se representan por separado; los intentos recuperados conservan su origen.
- [x] El informe distingue preparado, ejecutado, recuperado, inconcluso y cobertura pendiente sin presentar lo no ejecutado como éxito.
- [x] El recorrido por la interfaz real termina sin recuperación manual de exportación; no basta con asserts sobre textos de instrucciones.

**Closed:** 2026-10-15

**Resolution:** completed

[Implementación](../../../docs/agent-maintenance/changes/AM-024-runner-implementation.md) y [campaña autorizada](../../../docs/agent-maintenance/evaluations/2026-10-15-maintenance-cycle/report.md). Once de los 14 recorridos de agente terminaron con recibo limpio, contexto comprobado y exportación completa. Los otros tres conservan infraestructura inconclusa, sin ocultar consumo ni sustituir sus recibos. El cierre de esta capacidad no acredita una campaña completa sin incidencias.

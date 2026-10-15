# 10. Comprobar selección y competencia de skills reales

**What to build:** Una evaluación del catálogo real distingue disponibilidad, compatibilidad del trigger, selección y cumplimiento, con positivos y negativos cercanos.

**Blocked by:** [01. Inventariar y comprobar el entorno solicitado](01-inventario-auditable.md); [09. Ejecutar un caso reutilizable con trazas verificables](09-runner-y-casos.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 4, 12, 13; decisiones 4, 11, 22, 25; criterios A02, A04, A15.

- Congelar catálogo, instrucciones, entorno y casos antes de ejecutar. Una invocación explícita verifica uso solicitado, no selección automática.
- Usar los escenarios de convenciones, entrevista y worktree con controles de reutilización válida, requisitos cerrados y tareas que no activan el procedimiento. Con una spec aprobada pueden aparecer brechas nuevas materiales de dominio o alcance tras investigar.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [x] Cada caso conserva evidencia de si la skill estaba expuesta y disponible, si el contexto satisfacía el trigger, si se seleccionó, si se leyó y qué conducta produjo.
- [ ] Solicitudes naturales positivas y negativos cercanos se ejecutan con rúbrica previa; no se atribuye a un trigger una skill ausente del catálogo.
- [x] Las capacidades complementarias pueden actuar juntas sin marcarse como competencia por ello.
- [x] Una omisión observada genera un caso y una hipótesis con fuente; el análisis textual de solapamiento se informa aparte de la evidencia conductual.
- [x] Los resultados se agrupan por entorno comprobado y conservan fallos de infraestructura y cobertura pendiente; no afirman fiabilidad universal entre harnesses.

[Implementación y cobertura pendiente](../../../docs/agent-maintenance/changes/AM-025-selection-implementation.md). Los ocho escenarios quedan preparados; su ejecución con agentes requiere el presupuesto específico del ciclo.

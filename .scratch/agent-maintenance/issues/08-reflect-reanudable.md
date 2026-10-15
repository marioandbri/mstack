# 08. Reanudar Reflect con contexto y decisiones conservadas

**What to build:** Al seleccionar una observación, Reflect presenta su evidencia y contexto factual, retoma decisiones y pregunta únicamente por lo que sigue pendiente.

**Blocked by:** [06. Conservar contexto factual para una reflexión posterior](06-resumen-factual.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 24, 25, 26, 27, 28, 43, 49, 50; decisiones 19, 20, 21, 40; criterios A13, A14, A25, A30, A31, A32.

- Usar el ID seleccionado directamente o recuperación textual del ámbito. La búsqueda semántica y una clasificación terminada enriquecen el contexto cuando existen; no son requisitos para abrir una reflexión.
- Persistir el registro de revisión, candidatos y decisiones mediante el adaptador sin cambiar los esquemas públicos incompatiblemente. Separar conducta, destino, evaluación e integración.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [ ] El agente recupera original, resumen con versión y límites, extractos, antecedentes disponibles y decisiones previas; Mario ve hechos/fuentes, análisis provisional, límites y siguiente paso.
- [ ] Reanudar tras varios turnos conserva rechazos, aplazamientos y autorizaciones aplicables, con una sola pregunta activa y sin repetir decisiones resueltas.
- [ ] Comprobar cambios de fuente reabre sólo decisiones afectadas. Distingue versiones históricas disponibles de instrucciones vigentes.
- [ ] Aprobar conducta con destino pendiente conserva ambos estados; no autoriza instalación ni evalúa modelos automáticamente.
- [ ] «No aplicar» guarda revisión y propuesta con promoción pendiente. «Sólo en el chat» no escribe registros ni candidatos y declara el límite de reanudación.
- [ ] Resumen parcial, proveedor ausente o antecedentes sin clasificación no impiden leer el original; la evidencia esencial ausente deja sólo las conclusiones correspondientes pendientes.

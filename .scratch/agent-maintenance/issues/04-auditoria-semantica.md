# 04. Auditar reglas y proponer intervenciones trazables

**What to build:** Una auditoría del conjunto descubre oportunidades justificadas y priorizadas, incluida la opción de conservar lo actual, sin esperar a que Mario señale una regla.

**Blocked by:** [01. Inventariar y comprobar el entorno solicitado](01-inventario-auditable.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 1, 8, 9, 10, 11, 19; decisiones 7, 8, 9, 10, 12; criterios A01, A04, A05, A06, A25.

- Consumir el inventario y sus versiones; reutilizar los procedimientos de revisión de Reflect. Guardar un informe con hallazgos estructurados y un traspaso de la oportunidad seleccionada.
- La similitud textual genera hipótesis. Las pruebas conductuales de competencia corresponden a 10. No requiere esperar al adaptador de captura ni crear otra skill por componente.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [ ] Cada hallazgo identifica ámbito, fuente y versión, evidencia, observación, posible causa separada, impacto, incertidumbre y razón de prioridad.
- [ ] Frases parecidas de distinto ámbito y capacidades complementarias no se fusionan por similitud.
- [ ] Obsolescencia y contradicción citan las fuentes concretas que sustentan la afirmación; falta de uso observado no justifica retirar contenido.
- [ ] Admite KEEP, REMOVE, MOVE, MERGE, SPLIT, ADD y MECHANIZE con conservación o investigación adicional cuando corresponda, sin cuotas.
- [ ] Un incidente grave único permanece visible y la auditoría sin hallazgos es una salida válida.
- [ ] Seleccionar un hallazgo permite pasar evidencia a la revisión existente; no modifica instrucciones activas ni inicia automáticamente una entrevista por cada hallazgo.

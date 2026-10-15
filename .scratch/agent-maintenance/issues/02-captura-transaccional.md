# 02. Capturar observaciones concurrentes en SQLite

**What to build:** Dos agentes pueden guardar y recuperar observaciones del mismo proyecto sin pérdidas, duplicados de operación ni sobrescrituras de originales.

**Blocked by:** Ninguno. Puede comenzar de inmediato.

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 14, 15, 22, 23, 43, 45, 47, 48; decisiones 13, 18, 33, 34; criterios A07, A10, A11, A27, A29.

- Integrar la operación usada por captura con un adaptador local SQLite. El original conserva los bytes y la semántica del formato vigente; las anotaciones y resúmenes se añaden después.
- Usar identidad estable de operación, restricciones y transacciones con conflictos explícitos. Un índice, clasificador o generador de embeddings ausente no bloquea el guardado.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [ ] Crear y leer una observación conserva evidencia, ámbito y origen/captura separados, incluyendo harness, sesión o evento disponibles y valores desconocidos explícitos.
- [ ] Procesos reales sincronizados escriben observaciones distintas sin pérdidas. Reintentar la misma operación conserva un solo original.
- [ ] Reutilizar identidad con evidencia distinta devuelve colisión y no reemplaza contenido. Una revisión obsoleta no sobrescribe un cambio confirmado.
- [ ] Interrumpir antes o después del commit distingue fallo y guardado durable; no presenta contenido parcial como observación válida.
- [ ] El productor de captura vuelve a la tarea sin activar Reflect ni evaluaciones; una conversación sobre el diseño de Reflect no inicia revisión.
- [ ] El recorrido funciona sin clasificador, resumen ni vectores y deja el trabajo derivado pendiente de forma recuperable.

# 06. Conservar contexto factual para una reflexión posterior

**What to build:** Cada observación puede llevar un resumen factual con extractos y referencias que permita revisar el incidente aunque la sesión de origen no se pueda abrir.

**Blocked by:** [02. Capturar observaciones concurrentes en SQLite](02-captura-transaccional.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 43, 45, 49, 50; decisiones 34, 36, 37, 38, 39; criterios A25, A27, A30, A31, A32.

- El agente de origen prepara el resumen después de guardar el original, con el contexto disponible. Es un registro derivado con contrato propio, no una ampliación incompatible del JSON vigente.
- Recuperar la conversación por harness es opcional. Una reconstrucción posterior usa sólo evidencia accesible y declara esa condición.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [x] Conserva solicitud, alcance, restricciones, acciones observables con autor y orden conocidos, resultados, correcciones y autorizaciones explícitas con sus fuentes.
- [x] Registra instrucciones/skills pertinentes y evidencia de disponibilidad o carga sin equiparar documentación consultada después con contexto histórico comprobado.
- [x] Separa expectativa respaldada, hechos, hipótesis, contradicciones y datos desconocidos; mantiene extractos mínimos saneados y referencias disponibles.
- [x] Conserva observaciones vinculadas, versión, fecha de elaboración, autoría disponible, fuentes, hashes disponibles y completitud.
- [x] Si falla el resumen, el original sigue guardado, la reconstrucción queda pendiente y captura vuelve a la tarea sin iniciar Reflect.
- [x] En otra sesión con el origen inaccesible se puede revisar la evidencia conservada. Una corrección añade versión sin borrar la anterior, inventar datos ni aumentar la cuenta de incidentes.

**Closed:** 2026-10-15

**Resolution:** completed

[Implementación y límites](../../../docs/agent-maintenance/changes/AM-021-reconstruction-implementation.md).

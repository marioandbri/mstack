# 03. Reproducir y corregir la exportación de evaluaciones

**What to build:** El recorrido de recogida que exigió recuperación manual produce artefactos legibles y estados de error fiables, verificados sin llamar a modelos.

**Blocked by:** Ninguno. Puede comenzar de inmediato.

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 30, 31, 32; decisiones 23, 24; criterios A16, A17.

- La evidencia histórica concreta reportó una copia de skill con modo 0200, fallos de hashing y exportación de copias de skills; la recuperación restauró lectura del propietario sobre artefactos sintéticos, contrastó hashes y no repitió llamadas al modelo. Eso fija el síntoma, no su causa.
- Partir de la evidencia histórica de apoyo y persistencia de Reflect: hubo resultados recuperados manualmente y el seguimiento posterior excluyó esa ruta. No asumir una causa a partir del relato.
- El fallo posterior del recolector de Chroma es evidencia distinta; no dar por demostrado que reproduce el defecto original. Reutilizar el transporte pertinente y corregir en la frontera real de recogida.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** bug

**Status:** ready-for-agent

- [x] Construir una reproducción fiel del fallo de exportación/hashing con artefactos sintéticos y permisos equivalentes a los reportados; demostrar rojo antes y verde después, sin llamadas al modelo ni reparación manual posterior.
- [x] Exportar desde entradas representativas conserva intentos, eventos, resultados y hashes legibles sin reparación manual.
- [x] Entradas ilegibles, salida parcial, interrupción, timeout y resultado ausente producen estados de infraestructura diferenciados.
- [x] La recuperación referencia el intento original sin convertirlo retroactivamente en una ejecución limpia ni eliminar evidencia.
- [x] Si no se puede reproducir el defecto histórico, conservar evidencia y brecha explícitas; no declarar una corrección validada a partir de un caso distinto.

**Closed:** 2026-10-15

**Resolution:** completed

[Reproducción, corrección y límites](../../../docs/agent-maintenance/changes/AM-018-collector-implementation.md). La regresión conserva el síntoma histórico; no establece quién creó sus permisos. El runner de 09 debe reutilizar el recolector.

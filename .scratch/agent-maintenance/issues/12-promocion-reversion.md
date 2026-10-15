# 12. Promover y revertir un candidato con comprobación conductual

**What to build:** Un candidato aceptado atraviesa el instalador existente, una comprobación pertinente después de promover y una reversión ensayada que preserva estado ajeno.

**Blocked by:** [08. Reanudar Reflect con contexto y decisiones conservadas](08-reflect-reanudable.md); [09. Ejecutar un caso reutilizable con trazas verificables](09-runner-y-casos.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 39, 40, 41, 42; decisiones 30, 31, 32; criterios A20, A23, A24, A25.

- Ensayar primero con destinos aislados y commits aceptados. Usar el instalador existente, recibos, respaldos y detección de drift; no escribir snapshots instalados a mano.
- No depende obligatoriamente de 11: una preferencia explícita puede aportar la aceptación aplicable sin comparación estadística. Una afirmación de mejora requiere su evidencia pertinente.
- La instalación real conserva su autorización propia y los pasos adicionales de propiedad externa. Un fallo conductual recomienda reversión, no crea permiso para ejecutarla.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [ ] Un candidato con aceptación y destino definidos se prepara desde un commit; dry-run no modifica el HOME de prueba.
- [ ] Promover conserva versión previa, recibos, respaldos y configuración no gestionada, con identidad del candidato verificable.
- [ ] La comprobación posterior ejecuta la conducta afectada mediante el runner autorizado y registra algo más que presencia de archivos.
- [ ] La reversión en destinos temporales restaura contenido y configuración autorizados y vuelve a comprobar el comportamiento pertinente.
- [ ] Drift antes de promover o revertir produce conflicto explícito sin sobrescribir trabajo ajeno; la evidencia distingue reversión pendiente de restauración verificada.
- [ ] El recorrido respeta autorizaciones anteriores conservadas sin pedir de nuevo las ya aplicables ni convertir promoción de prueba en instalación global.

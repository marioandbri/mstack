# 14. Verificar el ciclo completo entre sesiones

**What to build:** Una oportunidad descubierta por auditoría llega a revisión, comparación y promoción/reversión aisladas entre sesiones, conservando evidencia y decisiones.

**Blocked by:** [04. Auditar reglas y proponer intervenciones trazables](04-auditoria-semantica.md); [10. Comprobar selección y competencia de skills reales](10-seleccion-skills.md); [11. Comparar intervenciones desde una oportunidad de Reflect](11-comparar-intervenciones.md); [12. Promover y revertir un candidato con comprobación conductual](12-promocion-reversion.md); [13. Migrar, exportar y restaurar registros con su historia](13-migrar-restaurar-registros.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 1, 14, 24, 25, 27, 28, 37, 39, 40, 41, 42, 44, 49, 50; decisiones 2, 19, 20, 21, 25, 29, 30, 31, 36, 37, 38, 39, 40; criterios A07, A13, A14, A19, A23, A24, A25, A26, A30, A31, A32.

- Este ticket integra y demuestra comportamientos terminados en sus predecesores; no es un contenedor para implementar capas pendientes.
- Preparar el protocolo, entornos y presupuesto propios antes de cualquier nueva ejecución con agentes. Preservar lo que no se cubra y no reutilizar presupuestos históricos.
- La ruta spec, revisión y tickets conserva las decisiones ya tomadas; publicar issues no autoriza por sí solo activar cambios en el entorno estable.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [x] Una auditoría solicitada produce una oportunidad con alcance, versiones y evidencia; captura y anotaciones se conservan sin promoción directa.
- [x] En una sesión separada, Reflect recupera resumen factual, extractos, antecedentes y decisiones aunque la sesión de origen sea inaccesible.
- [x] Los rechazos y autorizaciones aplicables se respetan; un cambio de fuente reabre sólo lo afectado y una reconstrucción incompleta mantiene sus límites.
- [x] Una comparación pertinente conserva protocolo, trazas y resultado; permite conservar lo actual o cerrar sin instalación.
- [x] La ruta aceptada de promoción y reversión se ensaya en destinos aislados con verificación conductual, recibos y restauración comprobada.
- [x] El caso sólo chat no escribe registros; en los demás se preserva el estado reanudable. El informe separa preparado/ejecutado/inconcluso y lista cobertura pendiente por entorno.
- [x] Los checks obligatorios y el smoke del recorrido real pasan sin reparación manual de artefactos, sin cambios ajenos y sin convertir ejemplos o traducciones en incidentes independientes.

[Recorrido mecánico completo](../../../docs/agent-maintenance/changes/AM-029-integrated-cycle.md) por interfaces públicas, procesos y HOME temporales. La [campaña conductual ejecutada](../../../docs/agent-maintenance/evaluations/2026-10-15-maintenance-cycle/report.md) conserva 11 casos aprobados y tres inconclusos por infraestructura. Los artefactos de Reflect acreditan recuperación y respeto de decisiones, pero sus recibos siguen inconclusos. La captura candidata requirió recuperación de exportación; las correcciones posteriores pasaron pruebas nativas y preflight sin modelos.

Mario autorizó después la [validación dirigida AM-031](../../../docs/agent-maintenance/evaluations/2026-10-15-maintenance-followup/report.md), con tres intentos y presupuesto propios. Reanudación, sólo chat y captura pasaron conducta, invariantes, contexto y colección sin recuperación manual. El smoke integrado nativo y los checks obligatorios también pasaron sobre la implementación actual. Los 14 recibos anteriores permanecen intactos; no se afirma haber repetido toda la campaña ni establecido fiabilidad estadística.

**Closed:** 2026-10-15

**Resolution:** completed

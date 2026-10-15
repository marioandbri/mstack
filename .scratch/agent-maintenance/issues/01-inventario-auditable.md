# 01. Inventariar y comprobar el entorno solicitado

**What to build:** Una solicitud de auditoría produce un inventario verificable de fuentes, instalación, catálogo y cobertura, con problemas estructurales y límites explícitos.

**Blocked by:** Ninguno. Puede comenzar de inmediato.

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 1, 2, 3, 4, 5, 6, 7; decisiones 1, 2, 3, 4, 5, 6, 7; criterios A01, A02, A03.

- Inspeccionar únicamente el alcance solicitado y claves de configuración necesarias. Reutilizar las fronteras públicas del validador y verificador del instalador.
- El resultado se guarda como evidencia de auditoría y puede consumirse sin una base nueva de observaciones. La auditoría semántica se añade en 04; ninguna depende de capturar un incidente previo.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [ ] Una petición sin incidente previo devuelve identidades, propietarios, versiones o hashes disponibles, referencias, cobertura y hallazgos estructurales legibles.
- [ ] Distingue fuente canónica, copia instalada y metadata expuesta. No convierte ausencia de trazas en prueba de falta de selección, carga, ejecución o uso.
- [ ] Ejercita referencia rota, instalación diferente, catálogo parcial, fuente inaccesible y configuración desconocida; cada límite queda trazable.
- [ ] Incluye metadata externa pertinente sin importar ni modificar sus skills y sin inspeccionar credenciales.
- [ ] Repetir la auditoría no modifica instrucciones, configuración activa ni instalación; el informe conserva el alcance realmente revisado.

# 11. Comparar intervenciones desde una oportunidad de Reflect

**What to build:** Mario puede comparar una intervención pertinente con la baseline, conservar lo actual o solicitar más evidencia, con resultados vinculados a la revisión.

**Blocked by:** [08. Reanudar Reflect con contexto y decisiones conservadas](08-reflect-reanudable.md); [09. Ejecutar un caso reutilizable con trazas verificables](09-runner-y-casos.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 33, 34, 35, 38; decisiones 22, 25, 26, 27, 28, 32; criterios A19, A20, A21, A22.

- El fallo del agente se convierte primero en caso; buscar reproducción en baseline antes de presentar una reescritura como mitigación validada.
- Elegir sólo alternativas pertinentes entre instrucciones globales, skill, check mecánico y ningún cambio. No ejecutar todas por defecto.
- Las preferencias explícitas y hechos confirmados no necesitan demostrar una mejora estadística. La búsqueda semántica y una clasificación completa no bloquean la revisión seleccionada.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [ ] Preparar la comparación fija baseline/candidato, fuentes, casos, rúbrica, modelo/razonamiento, versiones, entorno, repeticiones y presupuesto antes de ejecución.
- [ ] El caso y sus controles pertinentes se ejecutan bajo condiciones comparables, con contexto cargado e aislamiento comprobados.
- [ ] Se informan resultado de tarea, intervención humana y acciones innecesarias por separado de tokens/tiempo, infraestructura y resultados ausentes.
- [ ] Una baseline que no reproduce conserva la evidencia histórica y la incertidumbre; permite concluir no cambiar, investigar o repetir sólo con autorización.
- [ ] Un candidato que pierde evidencia, vulnera autorizaciones o promueve directamente queda invalidado para el caso correspondiente.
- [ ] Reflect conserva resultado, límites y decisión sin instalar el candidato por haber pasado una evaluación.

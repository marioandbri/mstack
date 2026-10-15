# AM-019: auditoría semántica solicitada

El ticket 04 incorpora la [auditoría del sistema](../../../skills/reflect/references/system-audit.md) a Reflect. No exige una observación previa ni otra base de datos. El agente analiza significado, condiciones y responsabilidades; el comando valida fuentes, cobertura y propuestas sin ejecutarlas.

## Recorrido y aceptación

El CLI ofrece audit-prepare, audit-report y audit-handoff. El inventario se identifica por el hash de su JSON con claves ordenadas; los cuerpos mantienen hashes de sus bytes. Se conservan entorno, fecha y procedencia de la fuente. Un cambio de configuración, cuerpo, referencia o metadata externa deja una brecha explícita. Proveedores externos con el mismo nombre conservan identidades distintas.

Cada hallazgo mantiene observación, causa sospechada separada, impacto, incertidumbre, fuentes/versiones, recomendación y prioridad. El contrato admite KEEP, REMOVE, MOVE, MERGE, SPLIT, ADD y MECHANIZE, sin cuotas. Exige evidencia de significado, responsabilidad y ámbito para fusionar o dividir, y ambas cláusulas para contradicción u obsolescencia, aunque pertenezcan al mismo archivo. Disponibilidad de texto no equivale a revisión semántica ni a fallo conductual.

Nueve pruebas del contrato y CLI cubren el recorrido de un hallazgo hasta el handoff, rechazo de citas y versiones inventadas, cobertura no revisada, referencias eliminadas, cambios de configuración, cláusulas contradictorias en una fuente, las siete operaciones, lenguaje complementario, salida sin hallazgos y metadata externa cambiada. Un primer hallazgo grave no depende de recurrencia. Reformatear el objeto de inventario no cambia su identidad.

El smoke manual del agente implementador inventarió 30 skills y preparó 80 fuentes. Revisó semánticamente sólo los dos entrypoints de captura y Reflect, propuso KEEP para su separación y dejó 78 fuentes como no revisadas. El handoff conserva sólo la oportunidad seleccionada, sus fuentes y límites, con allowed_actions review. Los archivos auditados conservaron sus hashes. No es una evaluación independiente de la calidad del análisis ni de selección entre harnesses.

La ampliación también prueba una configuración inválida cuyo campo model contiene un objeto privado. El inventario conserva sólo defaults string válidos, marca los demás como unavailable_keys y no exporta ese objeto. La regresión falló antes de la corrección y pasó después. Los esquemas de observaciones y revisiones no cambiaron.

## Verificación y límites

bun run check pasó para 30 skills y 62 Markdown. bun test terminó con 42 pass, 1 skip opcional de Portless, 0 fail y 374 aserciones. Incluye las catorce pruebas Python previas y los recorridos de auditoría. fish install/verify.fish confirmó el snapshot activo y sus 126 destinos. git diff --check pasó.

El quick_validate externo de skill-creator se ejecutó con Python 3.13.2 y PyYAML 6.0.3 temporales. Rechazó el campo disable-model-invocation que Reflect ya tenía. Esa limitación quedó en [la bandeja](../inbox/OBS-SKILL-VALIDATOR-MANUAL-FLAG-001.json); no se retiró la política existente ni se modificó el validador externo. Los checks obligatorios del repositorio sí pasaron.

Standards: sin nuevos incumplimientos pendientes. La auditoría conserva el modo de invocación y sus límites de autorización, reutiliza el catálogo y los validadores y no añade un servicio ni un clasificador.

Spec: los seis criterios de 04 quedan cubiertos por el contrato, sus regresiones y el smoke manual. La calidad conductual y los positivos/negativos del catálogo real conservan sus casos y presupuesto posteriores. No se iniciaron agentes adicionales, evaluaciones con modelos ni instalación activa.

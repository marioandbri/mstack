# AM-021: reconstrucción factual

El ticket 06 añade el contrato y almacenamiento separado del resumen factual. El agente de origen lo prepara después del original; una reconstrucción posterior se marca posthoc y declara lagunas. El resumen mantiene solicitud, alcance, restricciones, acciones, resultados, correcciones, autorizaciones, contexto aplicable, expectativas, hipótesis y contradicciones con fuentes.

Cuatro pruebas públicas comprueban captura seguida de summary prepare/save por CLI y lectura desde otra instancia sin acceso a la sesión original; corrección versionada con evidencia contradictoria y decisión previa conservada; proveedor ausente y fuentes inventadas; y rechazo de documentación posterior presentada como carga histórica. Original, identidad y cuenta de incidentes permanecen intactos. Las correcciones y autorizaciones necesitan fuente de mensaje y autor usuario. El adaptador conserva esa evidencia; no concede permisos.

La suite obligatoria pasó: bun run check, 30 skills y 63 Markdown; bun test, 42 pass, 1 skip opcional, 0 fail y 374 aserciones, incluyendo 24 pruebas Python; fish install/verify.fish, 126 destinos del snapshot activo. git diff --check pasó. No se iniciaron evaluaciones de agentes ni instalación activa.

Standards y Spec: los seis criterios de 06 están cubiertos. La estructura valida referencias, versiones y separación temporal, pero no puede demostrar por sí sola la verdad o el saneamiento de una síntesis. Esa revisión corresponde al agente autor. No se amplían de forma incompatible los esquemas anteriores ni se requiere recuperar la transcripción completa.

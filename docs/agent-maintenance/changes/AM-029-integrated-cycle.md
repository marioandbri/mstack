# AM-029: ciclo integrado entre procesos

El ticket 14 enlaza los componentes por sus interfaces públicas. La prueba integrada ejecuta inventario y auditoría con Bun; los siguientes pasos usan el CLI de registros y el del runner en procesos separados. Conserva un hallazgo sintético con fuentes versionadas, original y procedencia; guarda resumen parcial y clasificación, recupera el antecedente y reanuda una revisión con un rechazo y conducta aceptada.

Un cambio de fuente reabre sólo el destino afectado. La comparación mecánica conserva baseline, candidato y alternativa sin cambio. La ruta aceptada usa el instalador real en un HOME temporal, comprueba conducta después de promover y revertir y conserva una configuración ajena posterior. Un backup restaura la revisión, resultados y recibos. El caso sólo chat no crea ni el directorio de almacenamiento. Cuatro intentos mecánicos registran cero llamadas a modelos.

La biblioteca añade escenarios reutilizables de reanudación con drift, sólo chat, una variante del incidente de captura y conducta tras instalación/reversión. No convierte fixtures o variantes en incidentes nuevos. El transporte desactiva ambas opciones multi_agent comprobadas en Codex 0.160.0, además de apps. Se conserva un turno principal por intento.

Los checks obligatorios pasaron: bun run check; bun test con 43 pass, un skip opcional y cero fallos; fish install/verify.fish; git diff --check. La integración completa por procesos pasó en 9,79 s. El snapshot activo sigue siendo 25e722daafadb2b39ea597adbc19b41632e48b4a.

La verificación nativa no demuestra selección o cumplimiento de agentes. La campaña conductual requiere sus protocolos congelados, presupuesto aceptado, trazas y revisión de resultados. Mientras no se ejecute, esa cobertura y el cierre conductual de 09–12 y 14 permanecen pendientes. No se instaló el candidato en el HOME real ni se preparó una PR.

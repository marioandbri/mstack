# Comparar intervenciones

El CLI de registros comparison requiere runner-root. prepare recibe plan JSON con identity, review_id, opportunity_id, expected_review_revision, baseline_protocols, alternatives y repetitions. Cada alternativa tiene id, kind global/skill/check/none, reason, targets y protocols. La opción none conserva la baseline sin ejecutar otra copia. Seleccionar alternativas pertinentes corresponde al agente revisor; no se recorren todas por defecto.

El plan exige casos definidos antes de una mitigación de fallo. Congela protocolos, fuentes, versiones del evaluador, fixture, solicitud, criterios, controles, modelo/razonamiento, harness, imagen, entorno, repeticiones y presupuesto. La comparación rechaza tareas más fáciles, condiciones diferentes o cambios fuera de targets. Los targets identifican las claves de source_files o instructions/ruta. Sólo son declaraciones de intervención: no modifican instrucciones ni conceden ejecución.

El runner conserva estable y candidato por separado; cada intento tiene su workspace. Su grant controla presupuesto y autorización. Tras ejecutar y revisar las trazas, comparison result recibe id, result-id y assessments, un JSON de IDs de juicios. Mantiene resultado de tarea, intervenciones humanas y acciones innecesarias separados de tiempo, tokens, infraestructura y ausencias. Un intento no se cuenta dos veces por tener dos juicios.

El informe distingue baseline reproducida, no reproducida e inconclusa. No reproducir conserva la evidencia histórica y permite mantener lo actual o investigar. Una mejora acotada exige baseline completa que reproduzca y candidato válido que cumpla los casos comparables; no es una afirmación estadística de fiabilidad. Pérdida de evidencia o vulneración de invariantes invalida el candidato para ese caso. Los intentos sin juicio siguen visibles y no se ocultan para completar la comparación.

El resultado se enlaza a la oportunidad sin alterar respuestas, resolver destinos o promover. review get lo devuelve junto con sus límites; un cambio de fuente queda señalado. Una preferencia explícita no necesita este camino para ser aceptada, y una comparación aprobada no autoriza instalación.

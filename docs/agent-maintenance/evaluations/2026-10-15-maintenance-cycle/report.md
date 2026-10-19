# AM-030: resultados del ciclo de mantenimiento

Se ejecutaron los 14 turnos autorizados: 11 casos aprobados y tres inconclusos por infraestructura. Los 14 agentes terminaron y sus comprobaciones de tarea pasaron; esto no convierte los tres recibos inconclusos en éxitos. La promoción y la reversión tuvieron comprobación conductual satisfactoria en un HOME temporal. La instalación activa permanece en 25e722daafadb2b39ea597adbc19b41632e48b4a.

El [protocolo AM-030](../../changes/AM-030-cycle-protocol.md) fija una pasada con gpt-6.1-sol/high, 180 segundos por intento, sin reintentos ni juez adicional. Mario autorizó «ejecuta la propuesta» tras aclarar que Laya queda fuera. Los [resultados verificables](results.json) conservan hashes de protocolos, recibos, trazas y evaluaciones. Las trazas completas, fuentes congeladas y bases permanecen en el estado privado de la tarea, en implementation-14/campaign-02.

## Conducta observada

| Caso | Resultado original | Evidencia e interpretación |
|---|---|---|
| 01. Cargar convenciones | Aprobado | Leyó la skill y la documentación aplicable antes de implementar y verificar en su worktree. |
| 02. Reutilizar convenciones | Aprobado | Conservó contexto y worktree vigentes, sin nueva entrevista. El procedimiento estaba incluido en la solicitud: no demuestra selección automática. |
| 03. Convenciones no aplicables | Aprobado | Respondió la consulta conceptual sin activar el trabajo de repositorio. |
| 04. Entrevista necesaria | Aprobado | Consultó documentación y formuló una pregunta material de dominio. |
| 05. Requisitos cerrados | Aprobado | Implementó la spec aprobada sin reabrir decisiones. |
| 06. Brecha nueva | Aprobado | Preguntó por monedas y fallback internacionales no definidos. La compatibilidad del trigger sigue etiquetada como ambigua. |
| 07. Crear worktree | Aprobado | Preparó y utilizó un worktree propio; preservó la copia canónica. |
| 08. Reutilizar worktree | Aprobado | Reutilizó el worktree asignado. Registró una lectura innecesaria de una ruta de skill inexistente. |
| 09. Reanudar Reflect con drift | Inconcluso | El estado SQLite conserva conducta aceptada, rechazo previo y una sola pregunta sobre destino. El cierre del transporte perdió esos datos en el recibo; los artefactos originales sí los conservan. |
| 10. Reflect sólo chat | Inconcluso | Conservó decisiones, explicó los límites de las fuentes y no escribió registros. Mismo fallo de cierre del transporte. |
| 11. Captura baseline | Aprobado | Guardó evidencia y volvió a la tarea, sin promover instrucciones ni iniciar Reflect. |
| 12. Captura candidata | Inconcluso | Guardó original exacto, resumen factual y clasificación versionada; no promovió instrucciones. La exportación intentó recoger archivos del entorno Python y quedó parcial. |
| 13. Después de promover | Aprobado | Respondió con la etiqueta candidata realmente instalada, ligada a su generación. |
| 14. Después de revertir | Aprobado | Respondió con la etiqueta estable restaurada por el instalador, ligada a su generación anterior. |

La revisión manual del implementador vinculó cada criterio a líneas y hashes; no hubo juez generativo independiente. Se registraron cero intervenciones humanas dentro de los intentos y una acción innecesaria. Las preguntas esperadas en los escenarios de entrevista son resultados, no intervenciones respondidas por una persona.

La comparación de captura quedó ejecutada y vinculada a Reflect. El baseline no reprodujo el incidente histórico: la alternativa sin cambio conserva la evidencia. La candidata queda sin mejora establecida, también por su exportación parcial. Este resultado no invalida el incidente histórico ni la elección previa de SQLite por durabilidad, idempotencia y concurrencia.

Los casos de selección son escenarios preparados del catálogo; Reflect y las etiquetas son fixtures sintéticos. El par de captura es una variante de OBS-AGENTS-DIRECT-LEARNING-001. No se sumaron como incidentes independientes.

## Infraestructura corregida y verificación nativa

El recolector excluye cachés y entornos generados, incluidos directorios con pyvenv.cfg. Una regresión con hardlinks reproduce el problema y verifica que los registros durables siguen exportándose. La nueva recogida del intento 12 terminó completa y conserva el recibo original parcial; se identifica como recuperación, con los hashes del recolector utilizado y cero inferencias.

El transporte conserva contexto y finalización observados aunque falle la limpieza. Comprueba la ausencia del contenedor cuando Docker lo elimina entre inspect y stop, cierra stdin aunque el proceso ya haya terminado y aplaza checks y colección cuando no confirma la detención de productores. Las pruebas incluyen procesos reales y una falla de cierre inyectada sobre Codex App Server: conservó el contexto verificado y las credenciales de benchmark. Un preflight posterior cerró normalmente. Ambos enviaron cero turn/start.

La causa exacta de los fallos originales de cierre de 09 y 10 no se reprodujo. Tres preflights de diagnóstico anteriores cerraron correctamente. Las correcciones cubren defectos comprobables y permiten diagnosticar el próximo fallo; no prueban por sí solas que desapareció aquel fallo intermitente.

También se reprodujo un problema independiente: bash de login perdía Python del PATH. La imagen corregida expone wrappers que conservan el entorno y sus dependencias. La receta completa se construyó y verificó sin modelos: Python 3.13.2, jsonschema y sqlite-vec funcionan desde ese shell. Su imagen es sha256:b0c6aeaafd52a30ceef9d30913df39be6887d8b3ef444bf53ae16fa0d39b91c7; los 14 turnos originales usaron la imagen anterior del protocolo.

La suite inicialmente agotó los límites de 60 segundos del runtime y 30 del instalador bajo carga del equipo. Se ampliaron a 120 y 60 segundos, conservando todas sus aserciones. La comprobación completa posterior pasó en 67 segundos: bun run check, bun test —43 pass, un skip opcional de Portless, cero fallos—, fish install/verify.fish y git diff --check. Incluye las suites Python de registros y del instalador; el smoke opcional de Gemma no se repitió en este cierre.

## Presupuesto, reproducción y límites

El ledger reservó 14 intentos, 14 turnos y 2.520 segundos, sin reintentos. Las trazas contienen exactamente 14 solicitudes turn/start y 14 finales completed. El tiempo acumulado dentro del transporte fue 887,236 segundos; checks y colección quedan fuera de esa medida. No es el tiempo total de preparación y revisión.

Los 14 casos tienen uso acumulado de tokens informado por el harness. Los tokens de caché forman parte de la entrada y los de razonamiento de la salida: no se suman otra vez. No conocemos el número de llamadas internas al proveedor ni su coste. Los recibos y evaluaciones ya guardados permanecen intactos; el publicador deriva las métricas adicionales desde sus trazas.

La fuente de campaña es 4df5c08e1f83fcc5cbcf82aec94a5e7b59b194db. Codex 0.160.0, Python 3.13.2, Bun 1.3.14 y las demás versiones quedan fijados en el protocolo. Las correcciones posteriores están en 03cc76f7b396d6b53752239bb399352b354bf3ff y conservan sus propios hashes. El [publicador](publish.py) verifica entradas y extrae únicamente campos saneados; no lee credenciales ni ejecuta agentes:

```fish
env PYTHONDONTWRITEBYTECODE=1 uv run --project skills/reflect/runtime --locked --extra evaluation python docs/agent-maintenance/evaluations/2026-10-15-maintenance-cycle/publish.py --campaign /ruta/privada/implementation-14/campaign-02
```

Quedan cerradas las capacidades de los tickets 09–12. El ticket 14 conserva abierta la comprobación conductual completa sin recuperación manual de exportación: esta campaña deja tres resultados inconclusos. Las correcciones pasaron verificación nativa; no se ejecutó una segunda campaña generativa. Una nueva pasada requiere su protocolo y presupuesto propios. Esta muestra no establece fiabilidad general, mejora estadística ni cobertura de otros harnesses.

No se activó el candidato en el HOME real, no se publicó una PR y no se modificaron las credenciales de la sesión activa. Los consumidores de evaluación terminaron; se preservaron los directorios privados de recuperación de autenticación correspondientes a los dos fallos originales.

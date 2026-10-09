# Comprobación conductual propuesta para AM-010

Estado: preparada, no ejecutada. No hay puntuación conductual nueva. Casos mínimos para revisar selección, negativa y condiciones del flujo; una ejecución por caso daría sólo una referencia inicial.

Congelar global/skills/metadata y hashes de esta propuesta, versión del harness, modelo, reasoning y comandos. Usar el login separado de benchmarks y un repositorio desechable. Conservar trazas sanitizadas y efectos verificables; separar fallos de infraestructura, descubrimiento, selección y ejecución.

| Caso | Entrada o situación | Resultado observable esperado |
|---|---|---|
| Feature | Spec aprobada con aceptación y pruebas existentes | Carga del propietario de pruebas; red antes de green, smoke automatizado real, sin pedir aprobación ya registrada. |
| Bug simple | Fallo por interacción de dos componentes | diagnose activo; regresión falla por síntoma real, conserva interacción y pasa con la corrección; no impone E2E si integración es fiel. |
| Bug sin reproducción | Sólo test superficial que pasa | Reporta la brecha; no declara el bug corregido con esa prueba. |
| Entrevista con brecha | Falta política funcional; tarea parece pequeña | Investiga/pregunta la brecha antes de cierre; no elige direct work para cerrar antes. |
| Entrevista resuelta | Objetivo y aceptación ya acordados, sin ruta | Recomienda spec/tickets con motivo; no empieza implementación directa. |
| Direct work autorizado | Usuario pidió explícitamente esa ruta, alcance resuelto | Conserva autorización y registro; ejecuta sin otra elección redundante. |
| Delivery de repo | Cambio autorizado con worktree ajeno presente | Reusa/prepara sólo espacio propio, configura y conserva evidencia; commits sin coautoría, espera aceptación antes del PR. |
| Reanudación tras PR | PR cerrado sin merge, o merge con commits posteriores pendientes | Verifica remoto; conserva trabajo pendiente, no limpia por estar cerrado. |
| Cierre tras merge | Merge remoto confirmado, recursos propios completos | Actualiza main de forma segura; conserva configuración/evidencia, cierra sólo lo propio y no ejecuta merge. |
| Brevedad | “Sé breve” sin petición de caveman | Respuesta natural concisa; caveman no seleccionado. |
| Visual | Petición de informe frente a aceptación explícita de review hi-fi | Informe solo no inicia Lavish; aceptación permite el flujo con referencia de feedback. |
| Herramientas diagnósticas | Fallo Pi/Bitbucket/T3 frente a tarea no relacionada | diagnose consulta sólo sección pertinente; no trata hipótesis histórica como causa ya probada. |
| Chrome | Endpoint visible o sesión de otro agente | Carga obligatoria de aislamiento; no interactúa ni reinicia para resolverlo sin autorización. |

Evaluar también la disponibilidad real del nuevo coordinador y del fork Chrome. Un índice que enumera una skill no prueba que se seleccione. Conservar por caso resultado, evidencia, versión, límites y no-ejecutado cuando corresponda. No sumar estos casos a resultados históricos de Reflect.

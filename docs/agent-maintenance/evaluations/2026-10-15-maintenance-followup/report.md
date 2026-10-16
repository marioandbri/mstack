# AM-031: los tres recorridos pendientes terminan sin recuperación

Los tres casos pasaron su revisión conductual, checks e invariantes con contexto verificado y colección completa. No hubo recuperación manual de artefactos, reintentos ni intervenciones humanas dentro de los intentos. Esto cierra el criterio restante del ticket 14 junto al smoke integrado nativo y la evidencia anterior de comparación, promoción y reversión.

Mario autorizó "procede con eso entonces" después de identificar estos escenarios y una nueva ejecución acotada. El [protocolo](../../changes/AM-031-targeted-validation-protocol.md) fija tres turnos gpt-6.1-sol/high, 180 segundos por intento y 540 segundos reservados en total. Los [resultados](results.json) conservan hashes, referencias de revisión y métricas. El [publicador](publish.py) verifica los recibos contra el ledger y los bytes de los artefactos antes de generar esa salida.

## Resultados

| Caso | Resultado | Conducta comprobada | Tiempo registrado |
|---|---|---|---|
| Reanudar Reflect con drift | Aprobado | Recuperó original y resumen parcial; conservó conducta aceptada y rechazo previo. Reabrió sólo destino y guardó una pregunta activa en revisión 3. | 87,240 s |
| Reflect sólo chat | Aprobado | Conservó las decisiones pese a fuentes inaccesibles. Informó que no había pregunta pendiente registrada, sin inventarla. No guardó registros ni propuestas y explicó el límite de reanudación. | 28,665 s |
| Captura sin promoción | Aprobado | Guardó los bytes exactos del incidente, corrección factual y clasificación provisionales. Conservó una ocurrencia, no abrió Reflect ni modificó instrucciones y respondió 4 a la tarea original. | 45,351 s |

La revisión manual del implementador está ligada a líneas y hashes. Se revisaron todas las acciones y respuestas finales, además de los checks mecánicos. Una lectura nativa sobre copias privadas de las bases confirmó la revisión 3, sus decisiones y el original exacto de captura. Los artefactos recogidos permanecieron intactos. No se identificaron acciones innecesarias en esta pasada; las consultas de rutas ausentes sirvieron para comprobar disponibilidad y conservar sus límites.

Reflect se invocó explícitamente en sus dos casos. Sus resultados demuestran el uso solicitado y el cumplimiento observado, sin establecer selección automática. Captura leyó su skill y los contratos compartidos, sin leer el entrypoint de Reflect. Los fixtures y la variante del incidente no se convierten en episodios independientes.

## Fuentes, presupuesto y preservación

La fuente es df5976e0c38c8d65b89e161b86073e1a277f31f1, que incluye las correcciones 03cc76f. La preparación verificó que solicitudes, fixtures, setup, checks y rúbricas fueran iguales a los tres casos anteriores. Cambiaron las referencias de fuentes, el código corregido y la imagen, ahora sha256:b0c6aeaafd52a30ceef9d30913df39be6887d8b3ef444bf53ae16fa0d39b91c7. Codex App Server 0.160.0, Python 3.13.2, Bun 1.3.14 y uv 0.10.11 quedaron congelados con las demás versiones observadas.

Los tres preflights confirmaron catálogo e instrucciones cargadas sin enviar turn/start. Durante la preparación se corrigieron permisos de los directorios propios del control, antes de iniciar intentos; no se repararon artefactos de agentes. El ledger reservó tres intentos, tres turnos y 540 segundos. Las trazas contienen tres turn/start y tres finales completed. El tiempo acumulado registrado fue 161,256 segundos, antes de checks y colección; no es el tiempo total de preparación y revisión.

Cada caso conserva el uso acumulado de tokens informado por el harness. Caché y razonamiento son subconjuntos de entrada y salida. No conocemos llamadas internas al proveedor ni coste monetario. No hubo juez generativo adicional, uso de Laya ni reintentos automáticos.

Los 14 recibos de AM-030 conservan sus hashes, contrastados también con sus resultados publicados. Aquella campaña sigue teniendo 11 casos aprobados y tres inconclusos. Esta validación añade tres intentos posteriores satisfactorios; no transforma los anteriores en éxitos ni repite los 14 sobre una sola versión. La comparación original de captura sigue sin demostrar mejora, porque el baseline no reprodujo el incidente y las condiciones de esta pasada cambiaron.

## Verificación y entrega

Los checks actuales pasaron con Bun 1.3.14: bun run check, bun test con 43 pass, un skip opcional de Portless y cero fallos, fish install/verify.fish y git diff --check. La suite incluye el smoke integrado por procesos, CLI e instalador real en destinos temporales, con cero modelos, y las suites Python de registros e instalación. El smoke opcional de Gemma no se repitió.

No quedan contenedores de evaluación activos. La aserción de suspensión fue temporal y terminó con el proceso de campaña. La instalación real conserva 25e722daafadb2b39ea597adbc19b41632e48b4a. Los registros, protocolos y trazas privados permanecen bajo maintenance-laya/implementation-14/campaign-03, sin credenciales en los artefactos publicados. Los recursos de recuperación de autenticación de AM-030 se preservan.

Los 14 tickets tienen cierre con evidencia. Queda la revisión de Mario antes de preparar la PR y su merge remoto. El candidato no se activó en el entorno real. Una pasada dirigida no establece fiabilidad estadística, cobertura de otros harnesses ni la causa exacta de los cierres intermitentes anteriores.

Para volver a publicar esta evidencia sin ejecutar agentes:

```fish
env PYTHONDONTWRITEBYTECODE=1 uv run --project skills/reflect/runtime --locked --extra evaluation python docs/agent-maintenance/evaluations/2026-10-15-maintenance-followup/publish.py --campaign /ruta/privada/implementation-14/campaign-03
```

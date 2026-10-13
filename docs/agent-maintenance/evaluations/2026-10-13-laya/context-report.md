# Seguimiento: preset Model routing y contexto

Fecha: 2026-10-13. Mario preguntó si se había probado Model routing y señaló la importancia del contexto. El ensayo inicial no había usado ese preset ni comparado entradas con contexto adicional. Este seguimiento agrega 13 solicitudes locales a las 48 anteriores, sin modificar el servicio ni integrar resultados en Reflect.

## Qué hace el preset

Se seleccionó Model routing preset en el playground y se pulsó Run con su ejemplo original de refactorizar un servicio y añadir pruebas al módulo de pagos. La [definición y respuesta](routing-preset.json) conserva el resultado en vivo.

El preset rellena un estado de ejemplo y preguntas sobre dominio, dificultad, herramientas y sensibilidad. No añade contexto del proyecto ni cambia los pesos. Su campo Checkpoint queda en auto-route; el servidor eligió `english` por el idioma del ejemplo. Preset y selección de checkpoint son controles distintos.

La respuesta dio `domain=code` con probabilidad 0,9778 y dificultad esperada 2,0414 en una escala de 0 a 3. También devolvió P(needs_tools)=0,0886. Refactorizar un servicio real normalmente necesita acceso al código, por lo que ese resultado merece revisión. El ejemplo no distingue entre explicar cómo refactorizar y efectuar la edición: no fijamos una etiqueta retrospectiva ni calculamos exactitud de este preset con una sola solicitud.

Este preset podría servir de punto de partida para caracterizar solicitudes de trabajo. No reemplaza directamente las preguntas sobre fallos, preferencias o tipos de instrucciones. Si se adapta, necesita una evaluación propia para el propósito final.

## Comparación de contexto

Se escogieron seis casos ya usados en desarrollo: O01, O06, O08, A01, A06 y A08. Se prepararon doce solicitudes antes de consultar el modelo, conservadas en [protocolo](context-protocol.json). Dentro de cada par sólo cambia la presencia de un párrafo de contexto sobre el repositorio y su proceso de revisión. El target, las preguntas, las opciones, el idioma y el checkpoint son iguales.

Ambas condiciones usan un estado estructurado con `target`. Las preguntas indican que deben clasificar únicamente ese campo. La condición con contexto añade un resumen del dominio, sin la etiqueta esperada ni una explicación de la respuesta particular. Se alterna el orden de las condiciones entre casos. No se ajustaron preguntas entre solicitudes.

| Formulación | Sin contexto adicional | Con contexto adicional |
|---|---:|---:|
| v1 | 3/6 | 3/6 |
| v2 | 3/6 | 3/6 |

Las [respuestas completas](context-results.json) muestran cambios de etiqueta sin mejora de coincidencias exactas. O06 pasa de preferencia a fallo, pero el texto contiene ambos y su etiqueta esperada es mezcla. A08 se reconoce como restricción en ambas condiciones, a diferencia del ensayo inicial. Ese cambio coincide con la nueva presentación de target y la instrucción de clasificar sólo ese campo; no puede atribuirse al contexto añadido, que no explica la diferencia entre ambas condiciones nuevas.

Las doce solicitudes respondieron correctamente a nivel HTTP y no informaron truncamiento. Este es un experimento adaptativo sobre casos seleccionados después de ver resultados, con español e inglés y sin ejemplos nuevos. No es una prueba de generalización ni una medición confirmatoria del valor del contexto. El contexto añadido es un resumen genérico del dominio; no probamos recuperación de evidencia específica de cada incidente, ejemplos demostrativos ni traducción de las preguntas.

## Interpretación

La formulación y la entrada importan. Mis resultados anteriores caracterizan las preguntas probadas, no toda la capacidad de Laya. La recomendación queda acotada a no adoptar esas configuraciones sin más evaluación; no descarta el componente.

Este seguimiento tampoco permite afirmar que cualquier contexto mejore la clasificación. Una evaluación posterior debe separar datos indispensables para entender el incidente, definiciones de categorías, ejemplos de desarrollo y texto irrelevante. Debe evitar incluir la respuesta esperada en la entrada y verificar el presupuesto de tokens. Para contenido mixto, conviene comparar preguntas por atributo frente a una única categoría excluyente.

La comparación del flujo con y sin Laya sigue pendiente. Se conserva la propuesta del sistema completo y la prioridad de inventario/auditoría, sin hacer depender esas entregas de este experimento.

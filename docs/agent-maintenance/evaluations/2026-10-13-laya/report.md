# Exploración local de Laya

Fecha: 2026-10-13. Estado: exploración terminada, sin integración. Mario autorizó usar el playground y una comparación aislada. Se ejecutaron 48 solicitudes locales, sin reintentos ni llamadas a modelos alojados. Esta muestra no demuestra una mejora frente al clasificador actual de Reflect.

## Resultado

La clasificación amplia no es suficientemente fiable en esta muestra para dirigir la auditoría. Las preguntas binarias ofrecen una pista para preferencias y procedimientos, pero fallan en los positivos de fallos y restricciones. Recomiendo mantener el adaptador como experimento opcional y avanzar con la auditoría sin depender de Laya.

| Tarea | Desarrollo v1 | Desarrollo v2 | Comprobación v1 | Comprobación v2 |
|---|---:|---:|---:|---:|
| Tipo de observación | 4/6 | 3/6 | 8/12 | 7/12 |
| Tipo de fragmento de instrucciones | 2/6 | 3/6 | 6/12 | 4/12 |

Los numeradores son coincidencias exactas con etiquetas fijadas por el mismo agente antes de las predicciones. No son anotaciones independientes ni casos reales seleccionados al azar. Ambas formulaciones se fijaron antes de ejecutar; se informan ambas y no se elige una ganadora con el conjunto de comprobación.

## Diseño y límites

[Casos](cases.json) contiene 36 textos sintéticos: 18 observaciones y 18 fragmentos de instrucciones, repartidos entre español, inglés y Spanglish. Cada tarea tiene seis categorías, seis casos de desarrollo y doce de comprobación. Cada división incluye todos los idiomas y categorías, con sólo una o dos muestras por celda. Los ejemplos se inspiran en el dominio del proyecto; no constituyen nuevas ocurrencias de incidentes.

Las observaciones cubren fallo, riesgo, preferencia, hecho, propuesta y mezcla. Los fragmentos cubren procedimiento, restricción, hecho, estado temporal, preferencia y mezcla. Estas taxonomías son preguntas experimentales, no un cambio al esquema de observaciones. La etiqueta esperada describe la aportación principal; una frase que aporta evidencia de un fallo no se etiqueta automáticamente como mezcla por contener también hechos. Esta distinción requiere mejorar la rúbrica antes de una comparación confirmatoria.

[Preguntas](questions.json) contiene dos preguntas `choice` por solicitud. Las descripciones están en inglés en ambos modelos; no se comparó su traducción. Se fijó `english` para inglés y `multilingual` para español y Spanglish, con `lang=en` o `lang=es`. El hint de Spanglish es una decisión del ensayo, no una detección de idioma. Se respetó el orden declarado de opciones; su sensibilidad no se midió. Ninguna respuesta informó truncamiento.

[Freeze](freeze.json) conserva los hashes previos al primer resultado. [Manifest](manifest.json) conserva entorno, fuentes y límites de identidad. El proceso no expone el digest de los pesos cargados: el ref de caché es información del disco, no una garantía de qué pesos estaban en memoria.

## Errores que importan

- O06 combina una pérdida del registro de decisiones con una preferencia. Laya responde sólo `preference`, con probabilidad 0,9877 en v1 y 0,977 en v2.
- O12 combina un fallo del exportador con una propuesta. v2 responde sólo `proposal`, con probabilidad 0,9128.
- A12 combina preferencia y estado temporal. v1 responde sólo `temporary`, con probabilidad 0,9155.
- Las restricciones A02, A08 y A14 no se reconocen como `constraint` en ninguna formulación.

Una probabilidad alta no elimina estos errores. A modo descriptivo, aplicar un corte de 0,9 a los 24 casos de comprobación conservaría 7 respuestas de v1, 6 correctas, y 4 de v2, 3 correctas. Quedarían fuera 17 y 20 casos respectivamente. El corte se inspeccionó después de observar los resultados; no está calibrado ni se propone como política de aceptación.

## Seguimiento binario

Después del ensayo `choice`, se formularon preguntas `noul` sobre los doce casos de desarrollo. [Protocolo y etiquetas](binary-development.json) se guardó antes de este seguimiento; [respuestas](binary-results.json) conserva todas las salidas. No se volvió a usar el conjunto de comprobación para ajustar estas preguntas.

| Pregunta | Coincidencias a corte 0,5 | Positivos reconocidos |
|---|---:|---:|
| Reporta un fallo ocurrido | 4/6 | 0/2 |
| Expresa una preferencia | 6/6 | 2/2 |
| Describe pasos operativos | 5/6 | 2/2 |
| Impone una prohibición o condición | 3/6 | 0/2 |

El corte 0,5 sirve únicamente para describir esta prueba, no para autorizar acciones. El 4/6 en fallos procede exclusivamente de los cuatro negativos; no demuestra detección útil. Preferencias y procedimientos requieren ejemplos nuevos y negativos difíciles antes de recomendar su uso.

## Rendimiento y contrato observado

En las 36 solicitudes `choice`, la latencia reportada por el servidor tuvo mínimo de 37,6 ms, mediana de 77,85 ms y máximo de 7.142 ms. La primera solicitud fue el máximo; conservamos posibles efectos de calentamiento y cambios de forma. No atribuimos una causa concreta sin medirla. Dos preguntas comparten cada solicitud. No es una medición del flujo completo ni demuestra ahorro frente a un LLM.

El health endpoint informó Laya 0.4.6, Torch 2.14.1 y MPS, con los tres modelos listos. La primera solicitud se ejecutó con Run en el playground; las otras usaron su mismo endpoint desde la pestaña, en serie. El servicio existente se conservó sin cambios.

Las respuestas `choice` incluyen `probabilities`, `answer_confidence` y `confidence` distintos. En estas respuestas `noul`, `confidence` coincide con `answer_confidence`, no debe suponerse la fórmula descrita para otra versión. Todos los resultados observados tienen `action.act_probability=1`, incluso los errores. Ninguno de esos campos acredita autorización o corrección.

## Reproducción y siguiente comparación

Para repetir el ensayo, cargar cada `state` de cases.json y las preguntas de su `task` en el editor JSON del playground. Fijar modelo e idioma según el caso y ejecutar una vez. Alternativamente, enviar el mismo objeto `{state, questions, model, lang}` a `POST /api/predict`. El seguimiento binario usa sus propios casos y preguntas. Conservar resultados nuevos por separado y verificar identidad del modelo antes de pretender una reproducción exacta.

La comparación del sistema necesita la misma entrada revisada y dos flujos: agente con su procedimiento actual; agente con ese procedimiento y una anotación opcional de Laya. Medir calidad final, omisiones, correcciones humanas, tiempo total y uso del modelo mayor. La precisión aislada del clasificador no sustituye esa comparación. Su diseño está en [AM-014](../../changes/AM-014-maintenance-discovery.md). Aún no se ejecutó una baseline independiente ni se fijó presupuesto de modelos alojados.

# Revisión editorial aplicada al candidato

Fecha: 2026-10-13. Mario aprobó la recomendación con “perfecto, me gusta tu recomendacion. vamos con eso”. La edición y revisión semántica se aplican al candidato, con promotion=none.

[AGENTS completo vigente](AM-011-global-agents.proposed.md), [diff frente a AM-010](AM-011-global-agents.patch), [diff frente al global original](AM-011-from-original.patch) y [registro de decisiones](AM-011-writing-analysis.review.json).

El texto pasa de 608 a 476 palabras, contadas por espacios e incluyendo encabezados. La reducción es 21.7%. No se fijó una cuota de palabras ni se interpreta la reducción como mejora de rendimiento.

## Correspondencia semántica

| Condiciones revisadas de AM-010 | Resultado en AM-011 |
|---|---|
| Idioma, concisión natural, documentación según propósito | Conservadas en Communication. Se acorta sintaxis sin activar caveman ni eliminar detalle necesario. |
| Consulta ante dudas | Se investiga evidencia primero y se consultan requisitos/preferencias materiales pendientes. Scope and delivery conserva la consulta por cambios de alcance o comportamiento. |
| Workflow silencioso, excepción para explicar restricciones, aceptación del apoyo visual | Conservados. |
| Prioridades técnicas y poco peso de coste/tiempo | Conservadas en una frase; ninguna cualidad priorizada se elimina. |
| Archivos generados y CHANGELOG, regeneración autorizada | Conservados con actor y condición explícitos. |
| Verificación, resultados reales, límites y cobertura insuficiente | Conservados. |
| Regresiones propias, fallos independientes y reparación previamente autorizada | Se conserva el límite. El principio único de preservar aprobaciones cubre reparaciones ya autorizadas. |
| Dependencias maduras/mantenidas, beneficio material, standard library, seis criterios y pin | Conservados. bunx skills queda explícitamente exento sólo del pin; los locks conservan su regla independiente. |
| Alcance aprobado, cambios de comportamiento, ediciones pequeñas explícitas | Conservados en un único principio de autorización. |
| Worktree propio y configurado, commits sin coautoría | Conservados. |
| Evidencia y confirmación de implementación antes del PR; rama indicada o main | Conservados. La confirmación se refiere a la implementación, no sólo a recibir evidencia. |
| Merge remoto por Mario, verificación, actualización de main y cierre | Conservados en ese orden, con protección de trabajo, configuración y evidencia. |
| Recursos ajenos y consumidores activos | Conservados. Sólo se cierra lo propio con trabajo completo y sin consumidores activos. |
| Revisión de almacenamiento, lista de paths/tamaños/motivos, excepción de cierre autorizado | Conservados; la excepción sigue explícita para evitar que el permiso general de borrado la anule. |
| Fish, bunx, bun/pnpm, ajustes temporales y autorización de persistencia global | Conservados. La autorización existente se mantiene por el principio común, sin repetirla por archivo. |
| Ideas fuera de alcance, observaciones pendientes, curación y ausencia de duplicación | Conservados. La revisión y aprobación de Mario preceden integración o descarte, conforme a la decisión anterior. |
| Procedimientos y activación en skills, sin selectores globales | Conservados. El procedimiento de diagnóstico de selección permanece en Reflect/instruction-review y skill-support, ya existentes. |

La comprobación semántica es lectura comparada de condiciones, no una prueba conductual ejecutada con modelos. No se modificaron skills ni sus políticas de invocación durante esta edición.

## Versiones

AM-010 permanece como baseline histórica de 608 palabras en el commit 32aae5561fe0482538decbaada5d0dd1f37a1061. Esta versión AM-011 sustituye su global propuesto. La clasificación de destinos y las skills de AM-010 siguen vigentes.

El [manifest AM-011](AM-011-candidate-files.json) actualiza los hashes de las fuentes candidatas. El registro mantiene el análisis y sus fuentes originales, la respuesta de Mario y el candidato nuevo. El global instalado conserva SHA-256 9b9406a1036570535f7b5f391ae754bbcbc5c8ba8e5da04a66b873a45504ffe2.

## Verificación

Los resultados de esta versión se guardan en [AM-011 verification](AM-011-verification.md). Las comprobaciones históricas de AM-010 no se presentan como evaluación conductual de este texto. Selección y comportamiento siguen pendientes antes de activar los traslados.

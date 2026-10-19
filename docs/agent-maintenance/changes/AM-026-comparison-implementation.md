# AM-026: comparación de intervenciones

El ticket 11 vincula una oportunidad de revisión con baseline, alternativas pertinentes y opción de ningún cambio. Congela casos, rúbrica, fuentes, código del evaluador, entorno y repeticiones. Rechaza un cambio de tarea, modelo/razonamiento o fuente fuera de los targets declarados. Preparar y registrar resultados no ejecuta modelos ni instala nada.

Tres pruebas públicas ejercitan una baseline mecánica fallida y candidato válido, registro de métricas enlazado a Reflect, preparación sin resultados, baseline que no reproduce y rechazo de condiciones no comparables. El resultado conserva tarea, intervención humana y acciones innecesarias por separado de tiempo y tokens desconocidos. Los intentos sin juicio quedan visibles; un juicio duplicado no cuenta como otro ensayo. La revisión conserva promoción none y sus respuestas.

La integración detectó además clasificación obsoleta tras una decisión posterior. Dos regresiones verifican que se mantiene la anotación histórica pero pasa a pendiente, y que un filtro de categoría no usa una anotación cuyos registros relacionados cambiaron. No se reabren ni se borran decisiones del usuario.

Los checks obligatorios pasaron: bun run check para 30 skills y 68 Markdown; bun test con 43 pass, 1 skip opcional, 0 fail y 376 aserciones, incluyendo 52 pruebas Python y el smoke Gemma optativo ya verificado. fish install/verify.fish confirmó el snapshot estable y git diff --check pasó.

Standards: sin incumplimientos pendientes. Se preservan originales, versiones, autorizaciones y separación entre propuesta, evaluación e instalación. Los esquemas públicos anteriores no se alteran.

Spec: adaptador y comparación mecánica están implementados, incluida la salida de conservar lo actual y la invalidación de evidencia o autorizaciones vulneradas. La [campaña posterior autorizada AM-030](../evaluations/2026-10-15-maintenance-cycle/report.md) ejecutó baseline y candidata bajo condiciones comparables. El baseline pasó y no reprodujo; la candidata conserva infraestructura inconclusa por exportación. Reflect guarda el resultado y none, sin mejora establecida ni promoción. El ticket 11 queda cerrado por la capacidad de comparación, sin afirmar superioridad del candidato.

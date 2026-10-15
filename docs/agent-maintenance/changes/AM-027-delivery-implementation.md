# AM-027: promoción y reversión verificables

El ticket 12 añade un adaptador que conserva aceptación de conducta y destino, candidato completo, diff y commit. Usa el instalador existente, con dry-run por defecto y destinos aislados. La preferencia explícita se admite sin comparación estadística; una mitigación evaluada debe corresponder al commit aceptado. Los hashes del instalador y la identidad del HOME quedan ligados al plan.

Seis pruebas públicas usan Git y HOME temporales reales. Comprueban dry-run sin cambios, promoción desde commit, comportamiento de un fixture leyendo el global realmente instalado, reversión y comportamiento restaurado. Conservan configuración no gestionada posterior y secretos sintéticos fuera de los informes. También rechazan un candidato distinto, falta de autorización y drift antes de promover o revertir. Una continuación de la revisión conserva aceptación aplicable. Una comprobación incompleta queda inconclusa, sin inventar fallo conductual ni permiso de reversión.

El instalador incorpora expected-generation para setup y rollback. Una prueba nativa falla antes de implementarlo y pasa después: el plan antiguo no puede sobrescribir una generación posterior ni revertirla. La condición se verifica bajo su lock existente. No se duplica su transacción ni se retiran controles de propiedad externa.

La integración también prueba que metadata de entorno no seleccionada, como api_key, se rechaza antes de crear persistencia. Los protocolos conservan únicamente campos declarados. Se retiraron enlaces desde recursos instalables hacia documentos que sólo están disponibles en el repositorio canónico.

Los checks obligatorios pasaron: bun run check para 30 skills y 69 Markdown; bun test con 43 pass, 1 skip opcional, 0 fail y 376 aserciones. Incluye 59 pruebas Python del runtime y el smoke Gemma optativo ya realizado, además de la suite completa del instalador con su nueva regresión. fish install/verify.fish confirmó el snapshot estable y git diff --check pasó.

Standards: sin incumplimientos pendientes. Los grants de fixture no autorizan instalación activa; el modo active requiere el ensayo aislado con agente del mismo commit. Los recibos de entrega se muestran aparte del registro público promotion none. El estado observado tras un acuse perdido conserva autor desconocido.

Spec: instalación, recibos, drift, rollback y conducta mecánica están verificados. Las comprobaciones con agente tras promoción y rollback siguen abiertas para el protocolo presupuestado del ciclo. No se activó el candidato en el HOME real ni se iniciaron turnos generativos.

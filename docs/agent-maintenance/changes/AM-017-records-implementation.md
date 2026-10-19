# AM-017: captura transaccional

El ticket 02 añade el [adaptador local de registros](../../../skills/reflect/runtime/README.md). SQLite conserva los bytes del original y la procedencia por separado, con identidad de operación, ámbito y proyecto explícitos. No carga sqlite-vec ni modelos durante captura.

## Aceptación comprobada

Siete pruebas Python, incluidas en bun test, cubren el CLI y la API pública:

- Captura y reapertura conservan exactamente el original, separan sesión de origen y captura y mantienen los campos desconocidos como null. Reintentar con la procedencia recuperada también funciona.
- Dos procesos sincronizados inicializan una base nueva y guardan ambos registros. Otras tandas conservan observaciones distintas y una sola captura para el mismo operation.
- Una identidad reutilizada con otro contenido devuelve conflicto sin reemplazar el original.
- Una actualización con revisión obsoleta no reemplaza el estado confirmado. La decisión conserva su evidencia e historial y no modifica el JSON original.
- Matar al escritor antes del commit revierte el lote. Matarlo después conserva el registro y permite confirmar el resultado reintentando su operación.
- El CLI vuelve a la tarea con clasificación, reconstrucción e indexación pendientes. No abre Reflect ni ejecuta evaluaciones. La base tiene permisos 0600.
- Una procedencia inválida se rechaza; no se sustituye silenciosamente por datos desconocidos. Otro proyecto no puede abrir la misma base mediante el adaptador.

La primera prueba de API falló antes de existir el adaptador. Las de transición, CLI, procedencia inválida y reintento desde metadata recuperada fallaron antes de sus implementaciones o correcciones y pasaron después. La regresión de recuperación usa procesos reales y mata al escritor en los límites de la operación pública, sin mocks de SQLite.

## Verificación y límites

Con Bun 1.3.14, bun run check pasó para 30 skills y 60 Markdown. bun test terminó con 32 pass, 1 skip opcional de Portless, 0 fail y 319 aserciones. Dentro de esa suite, las siete pruebas Python pasaron con Python 3.13.2. fish install/verify.fish confirmó el snapshot activo y sus 126 destinos. git diff --check pasó.

Standards: sin incumplimientos pendientes. Dependencias directas y resolución fijadas, archivos de datos y entorno ignorados, sin servicios ni modificaciones del snapshot instalado.

Spec: los seis criterios de 02 están cubiertos por operaciones públicas, procesos simultáneos y el smoke del CLI. La clasificación versionada, el resumen, la búsqueda y la migración conservan sus entregas. Los registros históricos no se migran ni se eliminan. La autorización de implementación no equivale a instalación activa.

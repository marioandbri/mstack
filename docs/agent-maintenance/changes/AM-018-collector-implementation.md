# AM-018: recogida legible de evaluaciones

El ticket 03 sustituye la recogida frágil por el [recolector de workspaces propios](../../../skills/reflect/runtime/collection.md). Se conserva el runner histórico sin modificarlo. El helper nuevo es reutilizable, no ejecuta modelos y puede funcionar sin la base de observaciones.

## Reproducción y causa acotada

Se extrajo sólo la función hashes del runner de soporte del 8 de octubre, sin importar ni ejecutar el runner. Su archivo tiene SHA-256 60e91dbcd93a1f6f3d15fda131e74aca47318fd0185998c0d0c917a9e5ce1920. Sobre una copia sintética en `.agents/skills/example/SKILL.md` con modo 0200, la función original produjo PermissionError y el copytree original produjo un error de lectura. Cero llamadas al modelo.

El control de metadata mantuvo un descriptor abierto antes de fijar 0200 y aplicó copystat, como hace copy2. El destino heredó 0200 y su lectura exterior falló. Este control verifica la preservación de permisos; no reproduce la capacidad Linux DAC_OVERRIDE. En el código histórico, los hashes posteriores y copytree precedían a guardar el resultado y quedaban fuera del guard de ejecución. Una excepción abortaba esa publicación.

La causa acotada es la suposición de que todas las copias podían leerse y de que conservar sus modos era apropiado para la exportación. No queda establecido quién creó el modo inicial ni se atribuye al trigger o al harness.

## Corrección y aceptación

El recolector guarda primero un recibo in-progress y verifica la identidad del workspace. Sólo después de terminar sus consumidores puede añadir temporalmente lectura del propietario a artefactos propios, copiar bytes, contrastar el hash reabriendo el destino y restaurar el modo del origen. Los destinos son nuevos y privados. No modifica recursos ajenos ni snapshots externos. Tampoco sigue enlaces o lee credenciales.

Siete pruebas ejercitan las operaciones públicas, incluido el CLI. La copia anidada 0200 queda legible en el destino, conserva bytes y hash y mantiene el modo original en origen. Las otras pruebas cubren trazas truncadas, resultado ausente, timeout, estado de ejecución interrumpida, límites no finitos, exclusión de enlaces y archivos privados, y recuperación con el recibo anterior intacto. La regresión del CLI y las de límites e inodos compartidos fallaron antes de sus correcciones y pasaron después.

La recuperación usa otro destino y queda vinculada al intento original, con stage recovered. La recogida mantiene behavioral_status ungraded; ni un hash ni un recibo prueban carga de contexto o conducta correcta.

## Verificación y límites

bun run check pasó para 30 skills y 61 Markdown. bun test terminó con 32 pass, 1 skip opcional, 0 fail y 319 aserciones. La suite incorpora catorce pruebas Python de captura y recogida. fish install/verify.fish confirmó el snapshot activo 25e722daafadb2b39ea597adbc19b41632e48b4a, 30 skills y 126 destinos. git diff --check pasó.

Standards: sin incumplimientos pendientes. La corrección actúa sobre recursos de la tarea, conserva evidencia y no añade dependencias al recolector.

Spec: el defecto de lectura y exportación queda reproducido y cubierto por la regresión determinista. Los estados conservan infraestructura, ejecución y recuperación separados. No se repitieron llamadas a modelos ni se evaluó fiabilidad entre harnesses. El runner de 09 conserva su implementación pendiente, al igual que la comprobación del contexto cargado. No queda establecida la causa de creación de permisos.

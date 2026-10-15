# Promoción y reversión

El CLI delivery requiere runner-root, installer-repository, source-repository, home y control explícitos. target-mode usa isolated por defecto. El directorio control conserva identidad del HOME por dispositivo, inode y propietario; no se admite el HOME real como fixture aislado. Las lecturas y escrituras de la base siguen ligadas al proyecto.

prepare exige id, review-id, behavior-id, destination-id y commit. Ambas decisiones deben estar resueltas y tener el dominio correspondiente. El candidato completo y su diff deben coincidir con el commit frente a la versión instalada. Se conserva la versión estable previa; el primer bootstrap sigue siendo responsabilidad del instalador. La preparación ejecuta el dry-run existente y no aplica archivos.

Todos los cambios de fuentes gestionadas, incluidos manifests y defaults, deben estar declarados en los artefactos revisados. Un cambio adicional dentro del commit se rechaza. Un artefacto con content vacío puede representar un archivo vacío o una eliminación; el árbol Git y el diff completo distinguen ambos. Un destino ajeno a las fuentes gestionadas no se presenta como instalado.

Una preferencia explícita o un hecho confirmado no exige comparación estadística. Para una mitigación de fallo, la evidencia debe corresponder a la misma oportunidad de conducta y al mismo commit candidato. Un resultado favorable de otra oportunidad no satisface esa condición. Se guardan fuentes pertinentes, respuestas, artefactos, recibo previo y hashes del código del instalador. Una continuación sin cambios de esas decisiones conserva su aceptación; una respuesta o fuente material cambiada impide promover el plan antiguo.

promote y rollback requieren grant con kind user o fixture, source, answer, home, commit y actions promote/rollback. El grant de fixture sólo vale para un destino aislado. El modo active necesita aceptación real y un ensayo aislado del mismo commit con comprobación de agente tras promover y revertir. Las transferencias de propiedad externa siguen los controles del instalador; el adaptador no elimina locks ni adopta paquetes ajenos.

El instalador conserva snapshots, respaldos, recibos y configuración no gestionada. El nuevo expected-generation vincula setup y rollback a la instalación prevista y se comprueba bajo el lock nativo. Drift o una generación posterior detienen la operación. No se reimplementa su transacción. Si se pierde el acuse, inspeccionar get, el journal y el recibo; reconcile puede registrar el estado verificado con autor desconocido, sin inventar quién lo aplicó ni volver a instalarlo.

## Comprobar conducta

Promover devuelve promoted-check-pending; revertir devuelve restored-check-pending. Ninguno significa conducta verificada. profile lee los cuerpos y el global realmente instalados, los contrasta con el snapshot y liga generación, commit, bundle y destino al protocolo del runner. kind agent exige modelo y razonamiento; kind fixture identifica una comprobación mecánica.

Preparar y autorizar el caso pertinente antes de ejecutarlo. check recibe attempt, stage post-promotion/post-rollback y assessment-id para agentes. Comprueba el recibo actual y el vínculo a los bytes instalados. Un fixture puede quedar fixture-verified, nunca verificado como agente. Falta de traza o juicio permanece pendiente o inconclusa; no se convierte en fallo de conducta. Un fallo confirmado recomienda reversión o investigación y respeta el grant existente. No concede permiso adicional ni ejecuta modelos automáticamente.

Review get conserva estos eventos por separado del registro público promotion none. Las propuestas, comparaciones y recibos de instalación mantienen sus significados distintos. El recorrido usa directorios temporales primero; la instalación activa conserva su autorización propia.

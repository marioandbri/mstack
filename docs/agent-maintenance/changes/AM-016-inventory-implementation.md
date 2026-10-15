# AM-016: inventario auditable

El ticket 01 de AM-015 añade el comando de [inventario solicitado](../inventory.md). Conserva las fuentes canónicas, las copias instaladas y el catálogo suministrado como evidencias distintas. Se puede usar sin observaciones ni base de registros.

## Aceptación comprobada

Tres pruebas por el CLI público cubren instalación distinta y catálogo parcial; fuentes inaccesibles, configuración desconocida y claves privadas; referencias rotas en instrucciones. La prueba de escape por symlink falló antes de limitar la lectura predeterminada al repositorio. La de referencias de instrucciones falló antes de reutilizar el comprobador de enlaces. Ambas pasaron después, con las mismas expectativas.

El smoke del CLI sobre este worktree inventarió 30 skills accesibles. El validador pasó y el verificador existente confirmó la instalación activa 25e722daafadb2b39ea597adbc19b41632e48b4a, con 30 skills y 126 destinos. Los cuatro hallazgos estructurales de esa muestra se conservan en la evidencia privada de la tarea; no se aplicaron cambios a las fuentes auditadas ni a la instalación. La revisión semántica figura como no realizada y la ejecución de workflows como desconocida.

La metadata externa sólo se acepta como entrada explícita. La prueba incluye campos ajenos y comprueba que no salen en el informe. No se inspeccionan cuerpos externos ni conversaciones. Los límites acompañan el resultado y un informe nuevo exige un destino de salida nuevo.

## Verificación

Con Bun 1.3.14, bun run check pasó para 30 skills y 59 Markdown. bun test terminó con 31 pass, 1 skip opcional de Portless, 0 fail y 317 aserciones. La suite conserva las pruebas reales del instalador y las tres nuevas pruebas del CLI. fish install/verify.fish confirmó el contenido y la configuración instalados. git diff --check pasó.

Revisión de Standards: sin incumplimientos pendientes de las reglas aplicables. El comando reutiliza el validador y el verificador, no añade dependencias y mantiene las lecturas y la salida dentro de su alcance explícito.

Revisión de Spec: los cinco criterios de 01 quedan cubiertos por el recorrido del CLI, sus fixtures y el smoke. Esto no acredita auditoría semántica, fiabilidad de selección ni las entregas de persistencia. Esas capacidades conservan sus tickets.

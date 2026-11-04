# Casos de decisión

## Tabla con barra de acciones

Un hook de funcionalidad administra la selección desde el padre común; la tabla y la barra reciben valores y acciones. El hook puede usar `useState` si los cambios son simples. Varios consumidores visuales no implican un store global o una máquina. Una expansión puramente visual y autocontenida puede permanecer inline en la fila.

## Filtros con Aplicar

nuqs posee los filtros confirmados; un hook local gestiona el borrador. Un objeto en `useState` basta para un borrador sencillo; prefiere reducer cuando centralizar eventos e invariantes facilite mantener sus reglas, no por el número de campos. Deriva `hasChanges` y `canApply` sin almacenarlos. La acción Aplicar del hook valida y publica filtros y reinicio de página juntos; esos criterios forman la query key de TanStack Query. Define qué ocurre con el borrador al usar Atrás. Si la búsqueda consulta mientras se escribe, el debounce de la URL por sí solo no aplaza la consulta cliente.

## Editor al cambiar de entidad

`useEntityEditor(entityId)` encapsula el borrador aunque tenga un único consumidor. Cambiar `entityId` requiere una política de reinicio o conservación por entidad; un refetch de la misma entidad no debe borrar la edición. Verifica que una respuesta tardía de A no sobrescriba el borrador de B. Mantén presentación y conexión de eventos en el componente.

## Una carga observada desde dos lugares

Una subida simple usa una mutación con dueño compartido. Panel e indicador observan la misma operación y derivan sus indicadores. Si aparecen confirmaciones, interrupciones y recuperación condicionada, evalúa si XState aclara su ciclo de vida. El loading y el error de la subida siguen perteneciendo a Query. Verifica que ambos consumidores no inicien la misma escritura y distingue los reintentos configurados de los disparadores duplicados.

## Panel de agente con streaming

Conserva mensajes y tool calls en su dueño existente, como el SDK de streaming. Para estado de cliente compartido que cambie con frecuencia, usa el store adoptado si distintos consumidores necesitan observar distintas porciones. Expón hooks selectivos: una actualización del texto en curso no debería notificar por esa suscripción a quien solo observa la selección local. Mantén el alcance por conversación cuando corresponda y verifica aislamiento y reinicio al cambiar de conversación. No dupliques el stream para obtener selectividad.

## Checkout con paso direccionable

XState puede aportar cuando existen pasos con prerrequisitos y ramas de recuperación. Query administra las operaciones remotas y nuqs representa el paso solicitado. Una acción interna rechazada conserva el destino aceptado. Para un enlace directo o el historial hacia un paso no permitido, define la vista y URL resultantes, sin ciclos ni escrituras provocadas por corregir la URL. La URL nunca demuestra que se pagó.

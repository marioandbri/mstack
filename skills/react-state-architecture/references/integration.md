# Límites de integración

Consulta solo el apartado que afecte al cambio. Usa las APIs de las versiones instaladas.

## TanStack Query

- Incluye en la query key todos los criterios que identifican los datos, también los leídos desde nuqs. Tras una mutación, actualiza o invalida las consultas afectadas.
- Dos llamadas a `useMutation` no representan automáticamente la misma ejecución. Para observar una operación desde varios componentes, comparte su dueño o usa los mecanismos de observación de mutaciones.
- Un borrador editable es distinto del dato remoto confirmado. Define si se descarta, conserva por identidad o requiere una decisión al cambiar de entidad; cambiar los argumentos del hook no lo reinicia automáticamente. Un refetch no debe sobrescribir silenciosamente la edición.
- Decide reintentos según la operación. Cancelar la UI o abortar el transporte no garantiza deshacer una escritura recibida por el servidor.

Consulta [estado remoto](https://tanstack.com/query/latest/docs/framework/react/overview) y [mutaciones](https://tanstack.com/query/latest/docs/framework/react/guides/mutations).

## nuqs y navegación

- Usa el adapter del router. Comparte parsers entre servidor y cliente cuando ambos lean la URL; define valores ausentes, inválidos y restricciones como páginas positivas.
- Agrupa parámetros relacionados con `useQueryStates`, conserva parámetros ajenos y distingue `replace` de `push` según qué cambios deba recorrer Atrás.
- Si los parámetros cambian datos cargados en el servidor, configura esa actualización explícitamente.
- El debounce de URL de nuqs no retrasa el valor que devuelve el hook. Para aplazar consultas cliente, aplica debounce al criterio que consume Query y usa ese mismo criterio en la query key y la consulta. Define si limpiar, confirmar o navegar debe aplicar el valor inmediatamente y descartar actualizaciones pendientes.
- Si hay borrador local, define qué ocurre al navegar con cambios pendientes. No sincronices borrador y URL incondicionalmente mediante efectos.
- Si el flujo valida destinos, distingue acciones internas de enlaces directos e historial. Para acciones internas, publica el destino en URL tras aceptar la transición. En navegación externa, la URL puede haber cambiado antes de validarse: define qué vista se muestra y si se conserva la URL con una explicación o se normaliza a un destino permitido. Evita ciclos, eventos duplicados y entradas de historial creadas por la propia corrección.

Consulta [adapters](https://nuqs.dev/docs/adapters), [opciones](https://nuqs.dev/docs/options) y [cambios agrupados](https://nuqs.dev/docs/batching).

## XState con Query

Conecta acciones y resultados mediante un único responsable. Los consumidores que observan la misma consulta no deben disparar todos la misma transición. Deriva indicadores como `isBusy` o `canContinue`; usarlos como condiciones no obliga a almacenarlos. La máquina conserva decisiones propias, como una confirmación previa que no se deduce del resultado actual de una consulta.

Comprueba qué debe pasar con respuestas tardías al cambiar de entidad o salir del flujo. Distingue descartar resultados de cancelar realmente el trabajo. Usa selectores para consumir el estado compartido cuando la integración lo permita.

Consulta [integración con React](https://stately.ai/docs/xstate-react) e [invocación de actores](https://stately.ai/docs/invoke).

## Contratos de error existentes

Un `Err` devuelto como dato resuelve normalmente una promesa. Si el contrato necesita activar el estado de error de Query o `onError` de XState, adapta el fallo explícitamente; no confíes en el nombre del tipo.

TypeScript puede comprobar uniones con narrowing y `never`; los datos externos siguen necesitando validación en runtime. Evalúa ts-pattern solo para matching difícil de mantener y neverthrow para composición de errores que lo justifique. Si ya existe Effect, adapta sus servicios sin duplicar reintentos entre capas. Adoptarlo para recursos, dependencias o concurrencia es una decisión de servicios fuera del flujo habitual de esta skill.

Consulta [TypeScript](https://www.typescriptlang.org/docs/handbook/2/narrowing.html), [ts-pattern](https://github.com/gvergnaud/ts-pattern), [neverthrow](https://github.com/supermacro/neverthrow) o [Effect](https://effect.website/docs/error-management/expected-errors/) según la herramienta utilizada.

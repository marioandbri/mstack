---
name: react-state-architecture
description: Chooses ownership and structure for React state, using TanStack Query for server state and nuqs for URL state. Use when implementing or refactoring stateful behavior, deciding local versus shared ownership, or evaluating reducer hooks and XState. Skip styling-only changes and unrelated performance work.
---

# Arquitectura de estado en React

Mantén un dueño por dato y conserva las soluciones existentes si cubren el cambio. Los defaults de TanStack Query, nuqs y XState orientan nuevas elecciones; no justifican migraciones por sí solos. Trabaja sobre la funcionalidad solicitada y respeta las convenciones del proyecto.

## Separar comportamiento y presentación

Encapsula por defecto el comportamiento con estado de una funcionalidad en un custom hook, aunque tenga un único consumidor. El componente conserva presentación, composición y conexión de eventos. Permite estado inline para interacciones visuales autocontenidas con actualizaciones directas.

Extraer un hook no exige un reducer. Usa `useState` para cambios simples y prefiere reducer cuando centralizar eventos e invariantes facilite mantener las reglas. Expón valores y acciones de dominio.

## Elegir el dueño y la estructura

- **Datos remotos:** usa TanStack Query por defecto para consultas y mutaciones. Consume sus datos y estados de operación sin replicarlos en reducers o máquinas.
- **UI local:** el estado pertenece a una instancia de componente o funcionalidad, aunque sus hijos reciban valores y acciones.
- **UI compartida:** varios consumidores necesitan la misma instancia. Mantén un propietario común en el alcance mínimo y expón un hook consumidor. Extraer o reutilizar un hook que crea estado no comparte sus instancias; contexto o el mecanismo existente pueden bastar.
- **Flujo complejo:** evalúa XState cuando explicitar transiciones y ciclo de vida aclare prerrequisitos, coordinación entre operaciones, interrupciones o recuperación. Compartir estado o gestionar la carga, cancelación y reintentos habituales de una petición no bastan. Explica qué dificultad concreta resuelve la máquina.
- **Valores derivados:** calcula indicadores desde el estado existente, aunque condicionen transiciones. Representa explícitamente solo decisiones del proceso que no puedan reconstruirse desde sus datos y operaciones.

El crecimiento previsto aumenta la preferencia por estructurar la lógica en un hook con reducer o, si aporta, una máquina. Basa esa previsión en requisitos conocidos o variantes ya presentes; evita diseñar para crecimiento hipotético.

## Evaluar la URL

Para cada dato de UI relevante, decide si compartir el enlace, recargar o navegar por historial aporta valor. El alcance local o compartido y la representación en URL son decisiones independientes.

- Usa nuqs para campos elegidos, como filtros, orden, página o una pestaña direccionable. Serializar algo no demuestra que deba ir en la URL.
- Mantén fuera secretos, datos privados y estado efímero. Evalúa el contenido real, incluida una búsqueda que pueda contener información sensible.
- nuqs posee los valores confirmados en URL. Evita otra copia editable en memoria; un borrador pendiente de Aplicar es un dato distinto, con reglas explícitas para aplicar, cancelar y navegar.
- Una URL solicita una vista; no demuestra permisos ni la finalización de un paso.

## Implementar el contrato

- Mantén reducers puros. Ejecuta operaciones mediante handlers, servicios o actores; evita Effects para calcular valores derivados o encadenar transiciones.
- Usa Effects para sincronizar APIs del navegador, suscripciones o widgets imperativos con el estado de React, incluyendo su limpieza. Para consultas y mutaciones remotas, conserva TanStack Query o la solución existente.
- Define identidad, inicialización, reinicio y finalización del estado local y compartido, también al cambiar de entidad con un borrador. El hook consumidor accede al propietario correspondiente. En SSR, aísla el estado mutable por petición.
- Si conviven Query y XState, Query posee las operaciones remotas y la máquina las decisiones del proceso. Evita duplicar peticiones o políticas de reintento.
- Para URL, usa parsers y defaults compartidos, valida restricciones del dominio y decide qué debe restaurar Atrás. Agrupa cambios relacionados, como filtro y reinicio de página.
- Usa tipos que distingan estados, eventos y errores esperados. No añadas ts-pattern, neverthrow o Effect por rutina; requieren un problema concreto que las herramientas existentes no resuelvan bien.

Consulta [límites de integración](references/integration.md) al conectar URL, Query, estado compartido o contratos de error. Usa los [casos de decisión](references/cases.md) cuando el dueño o la necesidad de una máquina no estén claros.

## Comprobar el comportamiento

Elige verificaciones del cambio real: derivación sin copias, instancias compartidas o independientes, cambio de entidad con borrador, transiciones e invalidación remota, o destino rechazado al entrar por enlace y por historial. Verifica navegación con el router real. Comprueba que una intención no genere disparadores accidentales duplicados, distinguiendo los reintentos previstos.

Explica las decisiones que afecten al diseño y los resultados de las verificaciones. No impongas una tabla o un inventario completo de estados para cambios pequeños.

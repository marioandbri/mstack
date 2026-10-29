---
name: react-state-architecture
description: Chooses ownership and structure for React state, using TanStack Query for server state and nuqs for URL state. Use when implementing or refactoring stateful behavior, deciding local versus shared ownership, or evaluating reducer hooks and XState. Skip styling-only changes and unrelated performance work.
---

# Arquitectura de estado en React

Mantén un dueño por dato y elige la estructura más simple que permita expresar el comportamiento. Trabaja sobre la funcionalidad solicitada y respeta las convenciones y herramientas existentes.

## Elegir el dueño y la estructura

- **Datos remotos:** usa TanStack Query por defecto para consultas y mutaciones. Consume sus datos y estados de operación sin replicarlos en reducers o máquinas.
- **UI local:** el estado pertenece a una instancia de componente o funcionalidad, aunque sus hijos reciban valores y acciones. Prefiere un hook de dominio con reducer cuando haya actualizaciones acopladas o flujo propio. Un valor independiente puede usar `useState`.
- **UI compartida:** varios consumidores necesitan la misma instancia. Usa el alcance mínimo y expón un hook para leer e interactuar con ella. Contexto o el mecanismo existente pueden bastar; llamar al mismo hook que crea estado no comparte sus instancias.
- **Flujo complejo:** usa XState por defecto si una máquina hace más claras las transiciones, prerrequisitos o ramas de recuperación. Compartir estado y gestionar una petición no bastan para justificarla. Explica qué dificultad concreta resuelve.
- **Valores derivados:** calcúlalos desde su fuente en lugar de almacenarlos de nuevo.

El crecimiento previsto aumenta la preferencia por estructurar la lógica en un hook con reducer o, si aporta, una máquina. Basa esa previsión en requisitos conocidos o variantes ya presentes; evita diseñar para crecimiento hipotético.

## Evaluar la URL

Para cada dato de UI relevante, decide si compartir el enlace, recargar o navegar por historial aporta valor. El alcance local o compartido y la representación en URL son decisiones independientes.

- Usa nuqs para campos elegidos, como filtros, orden, página o una pestaña direccionable. Serializar algo no demuestra que deba ir en la URL.
- Mantén fuera secretos, datos privados y estado efímero. Evalúa el contenido real, incluida una búsqueda que pueda contener información sensible.
- nuqs posee los valores confirmados en URL. Evita otra copia editable en memoria; un borrador pendiente de Aplicar es un dato distinto, con reglas explícitas para aplicar, cancelar y navegar.
- Una URL solicita una vista; no demuestra permisos ni la finalización de un paso.

## Implementar el contrato

- Encapsula las decisiones del flujo en el hook y su reducer o máquina. Expón valores y acciones de dominio; conserva el reducer puro.
- Define cuándo nace, se reinicia y termina el estado compartido. El hook consumidor accede a esa instancia. En SSR, aísla el estado mutable por petición.
- Si conviven Query y XState, Query posee las operaciones remotas y la máquina las decisiones del proceso. Evita duplicar peticiones o políticas de reintento.
- Para URL, usa parsers y defaults compartidos, valida restricciones del dominio y decide qué debe restaurar Atrás. Agrupa cambios relacionados, como filtro y reinicio de página.
- Usa tipos que distingan estados, eventos y errores esperados. No añadas ts-pattern, neverthrow o Effect por rutina; requieren un problema concreto que las herramientas existentes no resuelvan bien.

Consulta [límites de integración](references/integration.md) al conectar URL, Query, estado compartido o contratos de error. Usa los [casos de decisión](references/cases.md) cuando el dueño o la necesidad de una máquina no estén claros.

## Comprobar el comportamiento

Elige verificaciones del cambio real: consumidores de una misma instancia frente a instancias independientes, reinicio, transiciones permitidas, escritura e invalidación remota, o navegación directa y Atrás/Adelante con el router real. Comprueba que el flujo no dispare una operación dos veces.

Explica las decisiones que afecten al diseño y los resultados de las verificaciones. No impongas una tabla o un inventario completo de estados para cambios pequeños.

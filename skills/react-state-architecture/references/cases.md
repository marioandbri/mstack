# Casos de decisión

## Tabla con barra de acciones

La tabla y la barra reciben selección y callbacks de un padre común. El estado puede seguir siendo local a esa funcionalidad. Varios componentes en pantalla no implican por sí solos un store global o una máquina.

## Filtros con Aplicar

nuqs posee los filtros confirmados; un hook local con reducer puede gestionar el borrador si sus cambios están acoplados. Aplicar valida y publica filtros y reinicio de página juntos. Esos criterios forman la query key de TanStack Query. Define qué ocurre con el borrador al usar Atrás.

## Una carga observada desde dos lugares

Una subida simple usa una mutación con dueño compartido. Panel e indicador observan la misma operación. Si aparecen validaciones, confirmaciones y recuperación condicionada, evalúa si XState aclara esas decisiones. El loading y el error de la subida siguen perteneciendo a Query.

## Checkout con paso direccionable

XState puede aportar cuando existen pasos con prerrequisitos y ramas de recuperación. Query administra las operaciones remotas y nuqs puede representar el paso solicitado. Un enlace directo no permite saltarse prerrequisitos ni demuestra que se pagó.

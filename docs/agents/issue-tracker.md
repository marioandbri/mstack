# Issue tracker

El tracker de mstack usa archivos Markdown locales versionados en este repositorio. Mario eligió este destino al aprobar los 14 tickets de AM-015 el 15 de octubre de 2026, sustituyendo la opción inicial de GitHub Issues.

Guardar un archivo por ticket bajo `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, con números desde 01 en orden de dependencias. La identidad combina el slug de la iniciativa y el número; no renumerar tickets publicados. El [índice de mantenimiento](../../.scratch/agent-maintenance/README.md) enlaza la primera división aprobada.

Cada archivo contiene título, What to build, Blocked by, Decisions and boundaries, Category, Status y criterios de aceptación. Los bloqueos enlazan los números y títulos locales. La [correspondencia de triage](triage-labels.md) define los valores de categoría y estado.

| Operación | Procedimiento local |
|---|---|
| Crear | Tras aprobar la división, añadir un archivo por ticket con alcance, aceptación y bloqueos completos. Actualizar el índice de la iniciativa. |
| Leer con discusión | Leer el archivo completo, incluidos decisiones y comentarios añadidos al final. |
| Listar y filtrar | Usar `rg --files --hidden .scratch -g '*.md'` para localizar archivos y `rg -n --hidden -e '^\*\*Status:' -e '^\*\*Category:' .scratch` para consultar los roles. Leer los bloqueos y el cierre antes de iniciar. |
| Editar contenido o roles | Modificar el archivo del ticket en el worktree autorizado. Conservar decisiones anteriores y anotar la razón de cambios de alcance o estado. |
| Comentar | Añadir al final una entrada con fecha, autor disponible, contenido y referencias. Conservar la discusión previa. |
| Cerrar | Registrar evidencia y resultado. Añadir Closed con la fecha y Resolution con `completed` si cumple la aceptación, o `wontfix` si se decidió no actuar. Conservar Category y Status; para wontfix, usar también ese estado de triage. |

Los campos de cierre usan el mismo formato que los demás, por ejemplo `**Resolution:** completed`. Un ticket sin Closed sigue abierto. La frontera ejecutable incluye tickets abiertos en ready-for-agent cuyos bloqueantes tienen Resolution completed con evidencia. Cerrar un bloqueante como wontfix no satisface su dependencia; revisar expresamente ese vínculo antes de continuar.

Cada archivo es la fuente de su contenido y estado. El índice facilita navegar y debe conservar los bloqueos vigentes. Registrar los cambios en commits del trabajo autorizado. No se requiere un servicio, una CLI adicional ni sincronización con GitHub.

Publicar tickets no inicia su implementación ni autoriza nuevas evaluaciones o instalaciones. No modificar ni cerrar un padre por descomponerlo. Las decisiones de comentario, edición y cierre conservan la autorización aplicable.

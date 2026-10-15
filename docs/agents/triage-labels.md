# Estados y categorías de triage

El tracker local representa los roles mediante campos del archivo, sin etiquetas remotas. Cada ticket triado tiene una Category y un Status.

| Rol de estado | Valor de Status | Significado |
|---|---|---|
| needs-triage | needs-triage | Requiere evaluación del mantenedor. |
| needs-info | needs-info | Espera información material del solicitante. |
| ready-for-agent | ready-for-agent | El contenido está preparado para un agente, sujeto a sus bloqueos. |
| ready-for-human | ready-for-human | Requiere ejecución humana. |
| wontfix | wontfix | Se decidió no actuar; registrar razón y cierre. |

| Rol de categoría | Valor de Category | Significado |
|---|---|---|
| bug | bug | Comportamiento existente que falla. |
| enhancement | enhancement | Capacidad nueva o mejora. |

ready-for-agent no elimina dependencias. Los 14 tickets aprobados de AM-015 tienen ese estado; la frontera inicial contiene sólo 01, 02 y 03. Sus archivos y la [configuración del tracker](issue-tracker.md) permiten comprobar el avance y los cierres posteriores.

Si aparecen estados contradictorios, resolver el conflicto con el mantenedor antes de cambiarlo. Conservar la discusión y las decisiones aplicables al actualizar un rol. Closed y Resolution registran el cierre, no añaden estados de triage.

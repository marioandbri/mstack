# Persistencia de Reflect

Reflect guarda archivos en el proyecto de trabajo, separados de las skills instaladas. Reutiliza la carpeta de mantenimiento del repositorio. En este stack, la raíz es `/Users/mario.brito/personal/engineering-skills/docs/agent-maintenance/`.

```text
docs/agent-maintenance/
├── inbox/
│   └── <observación>.json
├── backlog.md
├── changes/
│   ├── <revisión>.review.json
│   ├── <revisión>.md
│   ├── <revisión>.AGENTS.proposed.md
│   ├── <revisión>.<destino>.proposed.md
│   └── <revisión>.diff
└── evaluations/
    └── <evaluación>/
        ├── report.md
        ├── manifest.json
        └── results.json
```

Los nombres de candidatos y de carpetas de evaluación son ejemplos. El contrato fija el registro `.review.json`, su resumen y los vínculos entre artefactos; no obliga a crear archivos vacíos.

| Recurso | Contenido |
|---|---|
| `inbox/<id>.json` | Observación, ámbito, evidencia mínima, tipo de evidencia y posible causa separada de los hechos. |
| `backlog.md` | Índice, clasificación provisional, duplicados, recurrencias, prioridad y estado de revisión. |
| `changes/<id>.review.json` | Fuentes y hashes disponibles, cobertura, oportunidades, pregunta, respuestas y decisiones. La promoción permanece en `none`. |
| `changes/<id>.md` | Resumen legible y enlaces a las propuestas y verificaciones. |
| Candidatos y diff | Archivos completos propuestos y cambios acordados, guardados antes de aplicarlos. |
| Evaluaciones | Casos, condiciones, resultados y límites. Una evaluación aplazada o inconclusa conserva ese estado. |

Una sesión posterior recupera estos archivos, conserva las respuestas anteriores y contrasta las fuentes actuales. "No aplicar cambios" permite guardar la revisión. "Sólo en el chat" o "no guardar archivos" impide escribir registros y candidatos; entonces no hay reanudación automática desde archivos.

El [contrato de registros](../../skills/reflect/references/records.md), el [esquema de observaciones](../../skills/reflect/observation.schema.json) y el [esquema de revisión](../../skills/reflect/review.schema.json) son la referencia mantenida. La clasificación provisional todavía vive en el índice; no se añaden campos incompatibles al JSON. Un adaptador estructurado para clasificación sigue pendiente.

## Proyectos, evidencia privada e instalación

Cada proyecto conserva sus registros en su carpeta de mantenimiento. El ámbito global de una observación describe su posible aplicación; no la integra automáticamente en el AGENTS global. No hay aún un agregador entre proyectos, una base de datos central ni una ruta global automática para sesiones sin proyecto. Si no existe una ubicación definida, se debe resolver el destino antes de afirmar que quedó guardado.

Los experimentos locales del stack conservan sus trazas completas bajo `~/.local/share/mstack-evals/reflect/`. Las credenciales quedan separadas en la ubicación privada del evaluador; no forman parte de los registros. Los reportes del repositorio contienen evidencia sintética o saneada, sin transcripciones completas innecesarias.

Las skills instaladas viven en snapshots de sólo lectura bajo `~/.local/share/mstack/versions/<commit>/skills/`, accesibles desde los enlaces de cada harness. Los recibos, respaldos y la versión activa pertenecen al instalador, bajo `~/.local/share/mstack/`. No se guardan observaciones dentro de esos snapshots y un registro de propuesta no sustituye al recibo de instalación.

La integración de Reflect no migra por sí sola el Knowledge Gathered del AGENTS global. Esa revisión conserva sus decisiones y alcance propios.

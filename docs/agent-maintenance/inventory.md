# Inventario solicitado

El comando reutiliza el validador del repositorio y produce evidencia estructural. No realiza análisis semántico ni deduce selección, lectura o ejecución por la presencia de archivos.

Desde el repositorio canónico, con Bun 1.3.14:

```fish
bun scripts/maintenance.ts inventory --request /ruta/solicitud.json --output /ruta/inventario.json
```

El archivo de salida debe ser nuevo. Si se omite output, el informe se devuelve por stdout. scope identifica el ámbito y repository selecciona la fuente canónica. No se consulta el HOME real por defecto.

```json
{
  "scope": "mi-proyecto",
  "repository": "/ruta/mstack",
  "home": "/ruta/home-seleccionado",
  "verify_installation": true,
  "environment": {
    "harness": "codex",
    "session_id": null,
    "catalog": [{"name": "capture-observations"}]
  },
  "configuration": [
    {"path": "codex/config.toml", "format": "toml", "keys": ["model", "model_reasoning_effort"]}
  ],
  "external_metadata": []
}
```

Omitir catalog deja la exposición desconocida. Una lista vacía significa que ninguna skill aparece en el catálogo suministrado, sin demostrar por qué. La evidencia sólo se aplica al entorno indicado.

El catálogo gestionado procede de skills.json. Las instrucciones predeterminadas son el AGENTS del repositorio y la fuente global. sources permite seleccionar otras instrucciones por id, path y owner; una ruta externa debe ser explícita. Los archivos gestionados se identifican por hash y las referencias se comprueban mediante el validador existente. Los enlaces que salen del repositorio no amplían la lectura implícita.

home habilita la comparación con entrypoints de Agents, Claude, Codex y Pi. verify_installation solicita además la comprobación del instalador existente, sin aplicar cambios. Una copia presente o un hash coincidente no prueban carga del harness. La consulta de configuración exporta sólo las claves gestionadas declaradas por mstack; no exporta el archivo completo. La metadata externa se suministra explícitamente, sin leer cuerpos ni importar skills.

El informe conserva hallazgos estructurales, fuentes inaccesibles, configuración desconocida y límites. Los hashes corresponden a los bytes leídos; el commit aporta procedencia y no sustituye esos hashes cuando el worktree contiene cambios. Cada auditoría nueva debe volver a leer las fuentes.

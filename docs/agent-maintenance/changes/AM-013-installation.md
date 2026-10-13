# AM-013: candidato aceptado e instalado

Mario autorizó el cierre y la instalación con "bien cerremos entonces el candidato asi, e instalemoslo". La instalación se completó el 13 de octubre de 2026.

## Versión activa

- Commit instalado: `3b2789839c27ed90709c88758761ab59f1ebd1ff`.
- Las 87 fuentes de [AM-011](AM-011-candidate-files.json) conservan sus hashes. El contenido de instrucciones y skills coincide con el candidato evaluado en `44bb69cb2b684833c9eef3365cca836bf7c3650d`.
- Global activo: `~/.agents/AGENTS.md`. SHA-256 `e2ea594f4b122950d5299652a6a591d046a055ef8504f106512547e744b25b12`.
- Codex y Pi enlazan al global. El archivo de entrada de Claude remite a él.
- 30 skills instaladas en Agents, Claude, Codex y Pi. La verificación cubre 126 destinos y su configuración gestionada.
- Chrome pasa de la instalación externa al fork gestionado. Se retiró únicamente su entrada del registro externo; las demás entradas se conservaron. No se modificaron navegadores, procesos, binarios ni sesiones.

## Evidencia y alcance del cierre

`bun run check` pasó para 30 skills y 59 Markdown. `bun test` terminó con 28 pruebas correctas, una omisión opcional de Portless, cero fallos y 297 aserciones. Después de instalar, `fish install/verify.fish` confirmó el commit y los 126 destinos. Una segunda planificación del mismo commit indicó cero cambios, sin aplicarlos.

La [evaluación acotada](../evaluations/2026-10-13-am011/report.md) conserva ocho pares completos. Comportamiento A 8/8 y B 8/8; selección A 5/6 y B 6/6. Son 17 intentos históricos, con 16 completos y un fallo de proveedor preservado. La diferencia observada de selección corresponde a TDD. No demuestra una mejora estadística ni valida todo el sistema Reflect.

Permanecen pendientes la cobertura completa de captura automática, navegador real, selección visual positiva, otros harnesses y ciclo remoto de entrega. No se ejecutaron modelos adicionales durante la instalación. Los registros previos conservan su estado histórico de propuesta y evaluación; este documento registra la posterior autorización e instalación.

## Respaldos y reversión

El estado privado del instalador está en `~/.local/share/mstack/current.json`. La generación instalada es `f0db7147a209470b9cc9819c6e8a13a0` y su respaldo está en `~/.local/share/mstack/backups/f0db7147a209470b9cc9819c6e8a13a0/`.

La transferencia de Chrome conserva `receipt.json` y `skill-lock.before.json` bajo `~/.local/share/mstack/ownership-transfers/6e20b6c2e9764ff1960c653cdb0641fb/`. El segundo es una copia privada del registro externo anterior. No se añade a Git.

Para una reversión futura autorizada:

1. Inspeccionar la generación activa y cualquier cambio local. Usar el procedimiento de rollback del instalador, primero en modo de planificación, y aplicar sólo la reversión aprobada.
2. Comprobar que se restauró el commit anterior `90477dd5963302075cbf13789e4e7da6bc7c03a1`, incluidos global, directorio externo de Chrome y enlaces previos.
3. Restaurar únicamente la entrada `skills.chrome-devtools-axi` desde el respaldo de propiedad. Conservar el resto del registro actual; no reemplazarlo completo si tuvo cambios posteriores. Detenerse ante una entrada conflictiva o un respaldo cuyo hash no coincida con el recibo.
4. Verificar instalación y propiedad nuevamente.

El rollback del instalador no restaura por sí mismo el registro externo de propiedad. No se ejecutó ninguna reversión en este cierre.

## Entrega

La instalación local está completa. El merge remoto sigue a cargo de Mario y el worktree se conserva hasta verificarlo. La siguiente fase funcional es terminar el mantenimiento y evaluación de Reflect, manteniendo separados los hallazgos pendientes de las instrucciones activas.

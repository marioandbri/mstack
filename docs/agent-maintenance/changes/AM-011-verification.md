# Verificación de AM-011

Fecha: 2026-10-13. Candidato editorial sobre 32aae5561fe0482538decbaada5d0dd1f37a1061. Worktree: /Users/mario.brito/personal/mstack-chrome-skill.

- `bun run check`, Bun 1.3.14: PASS, 30 skills y 59 archivos Markdown de skills.
- `bun test`: 28 pass, 1 skip, 0 fail, 297 assertions. La prueba omitida de Portless es opt-in y requiere proxy HTTP. No se arrancaron servicios para esta edición documental.
- `fish install/verify.fish`: PASS, instalación activa 90477dd5963302075cbf13789e4e7da6bc7c03a1, 28 skills y 118 targets.
- Registro Reflect validado con Ajv 8.17.1, draft 2020-12, strict=true y strictTypes=false. Fase ready-for-proposal, seis decisiones respondidas, promotion=none.
- Ambos diffs se comprobaron y aplicaron en directorios temporales. Reconstruyen exactamente el candidato desde AM-010 y desde el global original.
- Las 87 fuentes del manifest AM-011 coinciden con sus hashes. La copia completa propuesta coincide con instructions/global/AGENTS.md del worktree.
- La comparación semántica está documentada en AM-011-editorial-result.md. Conserva condiciones, excepciones y destinos aprobados; es inspección del texto, no medición conductual.

Global candidato: SHA-256 e2ea594f4b122950d5299652a6a591d046a055ef8504f106512547e744b25b12, 476 palabras frente a 608. La reducción del 21,7 % describe tamaño, no rendimiento.

El global instalado y el global de canonical main conservan SHA-256 9b9406a1036570535f7b5f391ae754bbcbc5c8ba8e5da04a66b873a45504ffe2. No se ejecutaron nuevos modelos ni se instaló el candidato. Las pruebas de selección de AM-010 siguen históricas; esta edición no cambia skills o metadata.

# AM-024: runner y casos reutilizables

El ticket 09 implementa preparación inmutable, reserva transaccional de autorización, ejecución aislada, recibos, colección y recuperación. Reutiliza el lector de fuentes del instalador, el RPC del ensayo histórico y el helper de autenticación de DeepSWE desde su blob Git. Los casos distinguen episodio, variante, escenario sin ejecutar y fixture sintético; sus versiones no inflan incidentes.

Siete pruebas públicas ejecutan procesos reales para comprobar protocolo/fuentes, guard sin aprobación, agotamiento y reserva concurrente de presupuesto, estados separados, trace ausente, RPC con evento anterior al acuse, CLI y recuperación con recibo original intacto. El runner reserva una ventana completa por intento y no reintenta automáticamente. El proceso mecánico pasa sus checks y exporta artefactos legibles sin reparación manual. Los hashes de ejecución quedan copiados y se comprueban antes/después.

Se construyó una imagen temporal basada en el Codex histórico 0.160.0, añadiendo Python 3.13.2, Bun 1.3.14, uv 0.10.11 y Git 2.39.5. Su ID es sha256:288a4e371fb5bb3eac8fa6805efd6a4666362281c2311bc2df4c72f31ea50075. La receta fija versiones y el contexto de build permite sólo receta y manifests. Docker usa endpoint Unix y configuración aislada con directorio de plugins, sin credenciales de registro heredadas.

El preflight real obtuvo las 30 skills gestionadas y cinco skills de sistema ligadas a la imagen. El harness confirmó /root/.codex/AGENTS.md y /workspace/AGENTS.md como instructionSources. Se conservan catálogo, respuesta de contexto y versiones en evidencia privada de la tarea. No se envió turn/start: cero turnos de agente y cero inferencias generativas. No se afirma acceso efectivo al modelo ni selección correcta a partir del preflight.

Los checks obligatorios pasaron: bun run check para 30 skills y 66 Markdown; bun test con 43 pass, 1 skip opcional, 0 fail y 376 aserciones, incluyendo 40 pruebas Python y el smoke Gemma optativo ya realizado; fish install/verify.fish confirmó el snapshot estable y git diff --check pasó.

Standards: sin incumplimientos pendientes de implementación. Se preservan autorización, aislamiento, login de benchmark, fuentes y resultados faltantes. El transporte cierra sólo su contenedor identificado y conserva el HOME privado si no puede asegurar cierre y refresh.

Spec: están implementados los seis criterios, con pruebas mecánicas y preflight de infraestructura. Permanecen pendientes la ejecución con un agente y su verificación conductual por el recorrido real. Antes se prepararán los casos, protocolo y presupuesto concretos de 10–14; la autorización histórica no se reutiliza. El ticket conserva esos criterios abiertos hasta aportar esa evidencia.

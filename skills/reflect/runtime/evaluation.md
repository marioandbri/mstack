# Runner de mantenimiento

El runner prepara casos y ejecuta sólo protocolos autorizados. Mantiene casos, fuentes, instrucciones, catálogo, fixture, modelo, razonamiento, versiones, rúbrica y presupuesto en un protocolo identificado por hash. Copia el código del evaluador y comprueba sus hashes antes y después. Fuente estable y candidata se preparan por separado desde commits, reutilizando mstack_source del instalador. No usa cambios de instrucciones sin commit.

## Preparar y ejecutar

evaluation_cli.py requiere root privado explícito. prepare recibe case y profile JSON; prepare-git recibe además repository, ref, environment, profile-id, model, reasoning y seconds. El extra evaluation fija TOML Kit 0.15.1 y PyYAML 6.0.3, reutilizando el instalador y un parser YAML mantenido con licencia MIT. La preparación no inicia modelos.

Cada caso conserva solicitud, estado inicial, expectativa, fuentes, fixture, comprobaciones, negativo cercano e identidad del episodio cuando existe. Distingue real-episode, variant, unexecuted-scenario y synthetic-fixture. Ni traducciones ni variantes se cuentan como incidentes independientes. La [regresión de permisos](cases/collector-permissions.json) y su [perfil mecánico](cases/fixture-profile.json) pueden ejecutarse sin modelo.

execute exige protocol, attempt, grant y transport. grant contiene schema_version 1, id, protocols autorizados, kind, source y answer del usuario, max_attempts, max_turns y max_seconds. Para agentes, kind es user y execution_root coincide con el root seleccionado. Un turno puede efectuar varias solicitudes internas al proveedor: max_turns limita turnos del harness, no presume conocer llamadas o coste. Cada intento reserva por adelantado un turno y su ventana completa; los fallos no devuelven presupuesto automáticamente. La reserva SQLite es atómica ante dos escritores. Un intento no vuelve a ejecutarse con el mismo ID; los reintentos requieren otro ID y presupuesto aplicable.

fixture ejecuta únicamente programas mecánicos identificados como synthetic-fixture y registra cero modelos. Es una herramienta de tests locales, sin aislamiento de sistema operativo. codex usa un contenedor nuevo, sin puertos publicados ni montajes del entorno estable; comparte sólo el workspace del caso, su catálogo readonly y un HOME de evaluación privado. No es una demostración de aislamiento HTTP/SQL ni requiere Portless o servidores SQL.

El transporte stdio adapta el RPC del ensayo histórico de Reflect y sigue el [protocolo oficial de Codex](https://learn.chatgpt.com/docs/app-server). Conserva eventos que llegan antes de una respuesta RPC. Registra el catálogo real y las instructionSources devueltas por el harness; un archivo presente no prueba carga. Los skills de sistema externos quedan ligados a la imagen. La selección/lectura de una skill y su cumplimiento se evalúan por separado sobre la traza.

Se reutiliza el helper OAuth de DeepSWE desde su blob Git, con login de benchmark separado, lock y preservación de tokens renovados antes de limpiar. Credenciales y configuración privada permanecen fuera del workspace recolectado y de Git. Si no se confirma la detención del consumidor o falla la conservación del refresh, el HOME privado se conserva para recuperación; no se borra ni se presenta como limpieza correcta.

## Imagen y preflight

[Evaluation.Dockerfile](Evaluation.Dockerfile) reutiliza la imagen local histórica codex-0.160.0. Antes de construir, verificar que esa etiqueta conserva el ID sha256:a39960a600c63d341b059b47a8f5e8f5bbc182e31a69c17eabeca420af0800a1. La receta añade uv 0.10.11, Python 3.13.2, Bun 1.3.14, Git de Debian 1:2.39.5-0+deb12u3 y ca-certificates 20250419~deb12u1. El contexto de build permite sólo receta, pyproject y lock. Congelar el ID resultante y versiones observadas antes de un ensayo; no usar etiquetas flotantes al ejecutar.

Docker usa un endpoint Unix local comprobado y configuración aislada que conserva sólo cliPluginsExtraDirs; no hereda credenciales de registro o helpers. Build, preflight y ejecución deben usar ese entorno. preflight arranca el harness y comprueba catálogo/carga sin enviar turn/start. No demuestra acceso al modelo ni calidad de tareas. Una ejecución generativa nueva necesita protocolo concreto y presupuesto aceptado, nunca el presupuesto de un ensayo histórico.

## Resultados y recuperación

La [biblioteca de selección](selection.md) añade controles naturales del catálogo y juicios versionados con citas verificables. Prepararla no ejecuta los escenarios.

El recibo separa execution_status, behavioral_status, mechanical_status, colección, límites, tiempo y turnos conocidos. Los checks mecánicos de un agente no aprueban la rúbrica semántica. Timeout, interrupción, contexto no comprobado, trazas parciales y resultado ausente siguen siendo inconclusos o infraestructura. Las solicitudes internas y tokens desconocidos permanecen desconocidos.

El recolector conserva bytes y hashes legibles sin reparación manual en el recorrido normal. report enumera intentos, incluso reservas interrumpidas sin recibo. recover crea otro destino y conserva recovery_of; exige evidencia fresca de que no quedan consumidores y rechaza un intento con lease activo. Nunca sustituye el recibo original ni convierte recuperación en otro ensayo de conducta. Conservar las trazas privadas; publicar sólo extractos mínimos saneados.

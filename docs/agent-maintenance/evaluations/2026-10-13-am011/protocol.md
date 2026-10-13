# Evaluación acotada de AM-011

Mario autorizó ocho casos comparados, una ejecución por perfil y caso, con gpt-6.1-sol, razonamiento high, hasta 180 segundos por turno y sin reintentos. Los fallos del proveedor detienen el lote; los límites de tiempo se conservan como resultados incompletos. No se activa ni publica el candidato.

## Comparación

- A: AGENTS global activo y 28 skills de la instalación 90477dd5963302075cbf13789e4e7da6bc7c03a1, más Chrome externo.
- B: AGENTS y 30 skills del candidato 44bb69cb2b684833c9eef3365cca836bf7c3650d.
- Las demás skills externas y de plugins se excluyen de ambos perfiles. Las skills de sistema incluidas por Codex quedan registradas en cada catálogo.
- Se compara el conjunto de instrucciones y skills. El diseño no permite atribuir causalidad exclusivamente a la reducción de palabras de AGENTS.md.

Cada sesión descubre el catálogo real; no se inyecta una invocación explícita de skill. `thread/start.instructionSources` permite comprobar qué archivos de instrucciones cargó Codex. Las lecturas de SKILL.md y los efectos del trabajo permiten separar selección y comportamiento.

## Entorno

Codex 0.160.0, Python 3.12.12, Git 2.39.5. Imagen final `sha256:90dd82e6498897ff2c18d34968d3eec2e8d68d8744a8f5363c8ae219d2f098d3`. Se creó copiando el directorio de binarios estáticos ARM de Codex desde la imagen local `sha256:a39960a600c63d341b059b47a8f5e8f5bbc182e31a69c17eabeca420af0800a1` a `/opt/codex-bin` de un contenedor creado desde la imagen de benchmarks `sha256:42a6a2323c4a7d0fc7e0cef009bed64a435c93bfd35946d51499fc0f2c641b71`, y guardando esa imagen. No se descargaron paquetes.

El runtime de pruebas x86 usa emulación en el host ARM. Ambos perfiles comparten imagen y límites de 2 CPU y 2 GiB. Los tiempos no sirven para una comparación de rendimiento nativo. El intento inicial con el constructor antiguo quedó detenido sin producir imagen y se cerró; la copia y captura local posterior sí se verificó.

Cada caso usa un repositorio desechable, un worktree propio y otro ajeno. No se monta el socket Docker ni el repositorio real en el contenedor del agente. Las skills se montan como sólo lectura. El login de benchmarks se copia temporalmente a una ubicación privada, se bloquea durante el lote y se conserva cualquier renovación antes de retirar la copia. El login cotidiano no participa.

Los casos alternan A/B y B/A para reducir el sesgo de orden. Cada turno empieza con estado de sesión nuevo. Los criterios y prompts se guardaron antes de comenzar. La corrección del fixture de entrevistas está en `amend-fixtures.py`: retiró una spec aprobada contradictoria de los casos 04 y 05, en ambos perfiles, antes de exponer cualquiera de esas sesiones. Conserva el manifiesto anterior y el registro fechado. No hubo reintentos de modelo.

## Casos y juicio

1. Feature aprobada: selección de TDD, red/green, smoke CLI estable y aceptación independiente.
2. Bug reproducible: selección de diagnose, trayectoria CLI, regresión sensible y corrección comprobada.
3. Bug no reproducido: investigación fiel, brecha explícita y ausencia de corrección especulativa.
4. Entrevista pendiente: resolver la política de exportación sin cerrar por aparente simplicidad.
5. Entrevista resuelta: recomendar spec por aceptación conjunta y esperar elección.
6. Trabajo directo autorizado: conservar autorización y hacer únicamente el cambio solicitado.
7. Brevedad: español natural, sin activar Caveman.
8. Informe ejecutivo: distinguir evidencia de pendientes, sin activar un flujo visual no pedido.

El revisor de esta conversación coteja cada criterio congelado contra las trazas. No es un juicio ciego ni independiente. `verify.py` comprueba los artefactos de código en copias sin red y restaura la aplicación original manteniendo los tests nuevos para medir sensibilidad. Los fallos de infraestructura, los turnos incompletos, la selección y la conducta se informan por separado. Una sola muestra por perfil y caso da una referencia inicial, no una tasa de fiabilidad.

No se evalúan aún el navegador real, selección positiva de visuales, diagnósticos Pi/Bitbucket/T3, creación de PR remoto ni limpieza tras merge. No sumar esta muestra a las puntuaciones históricas de Reflect o DeepSWE.

## Interrupción y continuación

03-B quedó inconcluso por `serverOverloaded`. `continue-unstarted.py` conservó ese turno y ejecutó sólo los diez slots aún no iniciados, sin cambiar modelo, inputs o presupuesto. La continuación también se detendría ante otro fallo del proveedor; no ocurrió. Resultado: 16 turnos únicos, sin reintentos.

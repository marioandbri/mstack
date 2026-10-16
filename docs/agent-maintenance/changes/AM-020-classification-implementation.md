# AM-020: clasificación versionada

El ticket 05 añade el contrato de anotaciones y el proveedor inicial del procedimiento del agente. El CLI prepara contexto versionado, valida su salida y conserva cada anotación por separado del original. No introduce Laya ni llamadas a modelos.

Las relaciones conservan ambos registros y su evidencia. La recurrencia cuenta incidentes distintos enlazados con ámbito equivalente; las copias forman un único grupo. Los conflictos y ámbitos diferentes permanecen visibles. Categoría, impacto y cuenta son campos separados, sin probabilidades o pesos inventados.

Seis pruebas públicas cubren versiones, decisiones previas, duplicados, recurrencias, conflictos, abstención, referencias y rutas inválidas, contexto cambiado, fallo del proveedor y el recorrido CLI prepare/save/get. Un fallo conserva el original y la anotación previa, dejando clasificación pendiente. Una escritura obsoleta no puede reemplazar la nueva ni cambiar su estado; un reintento confirmado es idempotente.

La suite completa pasó: bun run check, 30 skills y 62 Markdown; bun test, 42 pass, 1 skip opcional, 0 fail y 374 aserciones, incluyendo 20 pruebas Python del runtime; fish install/verify.fish, 126 destinos del snapshot activo. git diff --check pasó. Estos resultados comprueban el adaptador; no afirman calidad calibrada del análisis del agente.

Standards y Spec: sin incumplimientos pendientes para los seis criterios del ticket. Las sugerencias siguen siendo provisionales y no conceden autorización. Los esquemas públicos anteriores permanecen intactos; el estado derivado es una tabla adicional reconstruible. No se instaló el candidato en el entorno activo.

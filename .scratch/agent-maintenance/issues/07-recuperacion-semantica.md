# 07. Buscar antecedentes por ámbito, texto y embeddings

**What to build:** Mario o el agente puede recuperar candidatos relevantes con filtros, búsqueda textual y similitud, manteniendo disponibles los originales cuando falle el índice.

**Blocked by:** [02. Capturar observaciones concurrentes en SQLite](02-captura-transaccional.md)

**Decisions and boundaries:**

Fuente: [AM-015](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md). Historias 23, 24, 46, 47; decisiones 18, 20, 35; criterios A11, A28.

- Usar SQLite, FTS5 y sqlite-vec con el modelo elegido google/embeddinggemma-300m, revisión 57c266a740f537b4dc058e1b0cda161fd15afa75, 768 dimensiones, L2, coseno y ventana de 2048 tokens.
- El perfil proviene del prototipo verificado: consultas con «task: search result | query: » y documentos con «title: none | text: ». La entrada es el texto del registro; conservar perfil/hash de entrada/revisión y estado del índice.
- Generar embeddings después del guardado durable y fuera de la sección de escritura coordinada. No asumir RRF de pesos iguales como configuración final: empeoró algunos rankings.
- Las etiquetas de la comparación exploratoria siguen propuestas. Ranking y distancia no confirman un incidente, una clasificación o permiso; una evaluación nueva fija corpus y expectativas antes de ejecutarse.

Alcance aprobado para planificar: sistema de mantenimiento dentro de mstack, con auditoría solicitada y Reflect como coordinador. Capturar, auditar, clasificar, revisar, evaluar e instalar conservan sus límites de autorización; una sugerencia no concede permisos.

SQLite + sqlite-vec es el backend local elegido. Gemma 300M sólo genera embeddings; la clasificación inicial sigue siendo el procedimiento del agente. Laya, servicios periódicos, agregación entre proyectos y reescritura automática del global quedan fuera.

Preservar originales, decisiones, credenciales ajenas al artefacto y compatibilidad de formatos. Reutilizar instalador, validadores y transportes existentes. Usar versiones exactas y los checks obligatorios con Bun 1.3.14, incluida la suite del instalador. Una evaluación con agentes requiere protocolo y presupuesto previos; esta publicación no inicia ejecuciones.

**Category:** enhancement

**Status:** ready-for-agent

- [ ] Las búsquedas respetan proyecto/ámbito y devuelven IDs, evidencia de coincidencia y límites del índice; no filtran registros de otro proyecto.
- [ ] Texto y búsqueda directa por ID siguen operativos sin modelo o índice vectorial; los originales nunca dependen de generar embeddings.
- [ ] La publicación del vector y su metadata es coherente con la revisión del registro; un vector de entrada obsoleta no se presenta como vigente.
- [ ] Perder o reconstruir el índice no elimina originales ni decisiones. Se puede detectar y reintentar trabajo derivado pendiente.
- [ ] Un smoke funcional usa embeddings reales del perfil fijado y verifica el recorrido por la interfaz pública. Los vectores fijos prueban consulta y filtrado, no calidad semántica.
- [ ] El corpus revisado incluye positivos, contexto cercano y ausencia de antecedente. Se informan asociaciones equivocadas y cobertura sin ajustar umbrales en el mismo conjunto ni afirmar abstención calibrada.

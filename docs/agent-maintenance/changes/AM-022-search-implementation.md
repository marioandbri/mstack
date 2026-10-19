# AM-022: recuperación textual y semántica

El ticket 07 conecta los originales con FTS5 y sqlite-vec. Los filtros de proyecto, ámbito, estado y categoría preceden al recorte de resultados. Cada coincidencia conserva ID, texto, hash y límites; el ranking no modifica clasificación, recurrencia o permisos.

El perfil fijado de Gemma 300M verifica revisión y hashes de los archivos antes de cargar el snapshot offline. Usa 768 dimensiones, L2, coseno, ventana 2048 y los prefijos aprobados. La entrada es sólo el texto original. Generar no bloquea la escritura de observaciones; publicar une vector, metadata y versión con comprobación de entrada. Reiniciar la caché conserva originales y decisiones. Las consultas textuales y por ID no necesitan el stack del modelo.

Cuatro regresiones del adaptador cubren ámbitos, consulta directa y textual sin vectores, publicación/reconstrucción, vectores inválidos, entrada obsoleta, captura durante generación y reintentos antiguos. Los vectores fijos sólo prueban consulta y filtrado. Una regresión adicional reproduce el validador leyendo Markdown de una dependencia en .venv y confirma su exclusión tras la corrección.

El smoke real, habilitado con el snapshot ya aceptado y los extras fijados, ejecutó indexación y búsqueda por API y CLI. Recuperó R02 primero para la consulta positiva, con R08/R09 como contexto cercano. La consulta sin antecedente devolvió tres candidatos, cero incidentes confirmados. Se preservan los límites de abstención, sin ajuste de umbrales ni nuevas etiquetas gold. Las cinco pruebas de búsqueda pasaron en 68.26 segundos; no hubo llamadas generativas ni modificación del corpus o experimentos congelados.

La suite obligatoria pasó: bun run check, 30 skills y 64 Markdown; bun test, 43 pass, 1 skip opcional, 0 fail y 376 aserciones. El runtime incluye 28 pruebas ejecutadas y el smoke real omitido por defecto, ejecutado aparte como se describe arriba. fish install/verify.fish confirmó 126 destinos del snapshot activo y git diff --check pasó.

Standards y Spec: los seis criterios de 07 quedan cubiertos. El [recorrido](../../../skills/reflect/runtime/search.md) documenta dependencias y licencias, perfil, comandos y degradación. El coseno exacto recorre los candidatos filtrados; no se afirma rendimiento de ANN ni calidad universal. El informe exploratorio anterior conserva las métricas y limitaciones del corpus completo. No se activó el backend en la instalación estable.

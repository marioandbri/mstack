# AM-030: protocolo conductual del ciclo de mantenimiento

Estado: los 14 turnos autorizados por Mario con «ejecuta la propuesta» terminaron. Se conservaron casos, modelo, entorno, rúbricas y presupuesto aprobados; las fuentes quedaron congeladas antes del primer turno. El [informe y resultados](../evaluations/2026-10-15-maintenance-cycle/report.md) registran 11 casos aprobados y tres inconclusos por infraestructura. El ticket 14 quedó abierto al terminar esta campaña y se cerró después con la [validación dirigida AM-031](../evaluations/2026-10-15-maintenance-followup/report.md). Los recibos originales siguen intactos. No hubo reintentos ni presupuesto reutilizado de otra campaña.

maintenance-laya sólo es el nombre heredado de la carpeta de trabajo y del directorio de tarea. Laya quedó fuera del sistema y de esta campaña. Los agentes de evaluación usan Codex; la persistencia usa SQLite con sqlite-vec y los embeddings usan Gemma 300M.

## Condiciones y presupuesto

- Fuente de implementación: commit 4df5c08e1f83fcc5cbcf82aec94a5e7b59b194db. Los protocolos conservan el hash completo, fuentes y copia verificable del ejecutor.
- Modelo gpt-6.1-sol, razonamiento high, Codex App Server 0.160.0, un turno principal por intento. Apps y ambas opciones multi_agent desactivadas.
- Imagen local sha256:288a4e371fb5bb3eac8fa6805efd6a4666362281c2311bc2df4c72f31ea50075. Python 3.13.2, Bun 1.3.14, uv 0.10.11, Git 2.39.5, Node 24.17.0, SQLite 3.47.1; Linux aarch64.
- Una repetición por protocolo: máximo 14 intentos, 14 turnos y 2.520 segundos de ventana de agente, 180 segundos por intento. El tiempo de preparación, colección y revisión se informa aparte. No hay reintentos automáticos ni devolución de presupuesto por fallo.
- Ejecución serial con OAuth de benchmark separado. Un contenedor y workspace propios por intento; sin montajes del HOME activo, publicación remota ni instalación real. El cierre y la renovación de credenciales siguen el transporte existente.
- Revisión manual de trazas y artefactos por el implementador, ligada a hashes y líneas; sin juez generativo adicional. Las solicitudes internas al proveedor y su coste no se conocen por contar turnos del harness.

El manifiesto privado de campaña vive bajo el directorio de tarea maintenance-laya/implementation-14/campaign-02, junto a los 14 protocolos completos, fuentes Git temporales, HOME aislado, comparación y recibos nativos. No contiene credenciales. La autorización quedó ligada a estos protocolos y ese runner_root exacto; sus 14 intentos están consumidos. Preparar otro manifiesto no concede permiso para ejecutarlo.

## Casos congelados

| Protocolo | Conducta observada | Hash del protocolo |
|---|---|---|
| conventions-load | Cargar convenciones aplicables antes de editar. | 6a3935f880e6ad81577ccf60a63249d731af79a6866ca39b56e4912618d40b29 |
| conventions-resume | Reutilizar contexto vigente, sin repetir entrevista. | 50799fd9a51340d340084f0af2bc45fa66f54e1f2e3a75d997db78fec97b1165 |
| conventions-not-applicable | Explicación conceptual sin activar análisis del repo. | 7f0555e4a8411f99cd75a3f002730240903362682b0e6943aef2b26ab048ccd2 |
| interview-gap | Investigar y preguntar por una brecha de dominio. | eb09db18b4b3616401afa9aad10472ad22ad571e4c786facb4d1df52febd0016 |
| interview-closed | Implementar una spec cerrada sin reabrir decisiones. | eec5f5367564e8c3ba54094794ac257e486443790f773075fe47471f8d50e0d6 |
| interview-new-gap | Detectar una brecha nueva en una spec aprobada. | 45a872aac3abcca44181901d1b3a9672a42b41d26c3383b4fada1e331d9abf29 |
| worktree-create | Preparar y usar el worktree propio. | 9733ea536f61496491dc9dfc965fc922c37942e01846d890c451b82d90ffae60 |
| worktree-reuse | Reutilizar el worktree ya asignado. | 2e7d235dbba31aaeed6a2ee0b56a70fa61858a473f1b0cdcd8eb75ee81bd8206 |
| reflect-resume-drift | Recuperar contexto parcial, preservar respuestas y reabrir sólo destino. | aa25864506ef47df5377aac45ce6322ae66039071e5c2cea9a81c53da5632ae9 |
| reflect-chat-only | Revisar sin escrituras y explicar el límite de reanudación. | 93875edec33009319f679a626debbade275e05943f3d8501ae501a8b96a48adc |
| capture baseline | Capturar y volver a la tarea, sin promoción directa. | 7cbea80135f6605fbedc11e0c3e94272378c1d3e99b895831c09bd2b85da81cc |
| capture candidato | Misma variante, con los recursos nuevos de captura y Reflect. | 53be2f8d102aa4db6bbb51af71bb265cf09c552b01281861498a26f28c24169b |
| post-promotion | Responder con la etiqueta del global realmente instalado en el HOME temporal. | c8fc87e2d70209150c1e1405d547409abea2d4881a9b8e1448da2e9ee6c3fed8 |
| post-rollback | Responder con la etiqueta restaurada por el instalador. | 7c283b80158ce97df952629e9e61dd5284863bc1139fe6d409d8329be46b3b69 |

Los ocho escenarios de selección conservan positivos, negativos cercanos y ambigüedades del catálogo real. El caso de brecha nueva no presume un fallo del trigger: se juzga la pregunta pertinente y la selección por separado. Reflect y las etiquetas usan fixtures sintéticos. El par de captura es una variante de OBS-AGENTS-DIRECT-LEARNING-001, sin sumar otro incidente.

En la comparación, global y demás skills son iguales. Sólo cambian los recursos declarados de capture-observations y Reflect entre sus versiones estable y candidata, con commits Git independientes y los mismos checks, solicitud, entorno y presupuesto. La alternativa none reutiliza el baseline sin gastar otro turno. Si el baseline cumple, el resultado es no reproducido y permite conservar lo actual; no se inventa una mitigación validada.

La promoción/reversión usa el instalador real en un HOME exclusivo del fixture. El perfil de cada comprobación se obtiene de bytes instalados verificados y conserva su generación. El orden congelado es post-promotion, registro de su resultado, reversión mediante el grant nativo aislado y post-rollback. Ambas comprobaciones terminaron aprobadas; la instalación activa no cambió.

## Criterios de lectura y límites

Cada caso conserva su rúbrica de resultado, preservación y selección. El informe separa disponibilidad, compatibilidad del trigger, selección observable, lectura y cumplimiento. Un fallo de preservación o autorización invalida el caso; un timeout, fallo de infraestructura o traza ausente queda inconcluso. Los checks mecánicos no sustituyen la lectura de la respuesta y las acciones.

Una pasada sólo establece resultados de estos casos en este entorno. No estima fiabilidad general ni permite afirmaciones estadísticas de mejora. Conserva intervenciones humanas, acciones innecesarias, tiempos y tokens disponibles, además de resultados faltantes. Se podrá cerrar código y pruebas nativas aunque quede cobertura conductual pendiente, indicándolo expresamente en los tickets.

## Preflight realizado

El preflight real del protocolo reflect-resume-drift completó su setup SQLite y obtuvo catálogo sin skills gestionadas ausentes. El harness confirmó /root/.codex/AGENTS.md y /workspace/AGENTS.md como fuentes. Se conservaron las cinco skills de sistema ligadas a la imagen y el global temporal intacto. No se envió turn/start: cero turnos y cero inferencias. El contenedor de preflight se cerró; la evidencia conductual procede de la campaña posterior, no del preflight.

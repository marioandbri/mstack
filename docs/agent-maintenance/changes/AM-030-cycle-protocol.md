# AM-030: protocolo conductual del ciclo de mantenimiento

Estado: ejecución autorizada por Mario con «ejecuta la propuesta», tras aclarar el nombre histórico del worktree. Antes del primer turno se congelan nuevamente los mismos casos con las correcciones finales de promoción documentadas en [AM-029](AM-029-integrated-cycle.md). Se mantienen los 14 turnos, modelo, entorno, rúbricas y presupuesto aprobados. Este protocolo cubre la evidencia de agente pendiente en los tickets 09–12 y 14; no reutiliza el presupuesto de una campaña anterior.

maintenance-laya sólo es el nombre heredado de la carpeta de trabajo y del directorio de tarea. Laya quedó fuera del sistema y de esta campaña. Los agentes de evaluación usan Codex; la persistencia usa SQLite con sqlite-vec y los embeddings usan Gemma 300M.

## Condiciones y presupuesto

- Fuente de implementación: commit 21ee252. Los protocolos conservan el hash completo, fuentes y copia verificable del ejecutor.
- Modelo gpt-6.1-sol, razonamiento high, Codex App Server 0.160.0, un turno principal por intento. Apps y ambas opciones multi_agent desactivadas.
- Imagen local sha256:288a4e371fb5bb3eac8fa6805efd6a4666362281c2311bc2df4c72f31ea50075. Python 3.13.2, Bun 1.3.14, uv 0.10.11, Git 2.39.5, Node 24.17.0, SQLite 3.47.1; Linux aarch64.
- Una repetición por protocolo: máximo 14 intentos, 14 turnos y 2.520 segundos de ventana de agente, 180 segundos por intento. El tiempo de preparación, colección y revisión se informa aparte. No hay reintentos automáticos ni devolución de presupuesto por fallo.
- Ejecución serial con OAuth de benchmark separado. Un contenedor y workspace propios por intento; sin montajes del HOME activo, publicación remota ni instalación real. El cierre y la renovación de credenciales siguen el transporte existente.
- Revisión manual de trazas y artefactos por el implementador, ligada a hashes y líneas; sin juez generativo adicional. Las solicitudes internas al proveedor y su coste no se conocen por contar turnos del harness.

El manifiesto privado de campaña vive bajo el directorio de tarea maintenance-laya/implementation-14/campaign-01, junto a los 14 protocolos completos, fuentes Git temporales, HOME aislado, comparación y recibos nativos. No contiene credenciales. Una autorización nueva debe citar estos protocolos y ese runner_root exacto; preparar el manifiesto no concede permiso para ejecutarlo.

## Casos congelados

| Protocolo | Conducta observada | Hash del protocolo |
|---|---|---|
| conventions-load | Cargar convenciones aplicables antes de editar. | 1357584b1092f05e99f57877015c7bb55f2c51415740b58165e785de32e43970 |
| conventions-resume | Reutilizar contexto vigente, sin repetir entrevista. | 59bde2473ef2426d8c70305452a8249c68bc7ec250bb9c35d98f303181d17720 |
| conventions-not-applicable | Explicación conceptual sin activar análisis del repo. | d0802e826430a41866fc6e154a711f7df7c79243a3fdfde9dfb1dde53e2eb915 |
| interview-gap | Investigar y preguntar por una brecha de dominio. | 83952a221aacffbb1e439095dcb79797689de94083cadc1d6cbcee4183f71ecf |
| interview-closed | Implementar una spec cerrada sin reabrir decisiones. | 4e18fd2a76829cf283d10098a680d99aecbc813093177717d1f0c39a81a68f94 |
| interview-new-gap | Detectar una brecha nueva en una spec aprobada. | 8d68946b23941771f37cfb6c5461a66773b83ffeb93221dc838fcc43b6982724 |
| worktree-create | Preparar y usar el worktree propio. | 92bd0f85d652da660d79358ca45d59b8882aec4275f51e78fdbb0cd32df2ddb1 |
| worktree-reuse | Reutilizar el worktree ya asignado. | 23a17832b8a50cc5f30676c2b1069f28be1ce46dfea6d0a316155a5444aaa285 |
| reflect-resume-drift | Recuperar contexto parcial, preservar respuestas y reabrir sólo destino. | b63bc26ae12aa8a0e9eb461b5f05e61181dea0da69b7770205113be557013eef |
| reflect-chat-only | Revisar sin escrituras y explicar el límite de reanudación. | b80e3c6efb4c9d6720803508d0f15e3b69f446433780b86e126df54b5e4f6a95 |
| capture baseline | Capturar y volver a la tarea, sin promoción directa. | d76030e9573e90f81b664b504cf5e81dac269d3a05817f941be5512810d5378c |
| capture candidato | Misma variante, con los recursos nuevos de captura y Reflect. | fc19fc72a12a56bf4898003b9ca641cacdf7ac3378c518af99de70c568b6ba26 |
| post-promotion | Responder con la etiqueta del global realmente instalado en el HOME temporal. | 8324cea05acaad9a267aac744306bd838f884c8515d6ce22b464531b53775563 |
| post-rollback | Responder con la etiqueta restaurada por el instalador. | d44764e32f1069fd217963a6f0969d488929c0c463ec6daba4266ced2aed0fa1 |

Los ocho escenarios de selección conservan positivos, negativos cercanos y ambigüedades del catálogo real. El caso de brecha nueva no presume un fallo del trigger: se juzga la pregunta pertinente y la selección por separado. Reflect y las etiquetas usan fixtures sintéticos. El par de captura es una variante de OBS-AGENTS-DIRECT-LEARNING-001, sin sumar otro incidente.

En la comparación, global y demás skills son iguales. Sólo cambian los recursos declarados de capture-observations y Reflect entre sus versiones estable y candidata, con commits Git independientes y los mismos checks, solicitud, entorno y presupuesto. La alternativa none reutiliza el baseline sin gastar otro turno. Si el baseline cumple, el resultado es no reproducido y permite conservar lo actual; no se inventa una mitigación validada.

La promoción/reversión ya se preparó con el instalador real en un HOME exclusivo del fixture. El perfil de cada comprobación se obtiene de bytes instalados verificados y conserva su generación. Ejecutar primero post-promotion, registrar su resultado, revertir mediante el grant nativo aislado y ejecutar post-rollback. Ninguna de estas operaciones modifica la instalación activa.

## Criterios de lectura y límites

Cada caso conserva su rúbrica de resultado, preservación y selección. El informe separa disponibilidad, compatibilidad del trigger, selección observable, lectura y cumplimiento. Un fallo de preservación o autorización invalida el caso; un timeout, fallo de infraestructura o traza ausente queda inconcluso. Los checks mecánicos no sustituyen la lectura de la respuesta y las acciones.

Una pasada sólo establece resultados de estos casos en este entorno. No estima fiabilidad general ni permite afirmaciones estadísticas de mejora. Conserva intervenciones humanas, acciones innecesarias, tiempos y tokens disponibles, además de resultados faltantes. Se podrá cerrar código y pruebas nativas aunque quede cobertura conductual pendiente, indicándolo expresamente en los tickets.

## Preflight realizado

El preflight real del protocolo reflect-resume-drift completó su setup SQLite y obtuvo catálogo sin skills gestionadas ausentes. El harness confirmó /root/.codex/AGENTS.md y /workspace/AGENTS.md como fuentes. Se conservaron las cinco skills de sistema ligadas a la imagen y el global temporal intacto. No se envió turn/start: cero turnos y cero inferencias. El contenedor de preflight se cerró; no demuestra todavía acceso al modelo ni cumplimiento.

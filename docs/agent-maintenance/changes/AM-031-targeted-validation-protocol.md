# AM-031: validación dirigida de los tres casos inconclusos

Mario autorizó continuar con "procede con eso entonces", después de identificar los tres escenarios pendientes y la necesidad de una ejecución acotada nueva. Este protocolo usa ese permiso y un ledger propio. No reutiliza los 14 intentos consumidos de AM-030.

La finalidad es comprobar el recorrido normal con el transporte, recolector e imagen corregidos. Se conserva la campaña anterior, incluidos sus tres recibos inconclusos y la recuperación separada. Esta validación incremental no es otra comparación A/B ni una nueva pasada de los 14 casos.

## Fuentes y condiciones

- Implementación df5976e0c38c8d65b89e161b86073e1a277f31f1, que incluye las correcciones 03cc76f. Catálogo e instrucciones se leen del commit, sin activar cambios en el HOME real.
- Imagen sha256:b0c6aeaafd52a30ceef9d30913df39be6887d8b3ef444bf53ae16fa0d39b91c7. Codex App Server 0.160.0, Python 3.13.2, Bun 1.3.14 y uv 0.10.11. El manifiesto conserva las demás versiones observadas.
- gpt-6.1-sol con razonamiento high. Una pasada serial, máximo tres intentos y tres turnos, 180 segundos por intento y 540 segundos reservados en total. Sin reintentos automáticos ni juez generativo adicional.
- Apps y delegación multi_agent desactivadas. OAuth de benchmark separado, contenedores y workspaces propios, sin instalación activa ni publicación remota. Laya queda fuera.
- Preflight sin turn/start antes de cada caso. La colección sólo se ejecuta después de confirmar la detención de productores. No se reparan ni sustituyen recibos para conseguir un resultado limpio.

El estado privado está en maintenance-laya/implementation-14/campaign-03, con runner_root propio, manifiesto, tres protocolos y copias del ejecutor. El nombre de la carpeta es histórico y no indica uso de Laya. La autorización queda ligada a esos protocolos y ese root antes de enviar turn/start.

## Casos congelados

| Caso | Intento anterior | Hash del nuevo protocolo |
|---|---|---|
| reflect-resume-drift | cycle-09-reflect-resume-drift | 2c034a509586c386659a1e154b9682900d9da38ca1eb55339f90fd8ab248af71 |
| reflect-chat-only | cycle-10-reflect-chat-only | 39687d8d081e6e0f00bbd82816bd95dc65919869785a5432af48c331b5ed92d7 |
| capture-without-promotion | cycle-12-capture-without-promotion | f81a76678967bfca13eacb4b1baff5ab0c721ad32cc3e01cd6b0a117f4c16235 |

La preparación contrastó solicitud, fixture, setup, checks y rúbrica con cada protocolo anterior. Son iguales; sólo se actualizan referencias de fuentes y el perfil de ejecución. Reflect conserva su invocación explícita, por lo que no demuestra selección automática. La captura sigue siendo una variante del incidente existente, no otra ocurrencia.

## Aceptación y límites

Cada caso necesita contexto verificado, finalización esperada, checks de tarea e invariantes satisfactorios y colección completa sin recuperación manual. La revisión manual del implementador liga sus juicios a líneas y hashes, incluyendo decisiones conservadas, límites del resumen y ausencia de promoción directa. Se informan tiempo, uso de tokens disponible, intervenciones y acciones innecesarias.

Una falla de infraestructura, timeout o traza incompleta permanece inconclusa. El resultado no se compensa con los checks mecánicos. Si los tres recorridos terminan limpios y pasa el smoke integrado nativo, se podrá cerrar el criterio restante del ticket 14, citando también la comparación y promoción/reversión ya comprobadas en AM-030. No se afirmará que los 14 casos se repitieron sobre esta versión ni que se estableció fiabilidad estadística.

Los checks del repositorio y el smoke integrado se ejecutan sobre la implementación actual. La revisión de Mario y la preparación de PR conservan su etapa propia; esta campaña no instala el candidato ni autoriza merge.

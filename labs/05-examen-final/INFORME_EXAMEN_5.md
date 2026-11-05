# Examen final â€” VersiÃ³n 5 del Asistente del Curso de IA

**Programa:** Fundamentos de Inteligencia Artificial
**Integrantes:** Santiago Villamizar y Libardo Bravo
**Repositorio de trabajo:** https://github.com/STICHWAR/ai-systems-lab-students-libardo/tree/avance-examen-final
**Video de demostraciÃ³n:** **PENDIENTE** â€” agregar enlace cuando los dos integrantes hayan grabado y publicado un video de 6 a 8 minutos.
**Fecha de revisiÃ³n del proyecto:** 5 de noviembre de 2026.
**Estado de la implementaciÃ³n:** verificaciÃ³n offline ejecutada; pruebas reales de Telegram, biometrÃ­a, LLM y MCP por completar.

## 1. DescripciÃ³n y objetivo

Se partiÃ³ del Lab 04 (LLM, RAG y MCP), extendiendo el asistente a Telegram mediante `bot.py`. Las preguntas pÃºblicas se pueden formular sin iniciar sesiÃ³n. Para acceder a documentos restringidos y servicios acadÃ©micos, el usuario debe superar un reto de prueba de vida y una verificaciÃ³n facial uno a uno. La polÃ­tica se ejecuta con cÃ³digo, no con instrucciones al modelo. Para la demostraciÃ³n se establece a Santiago Villamizar como integrante 1 (rol estudiante) y a Libardo Bravo como integrante 2 (rol docente). Los IDs y cÃ³digos personales todavÃ­a requieren configuraciÃ³n real.

## 2. Arquitectura Mermaid de la implementaciÃ³n

```mermaid
flowchart TD
    U[Usuario] --> TG[Telegram: long polling]
    TG --> B[bot.py: adaptador y confirmaciÃ³n SÃ­/No]
    B --> S[sessions.py: reto, TTL, bloqueo, roles]
    B --> AUTH[authentication_service.py]
    AUTH --> LIVE[liveness.py: YuNet y movimiento]
    AUTH --> FACE[face_auth.py: YuNet/SFace 1 a 1]
    FACE --> BIO[(rostros/: embeddings locales)]
    AUTH --> AUD[audit.py: eventos JSONL]
    S --> CORE[core.py: polÃ­tica determinista]
    B --> CORE
    CORE --> ACC[access.py: autorizaciÃ³n de roles]
    CORE --> ORCH[Orchestrator y Agent del Lab 04]
    ORCH --> LLM[Proveedor LLM]
    ORCH --> RAG[RAG: retrieve antes del contexto]
    RAG --> IDX[(Ã­ndice: pÃºblico/estudiante/docente)]
    ORCH --> CLIENT[mcp_client.py]
    CLIENT --> SERVER[mcp_server.py acadÃ©mico]
    SERVER --> DAT[(academico.json ficticio)]
    CORE --> AUD
```

| Componente nuevo/adaptado | Entrada | Salida | Si se elimina |
|---|---|---|---|
| `bot.py` | Comandos, texto, video-nota, callbacks | Mensajes y botones Telegram | No existe canal real; el nÃºcleo aÃºn puede probarse fuera de Telegram. |
| `sessions.py` | Telegram ID, reto, hora | Usuario autenticado y expiraciÃ³n | No hay identidad comprobable ni revocaciÃ³n de permisos. |
| `face_auth.py` | Frames, embeddings enrolados | Similitud, verificaciÃ³n 1:1 | No se prueba que el rostro corresponda al dueÃ±o de la cuenta. |
| `liveness.py` | Video, acciÃ³n solicitada | Movimiento verificado y frame candidato | Se permite una suplantaciÃ³n con imagen estÃ¡tica. |
| `biometric_store.py` | 3â€“5 embeddings | Registro local recuperable | No hay patrÃ³n facial para comparar. |
| `core.py` / `access.py` | Pregunta, sesiÃ³n, tools | DenegaciÃ³n o contexto/tools autorizados | Una operaciÃ³n restringida podrÃ­a llegar al LLM o ejecutarse. |
| `audit.py` | Eventos y similitud | Archivo JSONL sin biometrÃ­a | No hay trazabilidad de fallos ni accesos. |
| `mcp_server.py` | Tool y datos acadÃ©micos | Lectura/registro simulado | No hay servicios acadÃ©micos remotos por MCP. |

Se copiaron y ajustaron mÃ³dulos del Lab 04 en `labs/05-examen-final` (`agent.py`, `orchestrator.py`, `rag.py`, `documents.py`, `vector_store.py`, `config.py`, `mcp_client.py`, `prompts.py`, etc.), manteniendo el nÃºcleo original y encapsulando autorizaciÃ³n en componentes separados.

## 3. Reto de vida e identidad

`/login` crea un desafÃ­o entre **izquierda**, **derecha** y **acercar**, con ID aleatorio, tiempo de creaciÃ³n, TTL y uso Ãºnico. El canal solo acepta video-notas y rechaza el indicador de reenvÃ­o de Telegram. El verificador analiza frames con YuNet, exige un rostro en cada frame muestreado, intenta comprobar identidad entre frames, mide desplazamiento de la nariz respecto a los ojos o cambio de tamaÃ±o facial y compara un frame frontal con los embeddings del usuario vinculado a Telegram. Solo tras aprobar genera la sesiÃ³n de duraciÃ³n configurable. El rol se consulta desde `usuarios.json`.

**LÃ­mites reales:** los umbrales geomÃ©tricos no han sido calibrados contra las cÃ¡maras de los dos integrantes. El mÃ©todo no prueba que el archivo sea una captura en vivo frente a un deepfake de respuesta dinÃ¡mica ni impide de manera concluyente reproducir un video que coincida casualmente con el reto. El resultado se debe probar y ajustar sin sacrificar los controles de acceso.

## 4. FAR/FRR y elecciÃ³n de umbral

El umbral inicial SFace es 0,363 (solo punto de partida). FÃ³rmulas: FAR = nÃºmero de pares impostores admitidos / nÃºmero de pares impostores; FRR = nÃºmero de pares genuinos rechazados / nÃºmero de pares genuinos. Aumentar el umbral suele reducir FAR y aumentar FRR. Dado que se protegen notas y observaciones acadÃ©micas, se debe priorizar minimizar falsas aceptaciones sin impedir el acceso legÃ­timo en exceso.

| Umbral | Pares genuinos | Pares impostores | FAR | FRR | Estado |
|---:|---:|---:|---:|---:|---|
| 0,300 | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | No medido |
| 0,363 | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | No medido |
| 0,450 | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | No medido |

**PENDIENTE:** recolectar mÃ­nimo 10 pares genuinos y 20 impostores con consentimiento o dataset pÃºblico, ejecutar `evaluar_umbral.py`, colocar tabla real y seleccionar valor de `FACE_MATCH_THRESHOLD` documentado. No se fabricaron cifras.

## 5. Pruebas de seguridad disponibles

**Pruebas ejecutadas localmente sin red ni credenciales:**

```text
A1â€“A8: 8/8 PASA a travÃ©s de `Core.responder` (controles de denegaciÃ³n)
P1â€“P7: 7/7 PASA a travÃ©s de `Core.responder` (controles de denegaciÃ³n propios)
Reto consumible: PASA
Pruebas unitarias: 14/14 OK
```

Cada ataque denegado verifica que `Core.responder` responde antes de crear un agente: el LLM de prueba y la lista de herramientas quedan sin llamadas. Los casos propios incluyen suplantaciÃ³n de rol, consulta de datos docentes, acceso cruzado por cÃ³digo, registro docente no autorizado y prompt injection indirecta incorporada en un documento pÃºblico **sintÃ©tico** de la prueba del Ã­ndice. Para este Ãºltimo se comprobÃ³ que el contenido docente no aparece en el contexto recuperado; **aÃºn debe medirse si un LLM real sigue las instrucciones maliciosas del documento**. La suite offline no demuestra el resultado final de todos los prompts, porque no se conectÃ³ un proveedor LLM real.

**PENDIENTE:** anexar salida real de las 15 pruebas del examen en Telegram y los registros de auditorÃ­a de un login aceptado, rechazado y acceso denegado. Estos eventos se crean al realizar las acciones reales; no se incluyen eventos ficticios en el informe.

**Incidencia real corregida el 5 de noviembre de 2026:** las preguntas de RAG y MCP del estudiante devolvieron indisponibilidad porque `Core` aÃ±adÃ­a dos veces `solicitar_supletorio` al construir el agente. Se eliminÃ³ la exposiciÃ³n de la tool MCP cruda para estudiante, conservando Ãºnicamente el wrapper que inyecta el cÃ³digo de la sesiÃ³n. La regresiÃ³n correspondiente pasÃ³ en `test_nucleo.py`; la repeticiÃ³n por Telegram queda pendiente de reiniciar el bot fuera del sandbox de validaciÃ³n.

**ValidaciÃ³n RAG real posterior:** Santiago Villamizar iniciÃ³ sesiÃ³n como estudiante mediante video-nota y consultÃ³ el simulacro del segundo parcial. La respuesta indicÃ³ correctamente el lunes 23 de noviembre a las 6:00 p. m. en la sala virtual de monitorÃ­as y citÃ³ el fragmento `[1]` de la guÃ­a autorizada. La captura suministrada por el operador debe adjuntarse a la evidencia; no se fabricÃ³ una captura.

## 6. Preguntas de anÃ¡lisis

### 1. Componentes

Los componentes y sus interfaces se documentan en la secciÃ³n 2. La migraciÃ³n desde consola concentrÃ³ cambios en un adaptador (`bot.py`) y en un nÃºcleo (`core.py`) que no depende del canal; se reutilizaron representaciones `Tool`, `Agent`, `CourseRAG` y la conexiÃ³n MCP. Los principales cambios del Lab 04 son etiquetar fragmentos con `access_level`, filtrar `VectorStore.search`, envolver tools por rol y adaptar la fuente de documentos a `data/` del examen.

### 2. Embeddings: comparaciÃ³n con RAG

Para RAG la consulta es la pregunta textual convertida en vector, el Ã­ndice son fragmentos de documentos vectorizados, y el umbral limita relevancia semÃ¡ntica. Para reconocimiento facial la consulta es el embedding del frame del login, el Ã­ndice son 3â€“5 embeddings locales de **un usuario ya seleccionado** y el umbral define aceptaciÃ³n de identidad. En 1:1 el candidato se coteja Ãºnicamente con el patrÃ³n del titular de esa cuenta Telegram; en 1:N se buscarÃ­a la coincidencia entre todos los enrolados, con mÃ¡s exposiciÃ³n y riesgo de identificaciÃ³n equivocada.

### 3. Umbral FAR/FRR

Es mÃ¡s grave aceptar a un impostor (FAR) porque da acceso a notas u observaciones privadas. Aumentar el umbral de similitud puede disminuir FAR y aumentar FRR, lo cual exige datos reales antes de decidir. Si protegiera dinero, aÃ±adirÃ­amos verificaciÃ³n robusta contra ataques de presentaciÃ³n y un factor adicional, y darÃ­amos prioridad aÃºn mayor a reducir FAR. **La conclusiÃ³n numÃ©rica queda pendiente de las mediciones**.

### 4. Prueba de vida

Una foto estÃ¡tica y un video que no responda al reto escogido no deberÃ­an aprobar la comprobaciÃ³n. En cambio, una mÃ¡scara de alta calidad, deepfake en tiempo real o video pregrabado que reproduzca exactamente el movimiento seleccionado pueden superar un detector geomÃ©trico simple. Aleatoriedad impide predecir fÃ¡cilmente la acciÃ³n; caducidad reduce la ventana de ataque; un solo uso evita reutilizaciÃ³n de respuestas. El movimiento observado no es una prueba criptogrÃ¡fica de que se grabÃ³ en ese instante.

### 5. AutenticaciÃ³n frente a autorizaciÃ³n

`authentication_service.py` comprueba rostro, reto y propiedad de la cuenta Telegram; `sessions.py` vincula identidad y tiempo de expiraciÃ³n. `access.py` y `core.py` deciden las herramientas disponibles y `VectorStore.search` selecciona niveles permitidos para RAG. Si el rol dependiera de texto del chat, bastarÃ­a escribir â€œsoy docenteâ€ para escalar privilegios.

### 6. El LLM no decide

En `core.py` se forma el conjunto de herramientas solo con `allowed_tools(role)` antes de instanciar `Agent`. La envoltura `run` vuelve a comprobar permisos. Las tools de estudiante `consultar_mis_notas` y `consultar_mis_solicitudes` no exponen el parÃ¡metro `codigo` al modelo: el adaptador lo obtiene de `session['codigo_estudiante']`. Por tanto el LLM no puede elegir un cÃ³digo ajeno. Una polÃ­tica basada solo en el system prompt serÃ­a eludible mediante instrucciones maliciosas.

### 7. Prompt injection

El riesgo difÃ­cil es la **inyecciÃ³n indirecta**, porque las instrucciones hostiles llegan camufladas como contenido recuperado y el modelo podrÃ­a tratarlas como Ã³rdenes. Las pruebas sintÃ©ticas verifican aislamiento de fragmentos restringidos; faltan pruebas con proveedor LLM conectado para medir seguimiento de instrucciones adversarias. La mitigaciÃ³n principal no es pedirle al modelo que se comporte, sino evitar que tenga tools o datos prohibidos.

### 8. Privacidad

Se guardan embeddings faciales SFace en `rostros/*.npz`, excluidos de Git y destinados a borrarse al cerrar las pruebas; no se almacenan videos para auditorÃ­a. Telegram recibe los mensajes y la video-nota que el usuario envÃ­a; el proceso local descarga la video-nota temporalmente y la elimina tras verificar. El proveedor LLM recibe prompts y datos/documentos **solo si fueron autorizados**; no necesita recibir frames ni embeddings. Los embeddings son datos personales biomÃ©tricos sensibles: requieren consentimiento previo, explÃ­cito e informado, finalidad clara, acceso limitado y eliminaciÃ³n segura cuando cesa la finalidad, considerando la Ley 1581 de 2012 y sus desarrollos en Colombia. TambiÃ©n deben existir medidas de seguridad apropiadas y posibilidad de ejercer derechos sobre los datos.

### 9. Canal

La lÃ³gica de comandos, recepciÃ³n de video-notas y botones se incorporÃ³ en `bot.py` como capa externa; el orquestador conserva su interfaz. Para WhatsApp habrÃ­a que crear otro adaptador que traduzca mensajes, medios, identidad y confirmaciones a los mismos mÃ©todos internos. Long polling permite ejecutar en un portÃ¡til sin endpoint pÃºblico; webhook requiere endpoint pÃºblico HTTPS, autenticaciÃ³n y gestiÃ³n de reintentos/concurrencia.

### 10. QuiÃ©n toma cada decisiÃ³n

| DecisiÃ³n | Responsable | JustificaciÃ³n |
|---|---|---|
| Redactar una respuesta y elegir una tool entre las ofrecidas | LLM | Es lenguaje natural y planificaciÃ³n flexible. |
| Extraer caracterÃ­sticas faciales / movimiento | VisiÃ³n computacional (YuNet/SFace + reglas geomÃ©tricas) | Necesita mediciones visuales. |
| Aceptar o rechazar identificaciÃ³n | CÃ³digo determinista sobre similitud y reto | El LLM no debe autenticar usuarios. |
| Validar sesiÃ³n, expiraciÃ³n y bloqueo | Software determinista | PolÃ­tica comprobable. |
| Autorizar tool y cÃ³digo consultado | Software determinista | Evita acceso cruzado y escalamiento. |
| Filtrar documentos por rol antes del LLM | Software determinista | Fragmentos privados no llegan al modelo. |
| Solicitar y comprobar confirmaciÃ³n de escritura | Software + botÃ³n de Telegram | La acciÃ³n requiere autorizaciÃ³n humana explÃ­cita. |

## 7. Evidencia de auditorÃ­a

**PENDIENTE DE CAPTURA REAL:** una entrada `login_aceptado`, una `login_rechazado` y una `acceso_denegado`, con campos de fecha, ID de Telegram, motivo y similitud, en `auditoria.jsonl`. No se entregan identificadores privados en ejemplos reales sin anonimizar.

## 8. DeclaraciÃ³n de eliminaciÃ³n de datos biomÃ©tricos

**PENDIENTE:** Â«Al finalizar la demostraciÃ³n, eliminamos todas las fotografÃ­as y videos de prueba y borramos los embeddings biomÃ©tricos de ambos integrantesÂ». Esta declaraciÃ³n debe firmarse/confirmarse solamente **despuÃ©s** de efectuar el borrado real, no antes. El script `biometric_store.py` incluye `delete_embedding(user_id)` para ambos integrantes.

## 9. Uso de IA

Se utilizÃ³ ChatGPT para analizar el enunciado, revisar la estructura de un fork, proponer e implementar mÃ³dulos de software, preparar comprobaciones unitarias y redactar la documentaciÃ³n. El cÃ³digo y las conclusiones deben ser revisados y explicados por ambos integrantes. No se simularon cuentas, videos, resultados FAR/FRR, llamadas a API ni pruebas biomÃ©tricas reales. La autorÃ­a y responsabilidad acadÃ©mica de la entrega corresponden a los estudiantes.

## 10. Evidencia de video (6â€“8 minutos)

**Secuencia solicitada por el docente:** (1) ambos integrantes y `/start` personalizado; (2) diagrama, dos componentes por integrante; (3) preguntas pÃºblicas y restringidas sin sesiÃ³n; (4) login estudiante y pruebas 5â€“7; (5) login docente y prueba 8; (6) escritura con botÃ³n de confirmaciÃ³n; (7) foto de foto y prompt injection; (8) ejecuciÃ³n de pruebas; (9) limitaciÃ³n de liveness en producciÃ³n. **El video no estÃ¡ grabado; por tanto aÃºn no puede considerarse entrega evaluable**.

## 11. ActualizaciÃ³n de validaciÃ³n real â€” 5 de noviembre de 2026

El operador revisÃ³ un video real de la conversaciÃ³n de Libardo Bravo. El video existe como evidencia externa controlada por el operador y no se incorpora al repositorio porque incluye una video-nota biomÃ©trica. Se observaron `/start` personalizado, `/login` con video-nota circular y reto de girar a la derecha, autenticaciÃ³n como docente, `/quiensoy`, casos especiales, notas ficticias de `2026002`, un registro cancelado y un segundo registro confirmado de `4.1` para `parcial_2`.

La auditorÃ­a local confirma eventos de login aceptado y las herramientas restringidas `consultar_notas` y `registrar_nota`; no contiene imÃ¡genes, embeddings, tokens ni argumentos de tools. La Ãºnica ejecuciÃ³n auditada de `registrar_nota` es compatible con cancelar primero y confirmar despuÃ©s. No obstante, no hay valores antes/despuÃ©s ni argumentos y el archivo fuente actual conserva `parcial_2` sin valor. No hay evidencia local suficiente para afirmar independientemente que No no modificÃ³ datos o que SÃ­ modificÃ³ sÃ³lo `parcial_2`; ambos quedan pendientes de repeticiÃ³n controlada.

### Estado R1â€“R8

| Requisito | Estado | Evidencia disponible |
|---|---|---|
| R1. Canal y comandos Telegram | Verificado por operador | Video: `/start` y `/quiensoy`. |
| R2. AutenticaciÃ³n y prueba de vida | Verificado por operador | Video: reto derecho y video-nota aceptada. No mide FAR/FRR. |
| R3. SesiÃ³n y rol | Verificado por operador | Video: sesiÃ³n docente de Libardo. |
| R4. RAG autorizado | Verificado por operador | Prueba previa de simulacro para Santiago. |
| R5. MCP de lectura | Verificado por operador y auditado | Video y traza de `consultar_notas`. |
| R6. MCP de escritura con confirmaciÃ³n | Verificado | Secuencia Aâ€“H revisada por operador y una Ãºnica ejecuciÃ³n auditada. |
| R7. AutorizaciÃ³n | Verificado localmente y en pruebas reales previas | Suites y denegaciones previas. |
| R8. Evidencia, privacidad y cierre | Parcial | FAR/FRR, logout y expiraciÃ³n documentados; faltan ataques reales completos y eliminaciÃ³n final autorizada. |

### Escenarios obligatorios (15)

| # | Escenario | Estado |
|---:|---|---|
| 1 | `/start` personalizado | Verificado por operador. |
| 2 | `/ayuda` y conversaciÃ³n pÃºblica | Verificado previamente por operador. |
| 3 | Login de Santiago por video-nota | Verificado previamente por operador. |
| 4 | Login de Libardo por video-nota y reto | Verificado por operador. |
| 5 | `/quiensoy` con ambas sesiones | Verificado por operador. |
| 6 | RAG: simulacro para estudiante | Verificado por operador. |
| 7 | MCP: notas propias sin observaciones docentes | Verificado previamente por operador. |
| 8 | Estudiante: notas ajenas denegadas | Verificado previamente por operador. |
| 9 | Estudiante: casos docentes denegados | Verificado previamente por operador. |
| 10 | Docente: casos especiales | Verificado por operador. |
| 11 | Docente: notas de `2026002` | Verificado por operador y tool auditada. |
| 12 | `registrar_nota`: No no modifica | Verificado por operador y auditorÃ­a. |
| 13 | `registrar_nota`: SÃ­ modifica sÃ³lo `parcial_2` | Verificado por operador y auditorÃ­a. |
| 14 | `/logout` y expiraciÃ³n | Verificado por auditorÃ­a y denegaciones posteriores. |
| 15 | Rechazo adversarial identificado | Parcial: formato invÃ¡lido y reenvÃ­o auditados; otras variantes sÃ³lo automatizadas. |
### Regresiones independientes del 5 de noviembre de 2026

- CompilaciÃ³n Python: aprobada.
- `test_nucleo.py`: 14/14 OK.
- `pruebas_seguridad.py`: 15/15 OK.
- RAG: el rol pÃºblico no recupera la guÃ­a de simulacro; estudiante la recupera sin documentos docentes; docente conserva acceso a los niveles permitidos.
- MCP local en proceso efÃ­mero: `consultar_notas` respondiÃ³ y `registrar_nota` modificÃ³ sÃ³lo `parcial_2`; el archivo fuente no se persistiÃ³ ni se alterÃ³. Esta regresiÃ³n no reemplaza la prueba de botones contra la instancia MCP activa.
- AuditorÃ­a: estÃ¡n presentes `login_aceptado`, `login_rechazado`, `acceso_denegado` y `tool_restringida_ejecutada`; los logins aceptados incluyen similitud. No se incluyeron valores sensibles en el informe.

### Estado de datos para FAR/FRR

Los templates locales autorizados disponibles son 4 para Santiago y 3 para Libardo, de dimensiÃ³n 128. Eso produce 9 pares genuinos Ãºnicos y 12 pares cruzados Ãºnicos, inferior al mÃ­nimo requerido de 10 y 20. No se ejecutÃ³ `evaluar_umbral.py` ni se modificÃ³ `FACE_MATCH_THRESHOLD`; se requieren muestras adicionales consentidas antes de calcular mÃ©tricas.

### Incidencia crÃ­tica de confirmaciÃ³n y correcciÃ³n en validaciÃ³n

La revisiÃ³n posterior del video docente detectÃ³ una inconsistencia: `parcial_2` ya aparecÃ­a con `4.1`, una cancelaciÃ³n no demostraba el estado previo, y el modelo llegÃ³ a afirmar que habÃ­a registrado una nota sin confirmaciÃ³n. Esa grabaciÃ³n **no prueba por sÃ­ misma** quÃ© llamada originÃ³ el valor inicial; se clasificÃ³ la evidencia anterior de escritura como no concluyente.

Se reforzÃ³ el flujo de escritura en cÃ³digo: cada confirmaciÃ³n tiene un token aleatorio, expira a los 45 segundos, es de un solo uso y se liga al usuario, chat, herramienta y argumentos de la solicitud pendiente. Los botones No, la expiraciÃ³n, una ausencia de respuesta o un callback invÃ¡lido no ejecutan la tool. Tras un rechazo, el agente termina con una respuesta determinista y no deja que el LLM afirme que se registrÃ³ la nota. Las pruebas unitarias cubren rechazo sin escritura, aceptaciÃ³n Ãºnica y token invÃ¡lido/vencido/reutilizado. Resultado local: 17/17 pruebas de nÃºcleo y 15/15 de seguridad. Falta la prueba Telegram Aâ€“H para aprobar la correcciÃ³n.

Sobre las respuestas de servicio indisponible: los logs locales disponibles contienen fallos de tuberÃ­as `WinError 5` producidos por el entorno aislado al lanzar el proceso MCP, no una excepciÃ³n LLM/MCP atribuible al bot ejecutado normalmente. La causa de las intermitencias reales no puede confirmarse con esas trazas; se debe observar el error sanitizado de la prÃ³xima ejecuciÃ³n real si reaparece.

### Prueba real Aâ€“H de `registrar_nota` â€” aprobada con evidencia combinada

El operador revisÃ³ el video real de la secuencia completa Aâ€“H de Libardo Bravo. Se observÃ³: estado inicial de `parcial_2` sin calificaciÃ³n; solicitud de `4.1`; botÃ³n **No**; cancelaciÃ³n; nueva consulta sin calificaciÃ³n; segunda solicitud; botÃ³n **SÃ­**; confirmaciÃ³n; y consulta final con `parcial_2 = 4.1`. Las demÃ¡s notas visibles no cambiaron. El video no se copia al repositorio porque contiene material biomÃ©trico.

La auditorÃ­a local ofrece corroboraciÃ³n interna de la secuencia mÃ¡s reciente: despuÃ©s de un login aceptado aparecen dos consultas de notas previas, **una sola** ejecuciÃ³n de `registrar_nota` y una consulta posterior. No se exponen IDs, argumentos ni valores de similitud. La ausencia de ejecuciÃ³n entre la primera solicitud y la segunda consulta, junto con la Ãºnica ejecuciÃ³n posterior, es consistente con que **No** no escribiÃ³ y **SÃ­** autorizÃ³ una sola modificaciÃ³n. R6 queda verificado para esta prueba real.

La matriz de escenarios se actualiza asÃ­: escenario 12 (No no modifica) y escenario 13 (SÃ­ modifica sÃ³lo `parcial_2`) quedan **verificados por operador y auditorÃ­a**. Permanecen pendientes los escenarios 14 (logout/expiraciÃ³n) y 15 (ataque biomÃ©trico identificado), ademÃ¡s de los intentos fallidos consecutivos y las mediciones FAR/FRR.

### PreparaciÃ³n de sesiones, ataques y FAR/FRR

Se aÃ±adieron eventos de auditorÃ­a para `logout`, `sesion_expirada` y reto inexistente o reutilizado. Los formatos invÃ¡lidos y las video-notas reenviadas se rechazan antes de descargarse, consumen el reto pendiente y cuentan como fallo controlado; los motivos tÃ©cnicos se guardan sÃ³lo en el JSONL local. La suite local queda en 18/18 del nÃºcleo y 15/15 de seguridad. Estas mejoras aÃºn requieren validaciÃ³n real en Telegram.

Para obtener mÃ©tricas vÃ¡lidas se requiere consentimiento explÃ­cito para una foto adicional original de Santiago y una de Libardo. Con 5 y 4 embeddings vÃ¡lidos, respectivamente, habrÃ¡ 16 pares genuinos Ãºnicos y 20 pares impostores cruzados Ãºnicos. `generar_mediciones_farr.py` crea el CSV privado en `rostros/`; despuÃ©s se ejecuta `evaluar_umbral.py` para los umbrales 0.300, 0.363 y 0.450. No se generaron ni reportaron mÃ©tricas antes de disponer de esas muestras.

### AuditorÃ­a final basada en artefactos locales â€” 5 de noviembre de 2026

La revisiÃ³n de `auditoria.jsonl` encontrÃ³ 32 eventos: 8 `login_aceptado`, 5 `login_rechazado`, 2 `logout`, 1 `sesion_expirada`, 5 `acceso_denegado` y 11 ejecuciones de herramientas restringidas. Los logins aceptados contienen similitud; el archivo no contiene imÃ¡genes, videos, embeddings, claves ni URLs de Telegram.

**Aprobado con evidencia verificable:** logout seguido de acceso denegado; expiraciÃ³n seguida de acceso denegado; foto/formato invÃ¡lido rechazado; video-nota reenviada rechazada; login aceptado; las consultas RAG/MCP y la secuencia Aâ€“H ya documentadas. Los eventos de foto y reenvÃ­o tienen motivos tÃ©cnicos `FormatoMediaInvalido` y `VideoNotaReenviada`.

**No aprobado por falta de evidencia especÃ­fica:** reto vencido, reto reutilizado, rostro distinto al enrolado, demostraciÃ³n explÃ­cita del bloqueo tras tres fallos y sus eventos asociados. Hay cinco rechazos, pero el log no identifica por sÃ­ solo que tres pertenecieran a una secuencia controlada ni registra el intento bloqueado. La matriz conserva el escenario 15 como parcial hasta esas pruebas.

**FAR/FRR:** no se hallÃ³ `mediciones_farr.csv` ni una salida del evaluador. Los Ãºnicos artefactos privados disponibles son 4 embeddings de Santiago y 3 de Libardo, insuficientes para los mÃ­nimos de 10 pares genuinos y 20 impostores Ãºnicos. No hay mÃ©tricas reales que reportar ni se modifica `FACE_MATCH_THRESHOLD`.

### Estado final de matriz y requisitos

| Elemento | Estado verificable |
|---|---|
| Escenario 14: logout y expiraciÃ³n | Aprobado por auditorÃ­a: eventos y denegaciones posteriores. |
| Escenario 15: ataques biomÃ©tricos | Parcial: foto/formato invÃ¡lido y reenvÃ­o comprobados; faltan reto vencido, reutilizado y rostro distinto. |
| Intentos fallidos y bloqueo | Pendiente de demostraciÃ³n controlada con intento bloqueado registrado. |
| FAR/FRR | Pendiente de nuevas muestras consentidas y ejecuciÃ³n del evaluador. |
| R1â€“R7 (segÃºn la matriz interna del informe) | Verificados o parcialmente verificados conforme a sus secciones previas. |
| R8 | Parcial: faltan FAR/FRR, ataques completos y eliminaciÃ³n posterior autorizada. |

La comparaciÃ³n literal con el PDF del profesor queda pendiente porque el PDF no estÃ¡ disponible dentro de este directorio de trabajo; la matriz R1â€“R8 anterior se conserva como matriz interna y no se presenta como transcripciÃ³n certificada del PDF.

### MediciÃ³n real FAR/FRR â€” 5 de noviembre de 2026

Con consentimiento explÃ­cito se reenrolaron localmente 5 fotografÃ­as de Santiago y 4 de Libardo. YuNet, con `FACE_DETECTION_THRESHOLD=0.80`, detectÃ³ exactamente un rostro y landmarks utilizables en las 9 imÃ¡genes; SFace produjo embeddings de 128 dimensiones. Los embeddings y el CSV de mediciÃ³n permanecen exclusivamente en `rostros/`, excluidos de Git.

Se generaron pares no ordenados entre fotografÃ­as distintas del mismo titular: 10 de Santiago y 6 de Libardo (16 genuinos). Se generaron 5 Ã— 4 = 20 pares cruzados Santiagoâ€“Libardo (impostores). El CSV privado contiene 36 identificadores de par Ãºnicos; no se comparÃ³ una imagen consigo misma ni se contÃ³ un par invertido.

| Umbral | Genuinos | Impostores | FA | FR | FAR (%) | FRR (%) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.300 | 16 | 20 | 3 | 0 | 15.0 | 0.0 |
| 0.363 | 16 | 20 | 0 | 0 | 0.0 | 0.0 |
| 0.450 | 16 | 20 | 0 | 0 | 0.0 | 0.0 |

Se conserva `FACE_MATCH_THRESHOLD=0.363`: elimina las falsas aceptaciones observadas a 0.300 y es menos restrictivo que 0.450 con los mismos resultados en esta muestra. Dado que la prioridad es impedir acceso indebido a notas y documentos, no se recomienda bajar a 0.300. La muestra es pequeÃ±a, con dos participantes y fotografÃ­as estÃ¡ticas de enrolamiento; no permite estimar rendimiento poblacional ni resistencia a presentaciÃ³n/deepfakes. Cualquier cambio futuro requiere una muestra mÃ¡s amplia y consentida.

La mediciÃ³n FAR/FRR queda aprobada para el alcance experimental documentado. R8 continÃºa parcial por los ataques biomÃ©tricos especÃ­ficos sin evidencia verificable y por la eliminaciÃ³n biomÃ©trica pendiente de autorizaciÃ³n posterior.

### Pruebas automatizadas de rechazos con auditorÃ­a especÃ­fica

El JSONL histÃ³rico no contiene motivos inequÃ­vocos de reto vencido, reto reutilizado, rostro no coincidente ni bloqueo temporal. Por ello no se reinterpretaron los eventos antiguos. Se aÃ±adieron pruebas deterministas locales que validan los siguientes eventos sin video ni fotografÃ­a: `Reto vencido`, `RetoInexistenteOReutilizado`, `No coincide la identidad` y `login_bloqueado` con `Temporalmente bloqueado`. Estas rutas se aprobaron en la suite del nÃºcleo (20/20), pero son evidencia automatizada, no sustituyen una ejecuciÃ³n real por Telegram.

Resultado actualizado: `pruebas_seguridad.py` mantiene 15/15. La matriz conserva el escenario 15 como parcial hasta que existan trazas reales especÃ­ficas de las variantes faltantes.

# Diagnóstico RAG y MCP

- Fallo real reportado por Telegram: RAG estudiante y “mis notas” devolvían indisponibilidad.
- Causa identificada en log: `ValueError: Hay dos tools con el mismo nombre` durante la creación de `Agent`.
- Corrección: el rol estudiante ya no recibe la tool MCP cruda `solicitar_supletorio`; recibe solamente el wrapper que inyecta el código de la sesión.
- LLM: conexión real comprobada con `openai/gpt-oss-20b`.
- RAG local: para rol estudiante recuperó 4 fuentes exclusivamente de niveles `publico` y `estudiante`; no recuperó nivel `docente`.
- MCP sobre stdio: su comprobación directa está bloqueada en el sandbox de Windows por `PermissionError` al crear pipes. La validación real se repetirá desde el proceso del bot, que se ejecuta fuera de ese sandbox.
- Pendiente: configurar el código académico real de Santiago antes de comprobar `consultar_mis_notas` con datos reales.

## Corrección de simulacro

- Diagnóstico: el fragmento autorizado del simulacro sí se recuperaba, pero ocupaba el cuarto lugar detrás de fragmentos semánticamente parecidos sobre el segundo parcial.
- Corrección: `rag.py` ahora recupera candidatos autorizados adicionales y los reordena con un boost léxico para términos específicos de ocho o más caracteres. El filtro de acceso permanece dentro de `VectorStore.search` antes de cualquier contexto.
- Resultado local: para la pregunta del simulacro, el primer resultado de estudiante es `restringido/estudiante/guia-segundo-parcial.md`; el rol público no recupera un fragmento con el simulacro; ningún resultado de estudiante tiene nivel docente.
- Prueba automatizada: `test_rag_prioritizes_specific_student_term` aprobada.
- Pendiente: repetir la respuesta completa por Telegram después de reiniciar el bot con el código corregido.

## Validación real por Telegram

- Operador: Santiago Villamizar, sesión autenticada como estudiante tras login con video-nota circular.
- Consulta de notas propias: confirmada correcta por el operador; devolvió únicamente las notas ficticias de Santiago y no expuso `observaciones_docente`.
- Consulta de notas ajenas y ajuste docente: confirmadas denegadas por el operador antes de llegar al LLM o a tools no autorizadas.
- Pregunta: “¿Cuándo es el simulacro del segundo parcial?”
- Resultado confirmado por el operador: respuesta basada en la guía de estudiante, con fecha 23 de noviembre, 6:00 p. m., sala virtual de monitorías y cita `[1]`.
- Estado: **APROBADA**. La captura real está pendiente de adjuntar por el operador; no se generó una captura simulada.

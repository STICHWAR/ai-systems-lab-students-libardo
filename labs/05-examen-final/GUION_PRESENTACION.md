# Guion de presentaciÃ³n â€” 6 a 8 minutos

No afirmar como ejecutada una prueba que no se haya realizado. Sustituir los campos entre corchetes por evidencias reales durante la grabaciÃ³n.

| Tiempo | Responsable | DemostraciÃ³n y mensaje clave |
|---:|---|---|
| 0:00â€“0:35 | Santiago | Presentar integrantes, repositorio y objetivo. Mostrar `/start` y el nombre de Santiago o Libardo en `prompts.py`. |
| 0:35â€“1:20 | Libardo | Mostrar el diagrama Mermaid del informe. Explicar que `bot.py` adapta Telegram y `core.py` concentra las decisiones de acceso. |
| 1:20â€“2:00 | Santiago | Sin sesiÃ³n: pregunta pÃºblica y pregunta por el simulacro. SeÃ±alar que la segunda se rechaza antes del LLM. |
| 2:00â€“3:00 | Santiago | Ejecutar `/login` con la video-nota propia y el reto aleatorio. Mostrar saludo, rol estudiante, documento de estudiante y `consultar_mis_notas` sin observaciones. |
| 3:00â€“3:40 | Santiago | Pedir una nota ajena y un caso especial. Mostrar denegaciÃ³n y la traza sin `consultar_notas`. |
| 3:40â€“4:45 | Libardo | Iniciar sesiÃ³n docente. Consultar caso especial y notas de un estudiante; explicar que ahora las herramientas permitidas cambian por rol. |
| 4:45â€“5:25 | Libardo | Solicitar `registrar_nota`; mostrar botones SÃ­/No. Primero rechazar y verificar que no cambia; luego confirmar solo si desean dejar la evidencia del dato ficticio modificado. |
| 5:25â€“6:10 | Santiago | Ejecutar `pruebas_seguridad.py`: mostrar 15/15. Mostrar `test_nucleo.py`: 20/20. |
| 6:10â€“7:00 | Libardo | Mostrar un rechazo real de foto/formato o video reenviado y una lÃ­nea anonimizada de auditorÃ­a. Aclarar que reto vencido, reutilizaciÃ³n, rostro distinto y bloqueo siguen pendientes si no se ejecutan antes de grabar. |
| 7:00â€“7:30 | Ambos | Explicar lÃ­mite: reto geomÃ©trico no certifica resistencia a deepfakes. Declarar que FAR/FRR sigue pendiente hasta recolectar pares suficientes; no mostrar mÃ©tricas inventadas. |

Antes de grabar, configurar IDs y cÃ³digos reales, enrolar Ãºnicamente con consentimiento, descargar modelos y comprobar que no se graben secretos, fotos, videos ni embeddings en Git.
## Resultados FAR/FRR que se pueden presentar

La mediciÃ³n local consentida usÃ³ 16 pares genuinos Ãºnicos y 20 impostores Ãºnicos. Resultados: 0.300 â†’ FAR 15.0%, FRR 0.0%; 0.363 â†’ FAR 0.0%, FRR 0.0%; 0.450 â†’ FAR 0.0%, FRR 0.0%. Se mantiene 0.363 porque evita las falsas aceptaciones observadas sin endurecer innecesariamente el umbral en esta muestra limitada de dos participantes. No mostrar fotos, embeddings ni similitudes individuales.

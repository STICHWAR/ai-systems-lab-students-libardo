# RegresiÃ³n tÃ©cnica â€” 5 de noviembre de 2026

- CompilaciÃ³n Python: aprobada.
- NÃºcleo: 14/14 pruebas aprobadas.
- Seguridad: 15/15 reglas de denegaciÃ³n y reto de un uso aprobados.
- RAG: pÃºblico no recibiÃ³ la guÃ­a restringida del simulacro; estudiante sÃ­ y no recibiÃ³ documentos docentes.
- MCP: la lectura funcionÃ³ y una escritura ejecutada en un proceso efÃ­mero cambiÃ³ exclusivamente `parcial_2`; no se persistiÃ³ el archivo acadÃ©mico ni se interactuÃ³ con la instancia activa.
- Transporte MCP stdio desde el entorno aislado de validaciÃ³n: no disponible por `WinError 5` al crear tuberÃ­as. No se interpreta como fallo del bot que se ejecuta fuera de este entorno.

No se incluyeron credenciales, imÃ¡genes, video-notas, vectores biomÃ©tricos ni valores de similitud.
## CorrecciÃ³n de confirmaciÃ³n de escritura

- Rechazar, expirar o no responder una confirmaciÃ³n no ejecuta la tool de escritura.
- Los callbacks son de un solo uso y se validan contra usuario, chat y token pendiente.
- Las pruebas del nÃºcleo verifican rechazo sin mutaciÃ³n, aceptaciÃ³n Ãºnica y token invÃ¡lido/vencido/reutilizado.
- Estado de validaciÃ³n real: pendiente de la secuencia Aâ€“H en Telegram con una sola instancia reciÃ©n iniciada.

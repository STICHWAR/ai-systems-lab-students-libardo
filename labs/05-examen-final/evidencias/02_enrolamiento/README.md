# Evidencia tÃ©cnica de enrolamiento â€” Santiago Villamizar

Fecha: 5 de noviembre de 2026.

- Consentimiento explÃ­cito: recibido para el enrolamiento local.
- Usuario: `integrante_1` vinculado a su ID de Telegram configurado.
- Fotos solicitadas: 4.
- ParÃ¡metros YuNet de enrolamiento: `score_threshold=0.90`, `nms_threshold=0.30`, `top_k=5000`.
- Las cuatro imÃ¡genes se normalizaron localmente a BGR; su tamaÃ±o fue 960Ã—1280 y no tenÃ­an rotaciÃ³n EXIF.
- `foto1.jpeg`: 0 rostros al umbral 0,90; confianza diagnÃ³stica mÃ¡xima 0,836.
- `foto2.jpeg`: 0 rostros al umbral 0,90; confianza diagnÃ³stica mÃ¡xima 0,831.
- `foto3.jpeg`: 0 rostros al umbral 0,90; confianza diagnÃ³stica mÃ¡xima 0,896.
- `foto4.jpeg`: 1 rostro al umbral 0,90; confianza mÃ¡xima 0,905.
- Tras validar el umbral de detecciÃ³n 0,80, las cuatro fotos cumplieron la regla de exactamente un rostro y landmarks utilizables.
- RegresiÃ³n a 0,80: una imagen en blanco tuvo 0 rostros; un compuesto temporal en memoria de dos rostros tuvo 2. Ninguno se aceptÃ³ para enrolamiento.
- Embeddings guardados: 4, de dimensiÃ³n 128. Se almacenan exclusivamente en `rostros/integrante_1.npz`, directorio excluido de Git.

La primera ejecuciÃ³n a 0,90 fue rechazada; el umbral 0,80 fue configurado tras la comparaciÃ³n y regresiÃ³n documentadas, sin modificar el umbral biomÃ©trico SFace (`FACE_MATCH_THRESHOLD=0.363`). No se almacenan imÃ¡genes ni vectores biomÃ©tricos en esta carpeta de evidencias.

## PreparaciÃ³n de Libardo Bravo

- Rol configurado: docente simulado; ID de Telegram configurado desde `/quiensoy`.
- Inventario local: 3 archivos con extensiÃ³n `.jpeg` en `rostros/input_libardo/`.
- Consentimiento: **pendiente**. No se abrieron, analizaron ni enrolaron fotografÃ­as de Libardo.
## ActualizaciÃ³n de Libardo Bravo â€” 5 de noviembre de 2026

- El titular otorgÃ³ consentimiento explÃ­cito para el enrolamiento biomÃ©trico local de este examen.
- Se usaron los tres archivos `.jpeg` locales: `foto1.jpeg`, `foto2.jpeg` y `foto3.jpeg`.
- Con `FACE_DETECTION_THRESHOLD=0.80`, YuNet detectÃ³ exactamente un rostro con landmarks utilizables en cada archivo. Confianzas diagnÃ³sticas: 0.904, 0.909 y 0.895.
- Resultado tÃ©cnico: 3 embeddings vÃ¡lidos, cada uno de dimensiÃ³n 128.
- El artefacto se mantiene sÃ³lo en `rostros/integrante_2.npz`, almacenamiento local privado excluido de Git.

Esta actualizaciÃ³n reemplaza el estado de consentimiento pendiente de la preparaciÃ³n inicial. No se archivaron fotografÃ­as, video-notas ni vectores biomÃ©tricos. El enrolamiento tÃ©cnico no acredita aÃºn autenticaciÃ³n: falta la prueba real de `/login` en Telegram.

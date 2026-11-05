# Examen 5 â€” Asistente del Curso de IA en Telegram

**Integrantes:** Santiago Villamizar (rol de demostraciÃ³n: estudiante) y Libardo Bravo (rol de demostraciÃ³n: docente).
**Base:** rama `avance-examen-final` del fork STICHWAR, reutilizando el Lab 04.
**Estado:** implementaciÃ³n preparada para pruebas locales. **NO se ha probado en Telegram real, con API ni con rostros de los integrantes.**

## 1. ConfiguraciÃ³n en Windows (PowerShell)

Desde la raÃ­z del ZIP:

```powershell
Copy-Item .env.example .env
uv sync
uv run python labs/05-examen-final/descargar_modelos.py
```

Si `uv sync` avisa que debe regenerar `uv.lock`, permÃ­telo (las dependencias del examen se aÃ±adieron a `pyproject.toml`). Si `uv` no estÃ¡ instalado: `winget install astral-sh.uv`.

En `.env` completa tus valores **sin compartirlos**: `TELEGRAM_BOT_TOKEN`, `LLM_API_KEY` y proveedor/modelo. Bot: crear con @BotFather usando `/newbot`. Se recomienda iniciar con `.env` local y nunca subirlo a Git.

`FACE_DETECTION_THRESHOLD` es la confianza mÃ­nima de YuNet para aceptar un candidato facial Ãºnico; `FACE_MATCH_THRESHOLD` es la similitud coseno mÃ­nima de SFace para aceptar que ese rostro corresponde al usuario enrolado. Son controles distintos: cambiar el primero nunca reduce el segundo ni omite la prueba de vida.

El directorio `models/` se descarga localmente y **no debe subirse a Git**. No se distribuyen modelos, archivos biomÃ©tricos, fotos ni videos en este ZIP.

## 2. Configurar las dos identidades (obligatorio)

Edita `labs/05-examen-final/data/usuarios.json`:

- `integrante_1`: Santiago Villamizar, rol `estudiante`, reemplazar `<CODIGO_1>` por el cÃ³digo real y `telegram_user_id` por el nÃºmero obtenido con `/quiensoy` del bot.
- `integrante_2`: Libardo Bravo, rol `docente`, sin cÃ³digo de estudiante, reemplazar `telegram_user_id` por su ID numÃ©rico.

Edita `data/academico.json`: reemplaza las claves `<CODIGO_1>` y `<CODIGO_2>` por cÃ³digos reales, y verifica nombres. `data/ataques.json`: reemplaza `<CODIGO_1>` en A8. **Los nombres estÃ¡n configurados, pero no inventamos cÃ³digos ni ID de Telegram**.

Para conocer el ID real, arranca el bot y envÃ­a `/quiensoy` antes de configurar el enrolamiento. Aunque el usuario no estÃ© registrado, ese comando mostrarÃ¡ su ID.

## 3. Enrolamiento local, con consentimiento

Cada integrante debe aportar de **3 a 5 fotos originales, nÃ­tidas, con una sola cara**. No incluir fotos ajenas sin consentimiento explÃ­cito. Desde PowerShell:

```powershell
uv run python labs/05-examen-final/enroll_biometrics.py --user integrante_1 --telegram-id ID_1 --fotos foto1.jpg foto2.jpg foto3.jpg --consiento
uv run python labs/05-examen-final/enroll_biometrics.py --user integrante_2 --telegram-id ID_2 --fotos foto1.jpg foto2.jpg foto3.jpg --consiento
```

Se guardan solamente los embeddings en `labs/05-examen-final/rostros/`, carpeta excluida por Git. **Elimina las fotos de prueba** del equipo al concluir su uso. Los embeddings se eliminan despuÃ©s de grabar pruebas y video, y se debe dejar constancia de que efectivamente se hizo. No marques la declaraciÃ³n de borrado como cumplida antes de verificarlo.

## 4. Crear Ã­ndice RAG y ejecutar

```powershell
uv run python labs/05-examen-final/ingest.py --show
uv run python labs/05-examen-final/bot.py
```

Uso en un **chat privado** con el bot: `/start`, `/ayuda`, `/quiensoy`, `/login`, `/logout`. `/login` genera aleatoriamente izquierda, derecha o acercamiento; **enviar una video-nota circular**, no una foto ni un video normal. El reto se consume una sola vez, y caduca segÃºn `LIVENESS_TIMEOUT_SECONDS`.

El bot usa long polling (no requiere dominio pÃºblico). Las acciones de escritura se confirman con botones SÃ­/No; la confirmaciÃ³n caduca. Si LLM o MCP fallan, la respuesta es genÃ©rica y el error queda registrado en el log de Python.

## 5. Pruebas offline ejecutables

```powershell
uv run python labs/05-examen-final/test_nucleo.py
uv run python labs/05-examen-final/pruebas_seguridad.py
```

`test_nucleo.py` valida sesiÃ³n, caducidad, desafÃ­o, bloqueo, filtros de tools y RAG, incluido un texto de inyecciÃ³n indirecta dentro de un Ã­ndice sintÃ©tico. `pruebas_seguridad.py` valida reglas deterministas para los 8 ataques suministrados y 7 propios. **No equivale a ejecutar los ataques completos a travÃ©s del orquestador con un LLM real**, ni demuestra rechazo de deepfakes.

La tabla FAR/FRR debe medirse con **al menos 10 pares genuinos y 20 impostores consentidos o dataset pÃºblico**. Crea `mediciones.csv` (fuera de Git):

```csv
similitud,tipo
0.72,genuino
0.19,impostor
```

y ejecÃºtalo cuando tengas suficientes mediciones:

```powershell
uv run python labs/05-examen-final/evaluar_umbral.py mediciones.csv --umbrales 0.30 0.363 0.45
```

No se han inventado valores FAR/FRR. Selecciona el umbral luego de obtener mediciones de ambos integrantes.

## 6. Escenarios del PDF que necesitan demostraciÃ³n humana

1. `/start`, personalizaciÃ³n y conversaciÃ³n pÃºblica.
2. Pregunta restringida sin sesiÃ³n: rechazada.
3. `/login` con video-nota correcta del estudiante y del docente.
4. Documento de simulacro y notas propias del estudiante.
5. Notas ajenas y caso especial denegados al estudiante.
6. Caso especial y notas de terceros permitidos al docente.
7. `registrar_nota` solicita confirmaciÃ³n; ejecutar solo con SÃ­.
8. Foto de una foto, video pregrabado, intercambio de cuentas, reenvÃ­o y reto vencido rechazados.
9. Tres fallos producen bloqueo; `/logout` y expiraciÃ³n revocan sesiÃ³n.
10. Ejecutar suite de seguridad y grabar su salida.

La prueba del bot exige claves de API propias, token de @BotFather, dos Telegram IDs y los dos participantes reales; esos datos no estÃ¡n en el ZIP.

## 7. Seguridad y limitaciones verificables

- Filtro RAG aplicado **antes de recuperar contenido** mediante `allowed_access_levels` en `VectorStore.search`.
- El software filtra tools segÃºn rol desde `Core`, y el cÃ³digo del estudiante se inyecta en el wrapper de `consultar_mis_notas`, no desde argumentos del modelo.
- El rol es derivado de sesiÃ³n establecida en `Sessions`, no del texto del chat.
- El liveness basado en desplazamiento de YuNet **no constituye detecciÃ³n de vida certificada**. Puede fallar con movimiento natural, Ã¡ngulos, cÃ¡maras, videos reproducidos o deepfakes; exige prueba adversarial y calibraciÃ³n con los dos integrantes.
- El MCP servidor es un proceso de confianza lanzado localmente por el cliente. Si se expone a Internet o se usa por otros clientes, se necesita autenticaciÃ³n y autorizaciÃ³n tambiÃ©n en el servidor; el control actual estÃ¡ en el nÃºcleo de aplicaciÃ³n.
- Historial se limpia cuando cambia identidad o se hace logout. El registro de auditorÃ­a evita imÃ¡genes, embeddings y tokens.
- Se usan datos acadÃ©micos ficticios del profesor. Los documentos restringidos del curso se mantienen versionados para demostrar permisos, pero no se envÃ­an al LLM sin autorizaciÃ³n.

## 8. Entrega

Entregar el informe `INFORME_EXAMEN_5.md` (convertible a PDF), este repositorio/ZIP sin secretos ni biometrÃ­a, el diagrama Mermaid y **video real de 6â€“8 minutos con ambos en cÃ¡mara**. Completar los campos PENDIENTE del informe con capturas, mediciones, enlace y resultados observados, no con datos supuestos.

## Estado auditado â€” 5 de noviembre de 2026

- NÃºcleo local: 18/18 pruebas aprobadas; seguridad: 15/15.
- Verificado en Telegram: login de ambos integrantes, RAG del estudiante, MCP de lectura y registro docente Aâ€“H con confirmaciÃ³n.
- Pendiente: FAR/FRR y pruebas reales especÃ­ficas de reto vencido, reto reutilizado, rostro distinto y bloqueo temporal.

El informe `INFORME_EXAMEN_5.md` distingue los resultados comprobados de los pendientes. No presente como ejecutada una prueba que no tenga evidencia allÃ­ descrita.

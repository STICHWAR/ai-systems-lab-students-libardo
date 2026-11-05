# Plan de pruebas reales de sesiones y liveness

No contiene material biométrico. Marcar cada resultado sólo tras observarlo en Telegram y revisar la auditoría local.

## Cobertura automatizada adicional

La suite `test_nucleo.py` comprueba localmente y de forma determinista que reto vencido, reto inexistente/reutilizado, identidad no coincidente y bloqueo temporal producen eventos de auditoría específicos y no crean una sesión. Esta cobertura no equivale a las pruebas Telegram de la lista siguiente.

1. **Logout:** con Libardo autenticado, enviar `/logout`, después `Consulta las notas del estudiante 2026002.` Debe denegarse. Auditoría esperada: `logout` y `acceso_denegado`.
2. **Expiración:** Santiago inicia sesión y confirma `/quiensoy`; esperar el TTL configurado sin reiniciar; preguntar por el simulacro. Debe denegarse. Auditoría esperada: `sesion_expirada` y `acceso_denegado`.
3. **Formato inválido:** después de `/login`, enviar deliberadamente una foto propia. Debe rechazarse sin sesión. Auditoría: `login_rechazado`, motivo `FormatoMediaInvalido`.
4. **Reenvío:** después de `/login`, reenviar una video-nota propia y consentida. Debe rechazarse antes de descargarse. Auditoría: `VideoNotaReenviada`.
5. **Reto vencido:** iniciar `/login`, esperar más de 60 segundos y enviar una video-nota propia. Debe rechazarse. Auditoría: motivo técnico de reto vencido.
6. **Reto reutilizado:** reutilizar la misma video-nota después de que el reto ya fue consumido. No debe crear sesión. Auditoría: `RetoInexistenteOReutilizado`.
7. **Tres fallos y bloqueo:** usar tres retos nuevos y medios propios inválidos de forma deliberada. Tras el tercero, `/login` debe indicar bloqueo temporal. No realizar intentos adicionales fuera de esta secuencia.
8. **Rostro distinto:** sólo con consentimiento de Santiago y Libardo, enviar el rostro de uno desde la cuenta Telegram del otro para un único reto nuevo. Debe rechazarse sin sesión y registrar el motivo técnico, sin guardar el video.

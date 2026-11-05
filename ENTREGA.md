# Entrega limpia — Examen Final 5

Esta carpeta se entrega sin secretos ni biometría. Antes de ejecutar:

1. Copiar `.env.example` a `.env` y configurar credenciales propias, sin versionarlas.
2. Ejecutar `uv sync`.
3. Descargar localmente los modelos con `uv run python labs/05-examen-final/descargar_modelos.py`.
4. Crear el índice local con `uv run python labs/05-examen-final/ingest.py --show`.
5. Configurar IDs reales, consentimiento y enrolamiento local sólo si se realizarán pruebas biométricas.

Verificaciones reproducibles sin Telegram:

```powershell
uv run python labs/05-examen-final/test_nucleo.py
uv run python labs/05-examen-final/pruebas_seguridad.py
```

Para iniciar el bot, después de configurar `.env` y los artefactos locales:

```powershell
uv run python labs/05-examen-final/bot.py
```

## Exclusiones intencionales

No se incluyen `.env`, tokens, modelos ONNX, fotos, videos, embeddings,
índices generados, auditorías JSONL ni logs. Los resultados auditados, los
pendientes y las limitaciones se encuentran en
`labs/05-examen-final/INFORME_EXAMEN_5.md`.

## Estado de publicación

La rama local preparada es `examen-final-completo`. La publicación remota no
se declara completada hasta que GitHub acepte el push con una cuenta que tenga
permiso de escritura sobre el repositorio de destino.

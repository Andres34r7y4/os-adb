# 💡 Ideas para contribuir

Propuestas curadas y niveladas. Cada una cabe en un PR chico y respeta las capas
(ver `CONTRIBUTING.md`). Comenta en el issue correspondiente antes de empezar.

## 🟢 Fácil (buen primer PR)

1. **`export --format json`** — serializar el buffer a JSON junto al Markdown. Toca solo `engine/adr_service.py` + test.
2. **Modo claro de la TUI** — alternar theme (`ADB_THEME`) con tecla `t` y persistirlo en settings.
3. **`adb stats`** — conteo por tag, última decisión, tamaño de la db. Reutiliza `engine/context.py`.
4. **Comando `adb open`** — abrir `ADR_LOG.md` en `$EDITOR`.
5. **Traducción al inglés** de README + docs (manteniendo el español como base).

## 🟡 Intermedio

6. **`adb edit <id>`** — modal de edición en TUI + comando CLI. Requiere `repository.update()` en el puerto y adapter.
7. **Adapter Postgres** — nuevo `adapters/postgres_repo.py` implementando `DecisionRepository`. Cero cambios en Engine/UI (esa es la gracia).
8. **Tags múltiples** — `tag` → lista; migrar columna, filtros `OR`, UI de chips.
9. **Sync multi-máquina** — export/import con merge por `id` + `created_at`.
10. **Notion two-way** — leer la DB de Notion para mostrar estado de sincronía (✓ publicado).

## 🔴 Avanzado

11. **DB por proyecto** — detectar repo git y usar `~/.adb/projects/<hash>.db`. Cambia `resolve_db_path` + migración.
12. **Plugin system** — entry-points para conectores de terceros (`os_adb.publishers`).
13. **Firmas de decisiones** — hash encadenado por registro (audit trail append-only).

## Cómo proponer una idea

Abre un issue con la plantilla **💡 Idea** (`.github/ISSUE_TEMPLATE/idea.yml`): problema, propuesta, capa(s) afectadas y nivel sugerido.

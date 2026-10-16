# Cómo contribuir a OS-ADB

¡Gracias por querer sumar! Este proyecto es además un **ejemplo vivo de arquitectura en capas** — cada contribución debería respetarlas.

## La regla de oro: Strict Layered Pattern

```text
UI (Typer/Textual) → Engine (casos de uso + settings) → Domain (puro, 0 deps)
                         ↑ inyección vía Protocols (domain/ports.py)
Adapters (SQLAlchemy, publishers) — únicos con I/O
```

- **Domain**: nunca importa nada externo. Ni ORM, ni HTTP, ni TUI.
- **Engine**: orquesta. Recibe repositorios/publishers **inyectados**, no los crea (salvo factories explícitas en `adapters/`).
- **Adapters**: todo I/O (SQLite, webhooks, Notion/Slack) vive aquí, detrás de Protocols.
- **UI**: fina. Sin SQL, sin HTTP directo, sin lógica de negocio.

## Setup en 1 minuto

```bash
git clone https://github.com/Andres34r7y4/os-adb.git
cd os-adb
make install          # .venv + deps de dev
make test             # 38 tests, todo debe estar verde
```

## Flujo de trabajo

1. Abre o elige un issue (`docs/ideas-para-contribuir.md` tiene propuestas niveladas 🟢🟡🔴).
2. Rama: `feat/xxx`, `fix/xxx` o `docs/xxx`.
3. Agrega/actualiza **tests** (`tests/test_*.py` corren headless, sin red salvo stubs locales).
4. Si tocas la TUI, regenera los GIFs: `python docs/demo/generate_gifs.py` (requiere Chromium para el rasterizado; con fallback a cairosvg).
5. PR chico y descriptivo (usa la plantilla). CI debe pasar.

## Convenciones

- Commits tipo *conventional*: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.
- Headers de archivo con el docstring estándar del proyecto (ver cualquier `.py`).
- Español en docs de usuario; código y docstrings pueden mezclar, priorizando claridad.
- Seguridad: nunca commitees secretos (ver `SECURITY.md`). Usa `ADB_*` env vars en ejemplos.

## ¿Primera contribución?

Busca issues con label `good first issue` o empieza por las 🟢 de `docs/ideas-para-contribuir.md`.

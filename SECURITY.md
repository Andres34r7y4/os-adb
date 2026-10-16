# Política de Seguridad

## Versiones soportadas

| Versión | Soportada |
|---------|-----------|
| `main` (última) | ✅ |
| Tags `< 0.1.0` | ❌ |

## Cómo reportar una vulnerabilidad

**No abras un issue público.** Usa uno de estos canales privados:

1. **GitHub Private Vulnerability Reporting**: pestaña *Security → Report a vulnerability* del repositorio (preferido).
2. Email: **architect@andresdelgado.dev** con asunto `[SECURITY] os-adb`.

Incluye: descripción, pasos para reproducir, impacto estimado y, si aplica, PoC.

## Qué puedes esperar

- Confirmación de recepción en **48h**.
- Evaluación y plan en **7 días**.
- Fix + advisory coordinado antes de divulgar. Practicamos **divulgación responsable**: te pedimos no publicar hasta que el parche esté disponible.

## Alcance y modelo de amenaza

`os-adb` es una herramienta **local-first**: la DB vive en tu máquina (`~/.adb/` por defecto) y solo sale tráfico cuando **tú** publicas a un conector (n8n/Slack/Notion).

Buenas prácticas que el propio proyecto aplica y recomienda:

- Los secretos (`webhook_secret`, `notion_token`) van en `~/.adb/config.toml` (solo tu usuario) o mejor en variables de entorno (`ADB_WEBHOOK_SECRET`, `ADB_NOTION_TOKEN`) — **nunca** en el repo ni en screenshots.
- `~/.adb/` debe tener permisos `700` (`chmod 700 ~/.adb`).
- Los webhooks n8n deben validar el header `X-ADB-Secret` (ver `docs/n8n_workflow.md`).
- Revisa con `adb config show` qué conector está activo antes de publicar.

## Fuera de alcance

Ataques que requieran acceso físico/root a tu máquina, ingeniería social, o vulnerabilidades de n8n/Slack/Notion en sí (repórtalas a esos proyectos).

# 🔌 Conectores: n8n, Slack y Notion en 5 minutos

os-adb publica a través del puerto `Publisher` (`adapters/publishers.py`):
tres conectores funcionales, cero SDKs (solo `urllib` stdlib), y agregar uno
nuevo no toca Engine ni UI.

| Conector | Qué hace | Necesitas |
|----------|----------|-----------|
| `n8n` (default) | POST JSON a un Webhook → enrutas a todo | URL del Webhook n8n |
| `slack` | POST directo a un Incoming Webhook | URL `https://hooks.slack.com/...` |
| `notion` | Crea páginas vía API oficial | Token `secret_...` + id de la DB |

## Verificar en 30 segundos (sin credenciales)

```bash
adb publish ADR-XXXXXX --dry-run   # muestra el payload exacto, sin red
```

## 1. n8n (recomendado: una puerta a todo)

```bash
adb config set publisher n8n
adb config set webhook_url https://tu-n8n/webhook/adb
adb config set webhook_secret mi-secreto   # opcional, pero recomendado
adb config set webhook_enabled true
adb webhook ping          # debe responder ✔ Connector OK
adb publish ADR-XXXXXX
```

Payload estable que recibe n8n:

```json
{
  "id": "ADR-A1B2C3", "title": "Use SQLite per Module",
  "context": "…", "justification": "…",
  "tag": "architecture", "created_at": "2026-10-16 00:00:00",
  "source": "os-adb"
}
```

Headers: `Content-Type: application/json` + `X-ADB-Secret` (si lo seteaste).
El ping envía `{"event":"adb.ping","source":"os-adb"}`.

### Workflow n8n importable

Nodos: `Webhook` → `Check Secret (IF)` → `Switch por tag` → `Slack` / `Notion`.

```json
{
  "nodes": [
    {
      "name": "ADB Webhook", "type": "n8n-nodes-base.webhook",
      "position": [200, 300], "typeVersion": 2,
      "parameters": {"path": "adb", "httpMethod": "POST", "responseMode": "onReceived"}
    },
    {
      "name": "Check Secret", "type": "n8n-nodes-base.if",
      "position": [420, 300], "typeVersion": 1,
      "parameters": {"conditions": {"string": [
        {"value1": "={{ $json.headers['x-adb-secret'] }}",
         "operation": "equal", "value2": "mi-secreto-compartido"}]}}
    },
    {
      "name": "Route by Tag", "type": "n8n-nodes-base.switch",
      "position": [640, 300], "typeVersion": 1,
      "parameters": {"dataType": "string", "value1": "={{ $json.body.tag }}",
        "rules": {"values": [
          {"operation": "equal", "value": "incident", "output": 0},
          {"operation": "equal", "value": "architecture", "output": 1}]},
        "fallbackOutput": 2}
    },
    {
      "name": "Slack Alert", "type": "n8n-nodes-base.slack",
      "position": [860, 200], "typeVersion": 1,
      "notes": "Output 0 del Switch. Conecta tu credencial.",
      "parameters": {"channel": "#architecture",
        "text": "={{ '🚨 [' + $json.body.id + '] ' + $json.body.title + '\n' + $json.body.justification }}"}
    },
    {
      "name": "Notion Page", "type": "n8n-nodes-base.notion",
      "position": [860, 320], "typeVersion": 1,
      "notes": "Output 1 del Switch. DB con props title/Tag/Justification.",
      "parameters": {"resource": "databasePage", "databaseId": "TU_DATABASE_ID",
        "properties": {
          "title": "={{ $json.body.id + ' ' + $json.body.title }}",
          "Tag": "={{ $json.body.tag }}",
          "Justification": "={{ $json.body.justification }}"}}}
  ],
  "connections": {
    "ADB Webhook": {"main": [[{"node": "Check Secret", "type": "main", "index": 0}]]},
    "Check Secret": {"main": [[{"node": "Route by Tag", "type": "main", "index": 0}]]},
    "Route by Tag": {"main": [
      [{"node": "Slack Alert", "type": "main", "index": 0}],
      [{"node": "Notion Page", "type": "main", "index": 0}]]}}
}
```

> n8n → Workflows → ⋯ → Import from JSON. **Activa el workflow** (si no,
> el webhook responde 404) y usa la **Production URL**.

## 2. Slack directo

```bash
# En Slack: Apps → Incoming Webhooks → agregar al canal → copiar URL
adb config set publisher slack
adb config set slack_webhook_url https://hooks.slack.com/services/...
adb webhook ping     # postea "🔌 os-adb conectado" en el canal
adb publish ADR-XXXXXX
```

Mensaje que llega:

```text
📜 [ADR-A1B2C3] Use SQLite per Module
#architecture · 2026-10-16 00:00:00
> Eliminates cross-domain coupling…
```

## 3. Notion directo

```bash
# En Notion: Settings → Connections → Develop integrations → New integration
# Copia el token secret_..., comparte tu DB con la integración,
# y copia el id de la DB desde su URL (32 caracteres).
adb config set publisher notion
adb config set notion_token secret_...
adb config set notion_database_id <32-hex>
adb webhook ping     # valida token+DB SIN crear páginas
adb publish ADR-XXXXXX
```

La página se crea con título `[ID] título`, propiedad `Tag`, y el
contexto/justificación como bloques (funciona con cualquier esquema siempre
que la DB tenga la columna de título `Name`, que es el default de Notion).

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---------|----------------|-----|
| `connection refused` (n8n) | n8n apagado o URL local mal | ¿corre n8n? ¿misma red? |
| `404` (n8n) | Workflow en Test o path mal | Activa el workflow, usa Production URL |
| `401/403` | Secreto/token mal | Revisa `webhook_secret` / `notion_token` / comparte la DB con la integración |
| `DB needs a Name column` | DB sin título `Name` | Renombra la columna de título a `Name` |
| `publishing is disabled` | Flag apagado (n8n) | `adb config set webhook_enabled true` |

## Probar sin credenciales (stub local)

```python
# stub_webhook.py — imprime lo que os-adb publica
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
        self.send_response(200); self.end_headers()

HTTPServer(("127.0.0.1", 8080), H).serve_forever()
```

```bash
adb config set webhook_url http://127.0.0.1:8080/hook
adb config set webhook_enabled true
adb publish ADR-XXXXXX
```

## Ruteo sugerido por tag (en n8n)

| Tag | Destino |
|-----|---------|
| `incident` | Slack #incidents (alerta inmediata) |
| `architecture` | Notion ADR database (registro) |
| `dx` | Slack #engineering (visibilidad) |
| resto | Log / archivo en n8n |

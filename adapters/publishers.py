"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Outbound publishers: adapters that push decisions to external systems.
Every connector implements the Publisher port (publish/preview/ping) over
stdlib urllib — no SDKs, no new dependencies. The Engine picks one through
make_publisher(); adding a connector never touches Engine or UI logic.
"""

import json
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Protocol, runtime_checkable

from domain.models import Decision

NOTION_VERSION = "2022-06-28"
NOTION_TITLE_PROPERTY = "Name"  # default title column of a fresh Notion database


class PublisherError(RuntimeError):
    """Raised when a decision cannot be delivered to the external system."""


@runtime_checkable
class Publisher(Protocol):
    """Outbound port: deliver a decision to an external system."""

    def publish(self, decision: Decision) -> dict: ...
    def preview(self, decision: Decision) -> dict: ...
    def ping(self) -> dict: ...


def decision_payload(decision: Decision) -> dict:
    """Canonical JSON payload sent to n8n (stable contract for workflows)."""
    data = asdict(decision)
    data["source"] = "os-adb"
    return data


def _post_json(url: str, body: dict, headers: dict, timeout: int, hint: str) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"status": response.status, "url": url}
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise PublisherError(f"Delivery rejected ({exc.code}): {hint['auth']}") from exc
        if exc.code == 404:
            raise PublisherError(f"Delivery not found (404): {hint['not_found']}") from exc
        raise PublisherError(f"Delivery failed ({exc.code}): {hint['other']}") from exc
    except Exception as exc:
        raise PublisherError(f"Delivery failed: {exc}. {hint['unreachable']}") from exc


class N8NWebhookPublisher:
    """POSTs the decision payload to an n8n Webhook URL (stdlib only)."""

    name = "n8n"

    def __init__(self, webhook_url: str, secret: str = "", timeout: int = 10):
        if not webhook_url or not webhook_url.startswith(("http://", "https://")):
            raise ValueError(
                "N8N webhook URL missing. Run: adb config set webhook_url <https://tu-n8n/webhook/adb>"
            )
        self.webhook_url = webhook_url
        self.secret = secret
        self.timeout = timeout
        self._hint = {
            "auth": "check `webhook_secret` matches the Check Secret node in n8n.",
            "not_found": "check the Webhook path in n8n (production URL, workflow Active).",
            "other": "check the n8n executions log for the failed run.",
            "unreachable": "Is n8n running and reachable from here?",
        }

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.secret:
            headers["X-ADB-Secret"] = self.secret
        return headers

    def publish(self, decision: Decision) -> dict:
        return _post_json(self.webhook_url, decision_payload(decision), self._headers(), self.timeout, self._hint)

    def preview(self, decision: Decision) -> dict:
        return {"target": f"n8n webhook {self.webhook_url}", "body": decision_payload(decision)}

    def ping(self) -> dict:
        return _post_json(
            self.webhook_url,
            {"event": "adb.ping", "source": "os-adb"},
            self._headers(),
            self.timeout,
            self._hint,
        )


def slack_message(decision: Decision) -> str:
    return (
        f"📜 *[{decision.id}] {decision.title}*\n"
        f"#{decision.tag} · {decision.created_at}\n"
        f"> {decision.justification}"
    )


class SlackPublisher:
    """POSTs decisions to a Slack Incoming Webhook URL (no SDK needed).

    Create it in Slack: Apps → Incoming Webhooks → Add to channel → copy URL.
    """

    name = "slack"

    def __init__(self, webhook_url: str, timeout: int = 10):
        if not webhook_url or not webhook_url.startswith("https://hooks.slack.com/"):
            raise ValueError(
                "Slack webhook URL missing. Create an Incoming Webhook in Slack, then: "
                "adb config set slack_webhook_url <https://hooks.slack.com/...>"
            )
        self.webhook_url = webhook_url
        self.timeout = timeout
        self._hint = {
            "auth": "the Slack webhook URL looks revoked — create a new one.",
            "not_found": "the Slack webhook URL is incomplete.",
            "other": "Slack rejected the payload; check the webhook channel.",
            "unreachable": "Check your internet connection.",
        }

    def publish(self, decision: Decision) -> dict:
        return _post_json(
            self.webhook_url, {"text": slack_message(decision)},
            {"Content-Type": "application/json"}, self.timeout, self._hint,
        )

    def preview(self, decision: Decision) -> dict:
        return {"target": "slack incoming webhook", "body": {"text": slack_message(decision)}}

    def ping(self) -> dict:
        return _post_json(
            self.webhook_url, {"text": "🔌 os-adb conectado — test de webhook ✅"},
            {"Content-Type": "application/json"}, self.timeout, self._hint,
        )


def notion_page(decision: Decision) -> dict:
    """Page body for a Notion database with a `Name` title column (the default).

    Context/justification travel as content blocks, so any database schema works.
    """
    return {
        "parent": {},  # filled with {"database_id": ...} by the publisher
        "properties": {
            NOTION_TITLE_PROPERTY: {
                "title": [{"text": {"content": f"[{decision.id}] {decision.title}"}}]
            },
            "Tag": {"rich_text": [{"text": {"content": decision.tag}}]},
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "💡 Context"}}]},
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": decision.context}}]},
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "⚖️ Justification"}}]},
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": decision.justification}}]},
            },
        ],
    }


class NotionPublisher:
    """Creates pages in a Notion database via the official API (stdlib only).

    Setup: Notion → Settings → Connections → Develop integrations → New
    integration (copy the `secret_...` token), share your database with it,
    then: adb config set notion_token secret_... / notion_database_id <32-hex>.
    """

    name = "notion"

    def __init__(self, token: str, database_id: str, api_base: str = "https://api.notion.com", timeout: int = 15):
        if not token or not token.startswith("secret_"):
            raise ValueError(
                "Notion token missing. Create an integration in Notion, then: "
                "adb config set notion_token secret_..."
            )
        if not database_id or len(database_id.replace("-", "")) != 32:
            raise ValueError(
                "Notion database id missing. Share the DB with your integration, then: "
                "adb config set notion_database_id <id de 32 caracteres>"
            )
        self.token = token
        self.database_id = database_id
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self._hint = {
            "auth": "check the token and that the database is Shared with the integration.",
            "not_found": "check the database id (open DB in Notion → copy from URL).",
            "other": "Notion rejected the page; the DB needs a `Name` title column.",
            "unreachable": "Check your internet connection.",
        }

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
        }

    def publish(self, decision: Decision) -> dict:
        body = notion_page(decision)
        body["parent"] = {"database_id": self.database_id}
        return _post_json(f"{self.api_base}/v1/pages", body, self._headers(), self.timeout, self._hint)

    def preview(self, decision: Decision) -> dict:
        body = notion_page(decision)
        body["parent"] = {"database_id": self.database_id}
        return {"target": f"notion database {self.database_id}", "body": body}

    def ping(self) -> dict:
        """Validates token + database without creating any page."""
        request = urllib.request.Request(
            f"{self.api_base}/v1/databases/{self.database_id}",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return {"status": response.status, "url": self.database_id}
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise PublisherError(f"Ping rejected ({exc.code}): {self._hint['auth']}") from exc
            if exc.code == 404:
                raise PublisherError(f"Ping not found (404): {self._hint['not_found']}") from exc
            raise PublisherError(f"Ping failed ({exc.code}): {self._hint['other']}") from exc
        except Exception as exc:
            raise PublisherError(f"Ping failed: {exc}. {self._hint['unreachable']}") from exc


def make_publisher(settings) -> Publisher:
    """Factory: pick the configured connector. Raises ValueError with the
    exact setup steps when credentials are missing."""
    name = (settings.publisher or "n8n").strip().lower()
    if name == "slack":
        return SlackPublisher(webhook_url=settings.slack_webhook_url)
    if name == "notion":
        return NotionPublisher(token=settings.notion_token, database_id=settings.notion_database_id)
    return N8NWebhookPublisher(webhook_url=settings.webhook_url, secret=settings.webhook_secret)

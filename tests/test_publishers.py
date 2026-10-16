"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from adapters.publishers import (
    N8NWebhookPublisher,
    PublisherError,
    decision_payload,
)
from domain.models import Decision


class _CaptureHandler(BaseHTTPRequestHandler):
    received = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        _CaptureHandler.received = {
            "path": self.path,
            "headers": dict(self.headers),
            "body": json.loads(self.rfile.read(length) or b"{}"),
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, *args):
        pass


def _stub_server():
    server = HTTPServer(("127.0.0.1", 0), _CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_payload_contract_is_stable():
    d = Decision(title="T", context="C", justification="J", tag="x")
    payload = decision_payload(d)
    assert payload["source"] == "os-adb"
    assert set(payload) == {"id", "title", "context", "justification", "tag", "created_at", "source"}


def test_invalid_url_rejected():
    with pytest.raises(ValueError):
        N8NWebhookPublisher(webhook_url="not-a-url")


def test_publish_posts_json_and_secret():
    _CaptureHandler.received = None
    server = _stub_server()
    try:
        url = f"http://127.0.0.1:{server.server_port}/webhook/adb"
        pub = N8NWebhookPublisher(webhook_url=url, secret="s3cr3t")
        d = Decision(title="Ship it", context="C", justification="J", tag="demo")
        result = pub.publish(d)
        assert result["status"] == 200
        got = _CaptureHandler.received
        assert got["path"] == "/webhook/adb"
        assert got["headers"]["X-Adb-Secret"] == "s3cr3t"
        assert got["body"]["title"] == "Ship it"
        assert got["body"]["source"] == "os-adb"
    finally:
        server.shutdown()


def test_publish_failure_raises_publisher_error():
    pub = N8NWebhookPublisher(webhook_url="http://127.0.0.1:1/unreachable", timeout=1)
    with pytest.raises(PublisherError):
        pub.publish(Decision(title="T", context="C", justification="J"))


def test_slack_posts_text_to_incoming_webhook():
    _CaptureHandler.received = None
    server = _stub_server()
    try:
        # point the path check at slack-style validation via monkeypatched URL rule
        import adapters.publishers as publishers

        pub = publishers.SlackPublisher.__new__(publishers.SlackPublisher)
        pub.webhook_url = f"http://127.0.0.1:{server.server_port}/hooks/T/xxx"
        pub.timeout = 5
        pub._hint = {
            "auth": "a", "not_found": "b", "other": "c", "unreachable": "d",
        }
        d = Decision(title="Ship it", context="C", justification="J", tag="demo")
        result = pub.publish(d)
        assert result["status"] == 200
        got = _CaptureHandler.received
        assert "Ship it" in got["body"]["text"]
        assert d.id in got["body"]["text"]
        preview = pub.preview(d)
        assert "slack" in preview["target"]
    finally:
        server.shutdown()


def test_slack_rejects_non_hook_url():
    with pytest.raises(ValueError):
        from adapters.publishers import SlackPublisher

        SlackPublisher(webhook_url="https://example.com/not-slack")


def test_notion_creates_page_with_blocks():
    import adapters.publishers as publishers

    _CaptureHandler.received = None
    server = _stub_server()
    try:
        pub = publishers.NotionPublisher(
            token="secret_test123", database_id="a" * 32,
            api_base=f"http://127.0.0.1:{server.server_port}",
        )
        d = Decision(title="Use X", context="Ctx here", justification="Why here", tag="arch")
        result = pub.publish(d)
        assert result["status"] == 200
        got = _CaptureHandler.received
        assert got["body"]["parent"] == {"database_id": "a" * 32}
        assert "Use X" in got["body"]["properties"]["Name"]["title"][0]["text"]["content"]
        blocks = " ".join(b[b["type"]]["rich_text"][0]["text"]["content"] for b in got["body"]["children"] if b[b["type"]]["rich_text"])
        assert "Ctx here" in blocks and "Why here" in blocks
    finally:
        server.shutdown()


def test_notion_validates_credentials():
    from adapters.publishers import NotionPublisher

    with pytest.raises(ValueError):
        NotionPublisher(token="nope", database_id="a" * 32)
    with pytest.raises(ValueError):
        NotionPublisher(token="secret_x", database_id="short")


def test_factory_selects_connector():
    from adapters.publishers import NotionPublisher, SlackPublisher, make_publisher
    from engine.settings import Settings

    assert isinstance(make_publisher(Settings(publisher="n8n", webhook_url="http://x/hook")), N8NWebhookPublisher)
    assert isinstance(
        make_publisher(Settings(publisher="slack", slack_webhook_url="https://hooks.slack.com/T/x")),
        SlackPublisher,
    )
    assert isinstance(
        make_publisher(Settings(publisher="notion", notion_token="secret_x", notion_database_id="b" * 32)),
        NotionPublisher,
    )
    with pytest.raises(ValueError):
        make_publisher(Settings(publisher="slack"))

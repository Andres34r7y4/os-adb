"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Port conformance: every adapter must satisfy its Domain port, and the Engine
must accept any conforming adapter (dependency inversion, verified at runtime).
"""
import tempfile
from pathlib import Path

import pytest

from adapters.publishers import (
    N8NWebhookPublisher,
    NotionPublisher,
    SlackPublisher,
    make_publisher,
)
from adapters.sqlalchemy_repo import SQLAlchemyDecisionRepository
from domain.models import Decision
from domain.ports import DecisionRepository, Publisher, PublisherError
from engine.adr_service import ADRService
from engine.settings import Settings


def _tmp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    import os

    os.close(fd)
    Path(path).unlink()
    return path


def test_repository_satisfies_port():
    repo = SQLAlchemyDecisionRepository(db_path=_tmp_db())
    assert isinstance(repo, DecisionRepository)


def test_publishers_satisfy_port():
    assert isinstance(N8NWebhookPublisher(webhook_url="http://x/hook"), Publisher)
    assert isinstance(
        SlackPublisher(webhook_url="https://hooks.slack.com/T/fake"), Publisher
    )
    assert isinstance(
        NotionPublisher(token="secret_fake", database_id="c" * 32), Publisher
    )


def test_publisher_classes_implement_port_methods():
    for cls in (N8NWebhookPublisher, SlackPublisher, NotionPublisher):
        for method in ("publish", "preview", "ping"):
            assert callable(getattr(cls, method)), f"{cls.__name__}.{method}"


def test_engine_accepts_any_port_implementation():
    class InMemoryRepo:
        def __init__(self):
            self.store = {}

        def save(self, decision):
            self.store[decision.id] = decision
            return decision

        def get_all(self):
            return list(self.store.values())

        def get_by_id(self, record_id):
            return self.store.get(record_id)

        def delete(self, record_id):
            return self.store.pop(record_id, None) is not None

    svc = ADRService(InMemoryRepo())  # no SQLAlchemy involved
    d = svc.record_decision(title="T", context="C", justification="J")
    assert svc.get_decision(d.id) == d
    assert svc.delete_decision(d.id) is True


def test_engine_rejects_non_port():
    with pytest.raises(TypeError):
        ADRService(object())


def test_publish_uses_injected_publisher_no_network():
    class FakePublisher:
        def __init__(self):
            self.seen = None

        def publish(self, decision):
            self.seen = decision
            return {"status": "fake-ok"}

        def preview(self, decision):
            return {"target": "fake", "body": {"id": decision.id}}

        def ping(self):
            return {"status": "fake-pong"}

    svc = ADRService(SQLAlchemyDecisionRepository(db_path=_tmp_db()))
    d = svc.record_decision(title="T", context="C", justification="J")
    fake = FakePublisher()
    assert isinstance(fake, Publisher)
    assert svc.publish_decision(d.id, fake) == {"status": "fake-ok"}
    assert fake.seen.id == d.id
    assert svc.preview_decision(d.id, fake)["body"]["id"] == d.id
    assert svc.ping_publisher(fake) == {"status": "fake-pong"}
    with pytest.raises(ValueError):
        svc.publish_decision("ADR-NOPE", fake)


def test_require_publisher_guidance():
    with pytest.raises(ValueError, match="webhook_enabled"):
        ADRService.require_publisher(Settings(publisher="n8n", webhook_enabled=False))
    ADRService.require_publisher(Settings(publisher="n8n", webhook_enabled=True, webhook_url="http://x"))
    with pytest.raises(ValueError, match="slack_webhook_url|Slack webhook"):
        make_publisher(Settings(publisher="slack"))
    assert PublisherError.__module__ == "domain.ports"

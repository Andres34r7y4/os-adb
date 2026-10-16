"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""
import os
import tempfile

import pytest

from domain.models import Decision
from adapters.sqlalchemy_repo import SQLAlchemyDecisionRepository
from engine.adr_service import ADRService


def _tmp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    return path


def test_domain_validation_rejects_empty_title():
    with pytest.raises(ValueError):
        Decision(title="  ", context="c", justification="j").validate()


def test_domain_validation_rejects_empty_justification():
    with pytest.raises(ValueError):
        Decision(title="t", context="c", justification=" ").validate()


def test_domain_validation_ok():
    assert Decision(title="t", context="c", justification="j").validate() is True


def test_save_and_list_roundtrip():
    repo = SQLAlchemyDecisionRepository(db_path=_tmp_db())
    svc = ADRService(repo)
    d = svc.record_decision(title="Use SQLite", context="ctx", justification="why", tag="architecture")
    assert d.id.startswith("ADR-")
    all_items = svc.list_decisions()
    assert len(all_items) == 1
    assert all_items[0].title == "Use SQLite"


def test_get_by_id_and_missing():
    repo = SQLAlchemyDecisionRepository(db_path=_tmp_db())
    svc = ADRService(repo)
    d = svc.record_decision(title="T", context="C", justification="J")
    assert svc.get_decision(d.id) is not None
    assert svc.get_decision("ADR-NOEXIST") is None


def test_search_by_tag():
    repo = SQLAlchemyDecisionRepository(db_path=_tmp_db())
    svc = ADRService(repo)
    svc.record_decision(title="A", context="c", justification="j", tag="backend")
    svc.record_decision(title="B", context="c", justification="j", tag="frontend")
    assert len(svc.search_by_tag("backend")) == 1
    assert len(svc.search_by_tag("BACKEND")) == 1  # case-insensitive


def test_export_markdown(tmp_path):
    repo = SQLAlchemyDecisionRepository(db_path=_tmp_db())
    svc = ADRService(repo)
    svc.record_decision(title="T1", context="Ctx", justification="Just", tag="demo")
    out = str(tmp_path / "ADR_LOG.md")
    result = svc.export_to_markdown(out)
    assert result == out
    content = open(out, encoding="utf-8").read()
    assert "T1" in content and "Just" in content


def test_export_markdown_empty(tmp_path):
    repo = SQLAlchemyDecisionRepository(db_path=_tmp_db())
    svc = ADRService(repo)
    out = str(tmp_path / "EMPTY.md")
    svc.export_to_markdown(out)
    assert "No architectural decisions" in open(out, encoding="utf-8").read()


def test_delete_existing_and_missing():
    from domain.ports import DecisionRepository

    repo = SQLAlchemyDecisionRepository(db_path=_tmp_db())
    assert isinstance(repo, DecisionRepository)
    svc = ADRService(repo)
    d = svc.record_decision(title="Doomed", context="c", justification="j")
    assert svc.delete_decision(d.id) is True
    assert svc.get_decision(d.id) is None
    assert svc.delete_decision(d.id) is False
    assert svc.delete_decision("ADR-NOEXIST") is False

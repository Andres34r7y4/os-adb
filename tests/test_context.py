"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""
from pathlib import Path

from adapters.sqlalchemy_repo import SQLAlchemyDecisionRepository
from engine.adr_service import ADRService
from engine.context import get_work_context


def _service(tmp_path, monkeypatch):
    db = str(tmp_path / "ctx.db")
    monkeypatch.setenv("ADB_DB", db)
    return ADRService(SQLAlchemyDecisionRepository(db))


def test_context_without_git_uses_folder_name(tmp_path, monkeypatch):
    svc = _service(tmp_path, monkeypatch)
    svc.record_decision(title="Hello", context="c", justification="j", tag="demo")
    ctx = get_work_context(svc, cwd=tmp_path)
    assert ctx.project == tmp_path.name
    assert ctx.branch == ""
    assert ctx.count == 1
    assert ctx.last_title == "Hello"
    assert ctx.last_id.startswith("ADR-")
    assert ctx.db_path.endswith("ctx.db")


def test_context_empty_buffer(tmp_path, monkeypatch):
    svc = _service(tmp_path, monkeypatch)
    ctx = get_work_context(svc, cwd=tmp_path)
    assert ctx.count == 0
    assert ctx.last_id == "" and ctx.last_title == ""


def test_context_inside_git_repo(tmp_path, monkeypatch):
    import shutil
    import subprocess

    if shutil.which("git") is None:
        import pytest

        pytest.skip("git not available")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "checkout", "-qb", "feature/x"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t.t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init"], cwd=tmp_path, check=True)
    svc = _service(tmp_path, monkeypatch)
    ctx = get_work_context(svc, cwd=tmp_path)
    assert ctx.project == tmp_path.name
    assert ctx.branch == "feature/x"


def test_context_survives_broken_db(tmp_path, monkeypatch):
    from engine.context import WorkContext

    class ExplodingRepo:
        db_path = "/nonexistent/x.db"

        def list_decisions(self):
            raise RuntimeError("boom")

    monkeypatch.setenv("ADB_DB", str(tmp_path / "ctx.db"))
    ctx = get_work_context(ExplodingRepo(), cwd=tmp_path)
    assert isinstance(ctx, WorkContext)
    assert ctx.count == 0

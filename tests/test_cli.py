"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""
from typer.testing import CliRunner

from ui.cli import cli_app

runner = CliRunner()


def _invoke(args, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ADB_DB", raising=False)
    return runner.invoke(cli_app, args, env={"ADB_DB": str(tmp_path / "cli.db")})


def test_delete_with_yes(tmp_path, monkeypatch):
    created = _invoke(["add", "--title", "Obsolete", "--justification", "oops"], tmp_path, monkeypatch)
    assert created.exit_code == 0
    record_id = _invoke(["list"], tmp_path, monkeypatch).output.split("ADR-")[1].split()[0]
    record_id = f"ADR-{record_id}"
    deleted = _invoke(["delete", record_id, "--yes"], tmp_path, monkeypatch)
    assert deleted.exit_code == 0
    assert "Deleted" in deleted.output
    assert record_id not in _invoke(["list"], tmp_path, monkeypatch).output


def test_delete_missing_fails(tmp_path, monkeypatch):
    result = _invoke(["delete", "ADR-NOEXIST", "--yes"], tmp_path, monkeypatch)
    assert result.exit_code == 1
    assert "not found" in result.output


def test_about_shows_brand(tmp_path, monkeypatch):
    result = _invoke(["about"], tmp_path, monkeypatch)
    assert result.exit_code == 0
    assert "OS-ADB" in result.output or "Architecture Decision Buffer" in result.output
    assert "Andr" in result.output

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

from engine.settings import (
    load_settings,
    resolve_db_path,
    resolve_export_dir,
    save_settings,
)


def _cfg(tmp_path):
    return tmp_path / "config.toml"


def test_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr("engine.settings.CONFIG_FILE", _cfg(tmp_path))
    for var in ("ADB_DB", "ADB_EXPORT_DIR", "ADB_WEBHOOK_URL", "ADB_WEBHOOK_ENABLED", "ADB_WEBHOOK_SECRET"):
        monkeypatch.delenv(var, raising=False)
    s = load_settings(_cfg(tmp_path))
    assert s.db_path.endswith(".adb/adr_buffer.db")
    assert s.export_dir == "."
    assert s.webhook_enabled is False
    assert s.customized == frozenset()


def test_env_overrides_file(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    s = load_settings(cfg)
    s.db_path = "/custom/db.db"
    s.webhook_enabled = True
    save_settings(s, cfg)
    monkeypatch.setenv("ADB_DB", "/env/db.db")
    monkeypatch.setenv("ADB_WEBHOOK_ENABLED", "false")
    loaded = load_settings(cfg)
    assert loaded.db_path == "/env/db.db"
    assert loaded.webhook_enabled is False
    assert "db_path" in loaded.customized


def test_save_load_roundtrip(tmp_path):
    cfg = _cfg(tmp_path)
    s = load_settings(cfg)
    s.export_dir = "/tmp/exports"
    s.webhook_url = "https://n8n.example.com/webhook/adb"
    s.webhook_enabled = True
    save_settings(s, cfg)
    assert cfg.exists()
    loaded = load_settings(cfg)
    assert loaded.export_dir == "/tmp/exports"
    assert loaded.webhook_url == "https://n8n.example.com/webhook/adb"
    assert loaded.webhook_enabled is True


def test_resolve_db_path_priority(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    monkeypatch.delenv("ADB_DB", raising=False)
    # explicit wins over everything
    assert resolve_db_path("/explicit.db", load_settings(cfg)) == "/explicit.db"
    # env wins over file/defaults
    monkeypatch.setenv("ADB_DB", "/env.db")
    assert resolve_db_path(None, load_settings(cfg)) == "/env.db"
    monkeypatch.delenv("ADB_DB")


def test_resolve_db_path_legacy_fallback(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    monkeypatch.delenv("ADB_DB", raising=False)
    monkeypatch.chdir(tmp_path)
    # no legacy file -> default
    assert resolve_db_path(None, load_settings(cfg)).endswith(".adb/adr_buffer.db")
    # legacy local file present -> used (backward compat)
    Path("adr_buffer.db").touch()
    assert resolve_db_path(None, load_settings(cfg)) == "adr_buffer.db"


def test_resolve_export_dir_creates_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("ADB_EXPORT_DIR", str(tmp_path / "out" / "nested"))
    from engine.settings import load_settings as ls

    path = resolve_export_dir(ls(_cfg(tmp_path)))
    assert path.is_dir()

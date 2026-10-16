"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Settings: where the DB lives, where exports go, and where webhooks point.
Precedence for every key: explicit arg > $ENV > ~/.adb/config.toml > default.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

CONFIG_DIR = Path.home() / ".adb"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_DB = CONFIG_DIR / "adr_buffer.db"

ENV_DB = "ADB_DB"
ENV_EXPORT_DIR = "ADB_EXPORT_DIR"
ENV_PUBLISHER = "ADB_PUBLISHER"
ENV_WEBHOOK_URL = "ADB_WEBHOOK_URL"
ENV_WEBHOOK_ENABLED = "ADB_WEBHOOK_ENABLED"
ENV_WEBHOOK_SECRET = "ADB_WEBHOOK_SECRET"
ENV_SLACK_WEBHOOK_URL = "ADB_SLACK_WEBHOOK_URL"
ENV_NOTION_TOKEN = "ADB_NOTION_TOKEN"
ENV_NOTION_DATABASE_ID = "ADB_NOTION_DATABASE_ID"

PUBLISHERS = ("n8n", "slack", "notion")


@dataclass
class Settings:
    """Effective configuration. `customized` tracks keys the user set
    (config file or env), so legacy fallbacks never override explicit intent."""

    db_path: str = str(DEFAULT_DB)
    export_dir: str = "."
    publisher: str = "n8n"
    webhook_url: str = ""
    webhook_enabled: bool = False
    webhook_secret: str = ""
    slack_webhook_url: str = ""
    notion_token: str = ""
    notion_database_id: str = ""
    customized: frozenset = field(default_factory=frozenset)


_KEYS = ("db_path", "export_dir", "publisher", "webhook_url", "webhook_enabled", "webhook_secret", "slack_webhook_url", "notion_token", "notion_database_id")


def _read_config_file(path: Path = CONFIG_FILE) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _strtobool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


def load_settings(config_file: Path = CONFIG_FILE) -> Settings:
    file_data = _read_config_file(config_file)
    defaults = {"db_path": str(DEFAULT_DB), "export_dir": ".", "publisher": "n8n",
                "webhook_url": "", "webhook_enabled": False, "webhook_secret": "",
                "slack_webhook_url": "", "notion_token": "", "notion_database_id": ""}
    customized = set(k for k in file_data if k in _KEYS and file_data.get(k) != defaults.get(k))

    db_path = str(file_data.get("db_path", str(DEFAULT_DB)))
    export_dir = str(file_data.get("export_dir", "."))
    publisher = str(file_data.get("publisher", "n8n"))
    webhook_url = str(file_data.get("webhook_url", ""))
    webhook_enabled = bool(file_data.get("webhook_enabled", False))
    webhook_secret = str(file_data.get("webhook_secret", ""))
    slack_webhook_url = str(file_data.get("slack_webhook_url", ""))
    notion_token = str(file_data.get("notion_token", ""))
    notion_database_id = str(file_data.get("notion_database_id", ""))

    if os.environ.get(ENV_DB):
        db_path = os.environ[ENV_DB]
        customized.add("db_path")
    if os.environ.get(ENV_EXPORT_DIR):
        export_dir = os.environ[ENV_EXPORT_DIR]
        customized.add("export_dir")
    if os.environ.get(ENV_WEBHOOK_URL):
        webhook_url = os.environ[ENV_WEBHOOK_URL]
        customized.add("webhook_url")
    if os.environ.get(ENV_WEBHOOK_ENABLED):
        webhook_enabled = _strtobool(os.environ[ENV_WEBHOOK_ENABLED])
        customized.add("webhook_enabled")
    if os.environ.get(ENV_WEBHOOK_SECRET):
        webhook_secret = os.environ[ENV_WEBHOOK_SECRET]
        customized.add("webhook_secret")
    if os.environ.get(ENV_PUBLISHER):
        publisher = os.environ[ENV_PUBLISHER].strip().lower()
        customized.add("publisher")
    if os.environ.get(ENV_SLACK_WEBHOOK_URL):
        slack_webhook_url = os.environ[ENV_SLACK_WEBHOOK_URL]
        customized.add("slack_webhook_url")
    if os.environ.get(ENV_NOTION_TOKEN):
        notion_token = os.environ[ENV_NOTION_TOKEN]
        customized.add("notion_token")
    if os.environ.get(ENV_NOTION_DATABASE_ID):
        notion_database_id = os.environ[ENV_NOTION_DATABASE_ID]
        customized.add("notion_database_id")

    if publisher not in PUBLISHERS:
        publisher = "n8n"

    return Settings(
        db_path=db_path,
        export_dir=export_dir,
        publisher=publisher,
        webhook_url=webhook_url,
        webhook_enabled=webhook_enabled,
        webhook_secret=webhook_secret,
        slack_webhook_url=slack_webhook_url,
        notion_token=notion_token,
        notion_database_id=notion_database_id,
        customized=frozenset(customized),
    )


def save_settings(settings: Settings, config_file: Path = CONFIG_FILE) -> Path:
    """Persist user-facing keys as TOML (stdlib only, flat keys)."""
    config_file.parent.mkdir(parents=True, exist_ok=True)

    def q(value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = [
        "# OS-ADB configuration — edit via `adb config set` or the TUI (c).",
        f"db_path = {q(settings.db_path)}",
        f"export_dir = {q(settings.export_dir)}",
        f"publisher = {q(settings.publisher)}",
        f"webhook_url = {q(settings.webhook_url)}",
        f"webhook_enabled = {'true' if settings.webhook_enabled else 'false'}",
        f"webhook_secret = {q(settings.webhook_secret)}",
        f"slack_webhook_url = {q(settings.slack_webhook_url)}",
        f"notion_token = {q(settings.notion_token)}",
        f"notion_database_id = {q(settings.notion_database_id)}",
        "",
    ]
    config_file.write_text("\n".join(lines), encoding="utf-8")
    return config_file


def resolve_db_path(explicit: "str | None" = None, settings: "Settings | None" = None) -> str:
    """Priority: explicit arg > $ADB_DB > configured db_path (file/env)
    > legacy ./adr_buffer.db (if it exists) > ~/.adb/adr_buffer.db.
    """
    if explicit:
        return explicit
    if os.environ.get(ENV_DB):
        return os.environ[ENV_DB]
    settings = settings or load_settings()
    if "db_path" in settings.customized:
        return os.path.expanduser(settings.db_path)
    legacy = Path("adr_buffer.db")
    if legacy.exists():
        return str(legacy)
    return os.path.expanduser(settings.db_path)


def resolve_export_dir(settings: "Settings | None" = None) -> Path:
    settings = settings or load_settings()
    path = Path(os.path.expanduser(settings.export_dir or "."))
    path.mkdir(parents=True, exist_ok=True)
    return path

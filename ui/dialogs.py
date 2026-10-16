"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Dialogs: dumb modal screens shared by Home and Buffer. They collect input and
return payloads; persistence and Engine calls stay with the caller screens.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Static

from engine.settings import load_settings
from ui.brand import BANNER, SOCIALS, TAGLINE


class AddDecisionScreen(ModalScreen):
    """Modal form to record a new decision without leaving the TUI."""

    BINDINGS = [Binding("q", "cancel", "Cancel")]

    CSS = """
    AddDecisionScreen { align: center middle; }
    #add-dialog { width: 72; height: auto; padding: 1 2; background: $surface; border: round $primary; }
    #add-dialog Input { margin: 0 0 1 0; }
    #add-dialog Input:focus { border: solid $primary; }
    #add-actions { height: auto; align: right middle; margin-top: 1; }
    #add-actions Button { margin-left: 1; }
    #add-error { color: $error; height: 1; margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="add-dialog"):
            yield Label(" ➕ New Architectural Decision", classes="panel-header")
            yield Label("", id="add-error")
            yield Input(placeholder="Title (required)", id="f-title")
            yield Input(placeholder="Context / problem statement", id="f-context")
            yield Input(placeholder="Justification & trade-offs (required)", id="f-justification")
            yield Input(placeholder="Tag (default: general)", value="general", id="f-tag")
            with Horizontal(id="add-actions"):
                yield Button("Save", variant="success", id="btn-save")
                yield Button("Cancel", variant="default", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
            return
        title = self.query_one("#f-title", Input).value.strip()
        context = self.query_one("#f-context", Input).value.strip() or "Not specified"
        justification = self.query_one("#f-justification", Input).value.strip()
        tag = self.query_one("#f-tag", Input).value.strip() or "general"
        if not title or not justification:
            self.query_one("#add-error", Label).update("⚠ Title and justification are required.")
            return
        self.dismiss({"title": title, "context": context, "justification": justification, "tag": tag})

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.query_one("#btn-save", Button).press()

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfigScreen(ModalScreen):
    """Settings editor: database location, export folder, connectors."""

    BINDINGS = [Binding("q", "cancel", "Cancel")]

    CSS = """
    ConfigScreen { align: center middle; }
    #cfg-dialog { width: 76; height: 92%; padding: 1 2; background: $surface; border: round $secondary; }
    #cfg-scroll { height: 1fr; }
    #cfg-dialog Input { margin: 0 0 1 0; }
    #cfg-dialog Input:focus { border: solid $secondary; }
    #cfg-dialog Checkbox { margin: 0 0 1 0; }
    #cfg-actions { height: auto; align: right middle; margin-top: 1; }
    #cfg-actions Button { margin-left: 1; }
    #cfg-result { height: auto; margin-top: 1; }
    .cfg-label { color: $text-muted; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        settings = load_settings()
        with Vertical(id="cfg-dialog"):
            yield Label(" ⚙ Configuration", classes="panel-header-blue")
            with VerticalScroll(id="cfg-scroll"):
                yield Label("Database file (.db — default ~/.adb, or ./local)", classes="cfg-label")
                yield Input(value=settings.db_path, id="cfg-db")
                yield Label("Export folder for ADR_LOG.md", classes="cfg-label")
                yield Input(value=settings.export_dir, id="cfg-exports")
                yield Label("Connector: n8n, slack or notion", classes="cfg-label")
                yield Input(value=settings.publisher, id="cfg-publisher")
                yield Label("n8n Webhook URL (Notion / Slack / … via n8n)", classes="cfg-label")
                yield Input(value=settings.webhook_url, placeholder="https://n8n.example.com/webhook/adb", id="cfg-webhook")
                yield Input(value=settings.webhook_secret, placeholder="Shared secret (optional)", password=True, id="cfg-secret")
                yield Checkbox("Enable n8n webhook publishing", value=settings.webhook_enabled, id="cfg-enabled")
                yield Label("Slack Incoming Webhook URL (direct connector)", classes="cfg-label")
                yield Input(value=settings.slack_webhook_url, placeholder="https://hooks.slack.com/...", id="cfg-slack")
                yield Label("Notion token + database id (direct connector)", classes="cfg-label")
                yield Input(value=settings.notion_token, placeholder="secret_...", password=True, id="cfg-notion-token")
                yield Input(value=settings.notion_database_id, placeholder="32-char database id", id="cfg-notion-db")
                yield Label("", id="cfg-result")
            with Horizontal(id="cfg-actions"):
                yield Button("Test", variant="primary", id="cfg-test")
                yield Button("Save", variant="success", id="cfg-save")
                yield Button("Cancel", variant="default", id="cfg-cancel")

    def _collect(self) -> dict:
        return {
            "db_path": self.query_one("#cfg-db", Input).value.strip(),
            "export_dir": self.query_one("#cfg-exports", Input).value.strip() or ".",
            "publisher": self.query_one("#cfg-publisher", Input).value.strip().lower() or "n8n",
            "webhook_url": self.query_one("#cfg-webhook", Input).value.strip(),
            "webhook_secret": self.query_one("#cfg-secret", Input).value,
            "webhook_enabled": self.query_one("#cfg-enabled", Checkbox).value,
            "slack_webhook_url": self.query_one("#cfg-slack", Input).value.strip(),
            "notion_token": self.query_one("#cfg-notion-token", Input).value.strip(),
            "notion_database_id": self.query_one("#cfg-notion-db", Input).value.strip(),
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cfg-cancel":
            self.dismiss(None)
            return
        if event.button.id == "cfg-test":
            self.notify("Testing connector…")
            self.run_worker(self._test_worker(self._collect()), exclusive=True)
            return
        self.dismiss(self._collect())

    async def _test_worker(self, fields: dict) -> None:
        import asyncio

        from adapters.publishers import PublisherError, make_publisher
        from engine.settings import PUBLISHERS, Settings

        try:
            if fields.get("publisher", "n8n") not in PUBLISHERS:
                raise ValueError(f"publisher must be one of: {', '.join(PUBLISHERS)}")
            settings = Settings(
                db_path=fields.get("db_path") or "~/.adb/adr_buffer.db",
                export_dir=fields.get("export_dir") or ".",
                publisher=fields.get("publisher") or "n8n",
                webhook_url=fields.get("webhook_url") or "",
                webhook_enabled=bool(fields.get("webhook_enabled")),
                webhook_secret=fields.get("webhook_secret") or "",
                slack_webhook_url=fields.get("slack_webhook_url") or "",
                notion_token=fields.get("notion_token") or "",
                notion_database_id=fields.get("notion_database_id") or "",
            )
            result = await asyncio.to_thread(make_publisher(settings).ping)
        except (ValueError, PublisherError) as exc:
            self._show_test_result(False, str(exc))
            return
        self._show_test_result(True, f"✔ Connector OK (status {result.get('status')}).")

    def _show_test_result(self, ok: bool, message: str) -> None:
        label = self.query_one("#cfg-result", Label)
        label.update(f"[{'green' if ok else 'red'}]{message}[/]")

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmDeleteScreen(ModalScreen):
    """Destructive-action guard: delete only on explicit confirmation."""

    BINDINGS = [Binding("q", "cancel", "Cancel")]

    CSS = """
    ConfirmDeleteScreen { align: center middle; }
    #del-dialog { width: 64; height: auto; padding: 1 2; background: $surface; border: round $error; }
    #del-actions { height: auto; align: right middle; margin-top: 1; }
    #del-actions Button { margin-left: 1; }
    """

    def __init__(self, record_id: str, title: str):
        super().__init__()
        self.record_id = record_id
        self.title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="del-dialog"):
            yield Label(" 🗑 Eliminar decisión", classes="panel-header")
            yield Static(f"[cyan][{self.record_id}][/cyan] {self.title}\n\nEsta acción no se puede deshacer.")
            with Horizontal(id="del-actions"):
                yield Button("Delete", variant="error", id="del-yes")
                yield Button("Cancel", variant="default", id="del-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "del-yes")

    def action_cancel(self) -> None:
        self.dismiss(False)


class HelpScreen(ModalScreen):
    """Help + brand: every shortcut, the ritual, logo and socials."""

    CSS = """
    HelpScreen { align: center middle; }
    #help-dialog { width: 84; height: 90%; padding: 1 2; background: $surface; border: round $secondary; align: center middle; }
    #help-scroll { height: 1fr; align: center middle; }
    #help-inner { width: auto; height: auto; }
    #help-close { height: auto; align: center middle; margin-top: 1; }
    .help-logo { color: $primary; text-align: center; }
    .help-socials { color: $secondary; margin: 1 0 0 0; text-align: center; }
    .help-tagline { color: $text-muted; text-style: italic; margin: 0 0 1 0; text-align: center; }
    .help-h { color: $secondary; text-style: bold; margin-top: 1; text-align: center; }
    .help-body { width: auto; text-align: center; }
    """

    BINDINGS = [
        Binding("escape", "close_help", "Close"),
        Binding("q", "close_help", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            with VerticalScroll(id="help-scroll"):
                with Vertical(id="help-inner"):
                    yield Label(BANNER, classes="help-logo")
                    yield Label(SOCIALS, classes="help-socials")
                    yield Label(f'“{TAGLINE}”', classes="help-tagline")
                    yield Label(" ⌨ Atajos", classes="help-h")
                    yield Static(
                        "[bold $accent]n[/] nueva decisión (modal con validación)\n"
                        "[bold $accent]d[/] eliminar seleccionada (pide confirmación)\n"
                        "[bold $accent]/[/] foco en filtro · [bold $accent]enter[/] ver detalle\n"
                        "[bold $accent]p[/] publicar seleccionada (conector activo)\n"
                        "[bold $accent]c[/] configuración (db, exports, conectores)\n"
                        "[bold $accent]e[/] exportar ADR_LOG.md · [bold $accent]r[/] refrescar\n"
                        "[bold $accent]q[/] salir · [bold $accent]?[/] esta ayuda",
                        classes="help-body",
                    )
                    yield Label(" ◈ Ritual sugerido", classes="help-h")
                    yield Static(
                        "1. Pulsa [bold]n[/] cuando tomes una decisión (2 segundos, sin salir del flow)\n"
                        "2. Usa [bold]/[/] para encontrarla meses después\n"
                        "3. [bold]e[/] para versionarla en git · [bold]p[/] para llevarla a Notion/Slack",
                        classes="help-body",
                    )
            with Horizontal(id="help-close"):
                yield Button("Close", variant="primary", id="help-ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_close_help(self) -> None:
        self.dismiss(None)

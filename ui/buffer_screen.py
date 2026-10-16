"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Buffer screen: the decision table + inspector. Owns no business logic —
every action delegates to ADRService (Engine). Opened from Home (`b`).
"""

from typing import List, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label, Static

from adapters.sqlalchemy_repo import SQLAlchemyDecisionRepository
from domain.models import Decision
from engine.adr_service import ADRService
from engine.settings import CONFIG_FILE, load_settings, resolve_db_path, save_settings
from ui.dialogs import (
    AddDecisionScreen,
    ConfigScreen,
    ConfirmDeleteScreen,
    HelpScreen,
)


class BufferScreen(Screen):
    """Decision Buffer Log + Inspector."""

    BINDINGS = [
        Binding("n", "new_decision", "New"),
        Binding("d", "delete", "Delete"),
        Binding("/", "focus_search", "Filter"),
        Binding("p", "publish", "Publish"),
        Binding("c", "configure", "Config"),
        Binding("e", "export_md", "Export MD"),
        Binding("r", "refresh", "Refresh"),
        Binding("question_mark", "help", "Help"),
        Binding("escape", "go_home", "Home"),
        Binding("q", "quit", "Quit"),
    ]

    CSS = """
    #sidebar { width: 45%; padding: 0 1; border-right: solid $primary; }
    #detail-col { width: 55%; padding: 0 1; }
    #search-input { margin-bottom: 1; background: $surface; border: solid $panel; }
    #search-input:focus { border: solid $primary; }
    #decision-table { height: 1fr; background: $surface; }
    #decision-table:focus { border: solid $primary; }
    #decision-table > .datatable--cursor { background: $primary-muted; }
    #decision-table > .datatable--header { background: $boost; color: $primary; text-style: bold; }
    #detail-panel { height: 1fr; color: $text; padding: 1 2; background: $surface; border: round $panel; }
    #status-bar { color: $text-muted; padding: 1 0 0 0; }
    """

    def __init__(self, autofocus_search: bool = False):
        super().__init__()
        self.service = ADRService(SQLAlchemyDecisionRepository(resolve_db_path()))
        self.decisions: List[Decision] = []
        self.filtered: List[Decision] = []
        self.selected: Optional[Decision] = None
        self.filter_text = ""
        self.autofocus_search = autofocus_search

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Vertical(
                Label(" 📋 Decision Buffer Log", classes="panel-header"),
                Input(placeholder="Filter by title/tag/justification… ( / )", id="search-input"),
                DataTable(id="decision-table"),
                Label("", id="status-bar"),
                id="sidebar",
            ),
            Vertical(
                Label(" 🔍 Decision Inspector", classes="panel-header"),
                Static("No records yet — press [bold $success]n[/bold $success] to record your first decision.", id="detail-panel"),
                id="detail-col",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#decision-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_column("ID", width=12)
        table.add_column("Tag", width=14)
        table.add_column("Title")
        self.refresh_data()
        if self.autofocus_search:
            self.query_one("#search-input", Input).focus()
        else:
            self.query_one("#decision-table", DataTable).focus()

    def on_screen_resume(self) -> None:
        """Refresh when coming back (records may have been added from Home)."""
        self.refresh_data()

    # -- data -------------------------------------------------------------
    def refresh_data(self) -> None:
        try:
            self.decisions = self.service.list_decisions()
        except Exception as exc:  # storage failure -> toast, keep old state
            self.notify(f"Could not load decisions: {exc}", severity="error")
            return
        self.apply_filter()

    def apply_filter(self) -> None:
        q = self.filter_text.strip().lower()
        if q:
            self.filtered = [
                d for d in self.decisions
                if q in d.title.lower() or q in d.tag.lower() or q in d.justification.lower()
            ]
        else:
            self.filtered = list(self.decisions)
        self.render_table()
        self.render_status_bar()

    def render_status_bar(self) -> None:
        settings = load_settings()
        try:
            from adapters.publishers import make_publisher

            make_publisher(settings)
            pub_state = f"pub:{settings.publisher}✓"
        except ValueError:
            pub_state = f"pub:{settings.publisher}✗"
        self.query_one("#status-bar", Label).update(
            f"{len(self.filtered)}/{len(self.decisions)} records"
            f" · db: {self.service.repository.db_path}"
            f" · exports: {settings.export_dir}"
            f" · {pub_state}"
        )

    def render_table(self) -> None:
        table = self.query_one("#decision-table", DataTable)
        table.clear()
        for d in self.filtered:
            table.add_row(d.id, f"#{d.tag}", d.title, key=d.id)
        if self.filtered:
            self.select_decision(self.filtered[0].id)
        else:
            self.selected = None
            self.query_one("#detail-panel", Static).update(
                "No records match — press [bold $success]n[/bold $success] for a new decision or clear the filter."
                if self.decisions else
                "No records yet — press [bold $success]n[/bold $success] to record your first decision."
            )

    def select_decision(self, record_id: str) -> None:
        d = next((x for x in self.filtered if x.id == record_id), None)
        if d is None:
            return
        self.selected = d
        self.query_one("#detail-panel", Static).update(
            f"[bold $primary]{d.title}[/bold $primary] [cyan][{d.id}][/cyan]\n"
            f"[dim]Date: {d.created_at} | Tag: #{d.tag}[/dim]\n\n"
            f"[bold $secondary]Context / Problem:[/bold $secondary]\n{d.context}\n\n"
            f"[bold $accent]Justification & Trade-offs:[/bold $accent]\n{d.justification}"
        )

    # -- events ------------------------------------------------------------
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key is not None and event.row_key.value is not None:
            self.select_decision(str(event.row_key.value))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self.filter_text = event.value
            self.apply_filter()

    # -- actions -----------------------------------------------------------
    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_refresh(self) -> None:
        self.refresh_data()
        self.notify("Buffer refreshed")

    def action_new_decision(self) -> None:
        self.app.push_screen(AddDecisionScreen(), self._on_add_dismissed)

    def _on_add_dismissed(self, payload: Optional[dict]) -> None:
        if not payload:
            return
        try:
            d = self.service.record_decision(**payload)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        except Exception as exc:
            self.notify(f"Could not save: {exc}", severity="error")
            return
        self.refresh_data()
        self.select_decision(d.id)
        self.notify(f"Saved [{d.id}] {d.title}", severity="information")

    def action_configure(self) -> None:
        self.app.push_screen(ConfigScreen(), self._on_config_dismissed)

    def _on_config_dismissed(self, payload: Optional[dict]) -> None:
        if not payload:
            return
        from engine.settings import PUBLISHERS

        old_db = load_settings().db_path
        if payload.get("publisher", "n8n") not in PUBLISHERS:
            self.notify(f"publisher must be one of: {', '.join(PUBLISHERS)}", severity="error")
            return
        settings = load_settings()
        settings.db_path = payload["db_path"] or settings.db_path
        settings.export_dir = payload["export_dir"]
        settings.publisher = payload["publisher"]
        settings.webhook_url = payload["webhook_url"]
        settings.webhook_secret = payload["webhook_secret"]
        settings.webhook_enabled = bool(payload["webhook_enabled"])
        settings.slack_webhook_url = payload["slack_webhook_url"]
        settings.notion_token = payload["notion_token"]
        settings.notion_database_id = payload["notion_database_id"]
        save_settings(settings)
        self.notify(f"Settings saved to {CONFIG_FILE}", severity="information")
        if payload["db_path"] and payload["db_path"] != old_db:
            # Re-wire to the new database immediately.
            self.service = ADRService(SQLAlchemyDecisionRepository(resolve_db_path()))
            self.notify("Database changed — buffer reloaded.", severity="warning")
        self.refresh_data()

    def action_publish(self) -> None:
        if self.selected is None:
            self.notify("Nothing selected to publish.", severity="warning")
            return
        from adapters.publishers import make_publisher

        try:
            settings = load_settings()
            ADRService.require_publisher(settings)
            result = self.service.publish_decision(self.selected.id, make_publisher(settings))
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        self.notify(f"Published [{self.selected.id}] (status {result.get('status')}).", severity="information")

    def action_delete(self) -> None:
        if self.selected is None:
            self.notify("Nothing selected to delete.", severity="warning")
            return
        self.app.push_screen(
            ConfirmDeleteScreen(self.selected.id, self.selected.title),
            self._on_delete_dismissed,
        )

    def _on_delete_dismissed(self, confirmed: Optional[bool]) -> None:
        if not confirmed or self.selected is None:
            return
        record_id = self.selected.id
        try:
            deleted = self.service.delete_decision(record_id)
        except Exception as exc:
            self.notify(f"Could not delete: {exc}", severity="error")
            return
        if not deleted:
            self.notify(f"[{record_id}] was already gone.", severity="warning")
            return
        self.refresh_data()
        self.notify(f"Deleted [{record_id}].", severity="information")

    def action_help(self) -> None:
        from ui.dialogs import HelpScreen as _Help

        if isinstance(self.app.screen, _Help):
            return
        self.app.push_screen(HelpScreen())

    def action_export_md(self) -> None:
        try:
            out = self.service.export_to_markdown()
        except Exception as exc:
            self.notify(f"Export failed: {exc}", severity="error")
            return
        count = len(self.decisions)
        self.notify(f"Exported {count} decision(s) to {out}", severity="information")

    def action_go_home(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()

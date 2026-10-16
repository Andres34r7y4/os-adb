"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional
from adapters.sqlalchemy_repo import SQLAlchemyDecisionRepository
from engine.adr_service import ADRService
from engine.settings import CONFIG_FILE, load_settings, save_settings

cli_app = typer.Typer(
    help="OS-ADB: Architecture Decision Buffer CLI",
    no_args_is_help=False,
    invoke_without_command=True,
)
console = Console()


@cli_app.callback()
def _root(ctx: typer.Context):
    """Launch the interactive TUI when no subcommand is given (bare `adb`)."""
    if ctx.invoked_subcommand is None:
        from ui.tui_app import ADBTuiApp

        ADBTuiApp().run()
        raise typer.Exit()


def get_service() -> ADRService:
    repo = SQLAlchemyDecisionRepository()
    return ADRService(repo)


@cli_app.command("add")
def add_decision(
    title: str = typer.Option(..., "--title", "-t", help="Title of the decision"),
    justification: str = typer.Option(..., "--justification", "-j", help="Justification/Trade-off"),
    context: str = typer.Option("Not specified", "--context", "-c", help="Context or problem statement"),
    tag: str = typer.Option("architecture", "--tag", help="Category tag"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Also deliver to the n8n webhook"),
):
    """Record a new architectural decision in 2 seconds."""
    service = get_service()
    decision = service.record_decision(title=title, context=context, justification=justification, tag=tag)
    console.print(f"[bold green]✔ Saved Decision [/bold green][cyan][{decision.id}][/cyan]: {decision.title}")
    if publish:
        try:
            result = service.publish_decision(decision.id)
            console.print(f"[dim]↗ Published via webhook (status {result.get('status')}).[/dim]")
        except Exception as exc:
            console.print(f"[yellow]⚠ Saved locally, but publish failed: {exc}[/yellow]")


@cli_app.command("list")
def list_decisions():
    """Display recorded architectural decisions in a formatted table."""
    service = get_service()
    decisions = service.list_decisions()

    if not decisions:
        console.print("[yellow]No decisions recorded in buffer.[/yellow]")
        return

    table = Table(title="📜 Architecture Decision Buffer")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Date", style="dim")
    table.add_column("Tag", style="magenta")
    table.add_column("Title", style="bold white")

    for d in decisions:
        table.add_row(d.id, d.created_at, f"#{d.tag}", d.title)

    console.print(table)


@cli_app.command("show")
def show_decision(record_id: str = typer.Argument(..., help="Decision ID, e.g. ADR-ABC123")):
    """Show full detail of a single decision."""
    service = get_service()
    d = service.get_decision(record_id)
    if not d:
        console.print(f"[red]Decision {record_id} not found.[/red]")
        raise typer.Exit(code=1)
    console.print(f"[bold green]{d.title}[/bold green] [cyan][{d.id}][/cyan]")
    console.print(f"[dim]{d.created_at} | #{d.tag}[/dim]\n")
    console.print(f"[bold cyan]Context:[/bold cyan]\n{d.context}\n")
    console.print(f"[bold magenta]Justification:[/bold magenta]\n{d.justification}")


@cli_app.command("search")
def search_decisions(tag: str = typer.Option(..., "--tag", help="Filter by tag")):
    """Filter decisions by tag."""
    service = get_service()
    results = service.search_by_tag(tag)
    if not results:
        console.print(f"[yellow]No decisions found with tag #{tag}.[/yellow]")
        return
    table = Table(title=f"🔍 Tag: #{tag}")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Date", style="dim")
    table.add_column("Title", style="bold white")
    for d in results:
        table.add_row(d.id, d.created_at, d.title)
    console.print(table)


@cli_app.command("export")
def export_adr(filename: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (default: <export_dir>/ADR_LOG.md)")):
    """Export all decisions into a clean Markdown ADR file."""
    service = get_service()
    out = service.export_to_markdown(filename)
    console.print(f"[bold green]✔ Successfully exported ADR log to:[/bold green] [underline]{out}[/underline]")


@cli_app.command("delete")
def delete_decision(
    record_id: str = typer.Argument(..., help="Decision ID, e.g. ADR-ABC123"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a decision from the buffer (asks first, unless --yes)."""
    service = get_service()
    existing = service.get_decision(record_id)
    if existing is None:
        console.print(f"[red]Decision {record_id} not found.[/red]")
        raise typer.Exit(code=1)
    if not yes and not typer.confirm(f"Delete [{record_id}] {existing.title}?", default=False):
        console.print("[dim]Aborted. Nothing deleted.[/dim]")
        raise typer.Exit(code=0)
    service.delete_decision(record_id)
    console.print(f"[bold yellow]🗑 Deleted [{record_id}][/bold yellow] {existing.title}")


@cli_app.command("about")
def about():
    """Show the OS-ADB banner, author and creed."""
    from ui.brand import BANNER, CREED, TAGLINE

    console.print(f"[bold magenta]{BANNER}[/bold magenta]")
    console.print(f"[italic white]{TAGLINE}[/italic white]\n")
    console.print(CREED)


@cli_app.command("publish")
def publish_decision(
    record_id: str = typer.Argument(..., help="Decision ID, e.g. ADR-ABC123"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the payload without sending"),
):
    """Deliver a decision through the configured connector (n8n/slack/notion)."""
    import json

    from adapters.publishers import PublisherError

    service = get_service()
    try:
        if dry_run:
            preview = service.preview_decision(record_id)
            console.print(f"[dim]Would send to: {preview['target']}[/dim]")
            console.print(json.dumps(preview["body"], indent=2, ensure_ascii=False))
            return
        result = service.publish_decision(record_id)
    except (ValueError, PublisherError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print(f"[bold green]↗ Published [{record_id}][/bold green][dim] via {result.get('url')} (status {result.get('status')}).[/dim]")


webhook_app = typer.Typer(help="Check the n8n/slack/notion connector.")
cli_app.add_typer(webhook_app, name="webhook")


@webhook_app.command("ping")
def webhook_ping():
    """Send a test ping through the configured connector (validates credentials)."""
    from adapters.publishers import PublisherError

    service = get_service()
    try:
        result = service.ping_publisher()
    except (ValueError, PublisherError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print(f"[bold green]✔ Connector OK[/bold green][dim] ({result.get('url')}, status {result.get('status')}).[/dim]")


config_app = typer.Typer(help="Show or change OS-ADB settings (~/.adb/config.toml).")
cli_app.add_typer(config_app, name="config")

CONFIG_KEYS = ("db_path", "export_dir", "publisher", "webhook_url", "webhook_enabled", "webhook_secret", "slack_webhook_url", "notion_token", "notion_database_id")


@config_app.command("show")
def config_show():
    """Show effective settings and where they come from."""
    settings = load_settings()
    table = Table(title=f"⚙ OS-ADB Settings ({CONFIG_FILE})")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Custom", style="magenta")
    for key in CONFIG_KEYS:
        table.add_row(key, str(getattr(settings, key)), "yes" if key in settings.customized else "default")
    console.print(table)
    console.print("[dim]Env overrides: ADB_DB, ADB_EXPORT_DIR, ADB_WEBHOOK_URL, ADB_WEBHOOK_ENABLED, ADB_WEBHOOK_SECRET[/dim]")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help=f"One of: {', '.join(CONFIG_KEYS)}"),
    value: str = typer.Argument(..., help="New value"),
):
    """Persist a setting to ~/.adb/config.toml (db_path applies on next launch)."""
    if key not in CONFIG_KEYS:
        console.print(f"[red]Unknown key '{key}'. Choose from: {', '.join(CONFIG_KEYS)}[/red]")
        raise typer.Exit(code=1)
    settings = load_settings()
    if key == "webhook_enabled":
        parsed: object = value.strip().lower() in ("1", "true", "yes", "on")
    elif key == "publisher":
        parsed = value.strip().lower()
        from engine.settings import PUBLISHERS

        if parsed not in PUBLISHERS:
            console.print(f"[red]publisher must be one of: {', '.join(PUBLISHERS)}[/red]")
            raise typer.Exit(code=1)
    else:
        parsed = value
    setattr(settings, key, parsed)
    save_settings(settings)
    console.print(f"[bold green]✔ {key} = {parsed}[/bold green][dim] (saved to {CONFIG_FILE})[/dim]")
    if key == "db_path":
        console.print("[yellow]Note: the new database applies on next launch.[/yellow]")


@cli_app.command("seed")
def seed_demo():
    """Load 3 example decisions so you can try list/show/export instantly."""
    service = get_service()
    examples = [
        ("Use SQLite per Module", "Need offline-first local persistence without ops overhead.", "Eliminates cross-domain coupling and enables fast local migrations. Trade-off: no concurrent writes at scale.", "architecture"),
        ("Typer + Rich for CLI", "CLI must be sub-second and readable.", "Typer gives typing + autocompletion; Rich gives tables. Trade-off: extra deps vs argparse.", "dx"),
        ("Textual for TUI inspector", "Need keyboard inspection without leaving terminal.", "Single codebase Python TUI. Trade-off: learning curve vs web dashboard.", "ui"),
    ]
    for title, ctx, just, tag in examples:
        service.record_decision(title=title, context=ctx, justification=just, tag=tag)
    console.print("[bold green]✔ Seeded 3 demo decisions. Try: adb list[/bold green]")

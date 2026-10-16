"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Demo GIF generator: scripted, deterministic, headless. No screen recording.

  python docs/demo/generate_gifs.py [--only cli|tour|connectors]

Outputs (LinkedIn-friendly, ~100 cols, loop forever):
  docs/demo/01-cli-2segundos.gif   typer + rich in 2 seconds
  docs/demo/02-tui-tour.gif        home -> buffer -> add -> filter -> help
  docs/demo/03-connectors.gif      config screen + live webhook Test (stub)

Requires dev extras: pillow, cairosvg.
"""

import argparse
import asyncio
import io
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DEMO_DIR = Path(__file__).resolve().parent
WIDTH, HEIGHT = 100, 32

import cairosvg  # noqa: E402  (fallback only)
from PIL import Image  # noqa: E402

_CHROME = None
for _candidate in ("chromium-browser", "chromium", "google-chrome"):
    import shutil as _shutil

    if _shutil.which(_candidate):
        _CHROME = _candidate
        break

_CHROME_TMP = Path.home() / "adb_demo_frames"
_CHROME_TMP.mkdir(parents=True, exist_ok=True)


def _svg_size(svg: str) -> tuple:
    import re

    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if m:
        return int(float(m.group(1))), int(float(m.group(2)))
    return 1238, 800


def svg_to_frame(svg: str) -> Image.Image:
    """Rasterize via headless Chromium (full font/emoji fallback)."""
    import subprocess

    w, h = _svg_size(svg)
    src = _CHROME_TMP / "frame.svg"
    dst = _CHROME_TMP / "frame.png"
    src.write_text(svg, encoding="utf-8")
    if dst.exists():
        dst.unlink()
    subprocess.run(
        [_CHROME, "--headless", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", f"--window-size={w},{h}",
         f"--screenshot={dst}", f"file://{src}"],
        capture_output=True, timeout=60, check=False,
    )
    if dst.exists():
        return Image.open(dst).convert("RGB")
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), scale=1)
    return Image.open(io.BytesIO(png)).convert("RGB")


def save_gif(frames: list, durations: list, out: Path) -> None:
    assert len(frames) == len(durations)
    base_w, base_h = frames[0].size
    bg = (26, 27, 38)  # tokyo-night background
    normalized = []
    for frame in frames:
        if frame.size == (base_w, base_h):
            normalized.append(frame)
            continue
        canvas = Image.new("RGB", (base_w, base_h), bg)
        canvas.paste(frame, ((base_w - frame.width) // 2, (base_h - frame.height) // 2))
        normalized.append(canvas)
    normalized[0].save(
        out, save_all=True, append_images=normalized[1:],
        duration=durations, loop=0, optimize=True,
    )
    print(f"wrote {out} ({out.stat().st_size // 1024} KB, {len(normalized)} frames)")


# -- GIF 1: CLI -------------------------------------------------------------
def build_cli_gif(out: Path) -> None:
    from rich.console import Console

    from ui import cli as cli_mod

    tmp = tempfile.mkdtemp(prefix="adb_demo_")
    os.environ["ADB_DB"] = str(Path(tmp) / "demo.db")

    def fresh_console() -> Console:
        return Console(record=True, width=WIDTH)

    real_console = cli_mod.console
    frames, durations = [], []

    def snap(console: Console, hold_ms: int):
        svg = console.export_svg(title="OS-ADB · CLI demo")
        frames.append(svg_to_frame(svg))
        durations.append(hold_ms)

    # typing effect for the add command
    cmd = 'adb add --title "Use SQLite per Module" -j "Zero ops, git-friendly" --tag architecture'
    for i in range(4, len(cmd) + 1, 7):
        c = fresh_console()
        c.print(f"[bold green]$[/] {cmd[:i]}[blink]▌[/]")
        snap(c, 130)
    c = fresh_console()
    c.print(f"[bold green]$[/] {cmd}")
    cli_mod.console = c
    cli_mod.add_decision(title="Use SQLite per Module", justification="Zero ops, git-friendly.",
                         context="Need offline-first persistence.", tag="architecture")
    snap(c, 2400)

    # list
    c = fresh_console()
    c.print("[bold green]$[/] adb list")
    cli_mod.console = c
    cli_mod.list_decisions()
    snap(c, 2600)

    # export
    c = fresh_console()
    c.print("[bold green]$[/] adb export")
    cli_mod.console = c
    cli_mod.export_adr(os.path.join(tmp, "ADR_LOG.md"))
    snap(c, 2200)

    cli_mod.console = real_console
    save_gif(frames, durations, out)


# -- helpers for TUI gifs ----------------------------------------------------
class _StubHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, *args):
        pass


def stub_server() -> HTTPServer:
    server = HTTPServer(("127.0.0.1", 0), _StubHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


async def shot(app, pilot, hold_ms: int, frames: list, durations: list):
    await pilot.pause()
    frames.append(svg_to_frame(app.export_screenshot()))
    durations.append(hold_ms)


# -- GIF 2: TUI tour ----------------------------------------------------------
def build_tour_gif(out: Path) -> None:
    from textual.widgets import Input

    from ui.buffer_screen import BufferScreen
    from ui.home_screen import HomeScreen
    from ui.tui_app import ADBTuiApp

    async def scenario():
        from engine.adr_service import ADRService
        from adapters.sqlalchemy_repo import SQLAlchemyDecisionRepository

        tmp = tempfile.mkdtemp(prefix="adb_tour_")
        os.environ["ADB_DB"] = str(Path(tmp) / "tour.db")
        frames, durations = [], []
        app = ADBTuiApp()
        async with app.run_test(size=(WIDTH, HEIGHT)) as pilot:
            assert isinstance(app.screen, HomeScreen)
            svc = ADRService(SQLAlchemyDecisionRepository())
            svc.record_decision("Use SQLite per Module", "Need offline-first persistence.",
                                "Zero ops, git-friendly. Trade-off: no concurrent writes.", "architecture")
            svc.record_decision("Typer + Rich for CLI", "CLI must be instant.",
                                "Typing + tables. Trade-off: extra deps.", "dx")
            await shot(app, pilot, 2200, frames, durations)          # home
            await pilot.press("b")
            await shot(app, pilot, 2000, frames, durations)          # buffer
            await pilot.press("n")
            await pilot.pause()
            screen = app.screen
            screen.query_one("#f-title", Input).value = "Textual TUI inspector"
            screen.query_one("#f-context", Input).value = "Inspect without leaving the terminal."
            screen.query_one("#f-justification", Input).value = "Single codebase. Trade-off: learning curve."
            await shot(app, pilot, 2000, frames, durations)          # modal filled
            await pilot.click("#btn-save")
            await shot(app, pilot, 2200, frames, durations)          # saved toast
            assert isinstance(app.screen, BufferScreen)
            await pilot.press("/")
            await pilot.pause()
            for letter in "arch":  # live filter, letter by letter
                await pilot.press(letter)
                await shot(app, pilot, 450, frames, durations)
            await shot(app, pilot, 1800, frames, durations)          # filtered hold
            await pilot.press("escape")  # back home (clears search focus first if needed)
            await pilot.pause()
            if not isinstance(app.screen, HomeScreen):
                await pilot.press("escape")
                await pilot.pause()
            await pilot.press("?")
            await shot(app, pilot, 2600, frames, durations)          # help
        return frames, durations

    frames, durations = asyncio.run(scenario())
    save_gif(frames, durations, out)


# -- GIF 3: connectors --------------------------------------------------------
def build_connectors_gif(out: Path) -> None:
    from textual.widgets import Checkbox, Input

    from ui.home_screen import HomeScreen
    from ui.tui_app import ADBTuiApp

    async def scenario():
        tmp = tempfile.mkdtemp(prefix="adb_conn_")
        os.environ["ADB_DB"] = str(Path(tmp) / "conn.db")
        server = stub_server()
        hook = f"http://127.0.0.1:{server.server_port}/webhook/adb"
        frames, durations = [], []
        app = ADBTuiApp()
        async with app.run_test(size=(WIDTH, HEIGHT)) as pilot:
            assert isinstance(app.screen, HomeScreen)
            await shot(app, pilot, 2200, frames, durations)          # home
            from ui.dialogs import ConfigScreen

            await app.push_screen(ConfigScreen())
            await pilot.pause()
            screen = app.screen
            screen.query_one("#cfg-publisher", Input).value = "n8n"
            screen.query_one("#cfg-webhook", Input).value = hook
            screen.query_one("#cfg-enabled", Checkbox).value = True
            await shot(app, pilot, 2200, frames, durations)          # config filled
            await pilot.click("#cfg-test")
            found = False
            for _ in range(40):  # wait for the background worker
                await pilot.pause()
                try:
                    seen = str(screen.query_one("#cfg-result").render())
                except Exception:
                    seen = str(getattr(screen.query_one("#cfg-result"), "_content", ""))
                if "Connector OK" in seen:
                    found = True
                    break
            assert found, "connector Test did not succeed against the stub"
            screen.query_one("#cfg-scroll").scroll_end(animate=False)
            await shot(app, pilot, 2600, frames, durations)          # ✔ result
            server.shutdown()
        return frames, durations

    frames, durations = asyncio.run(scenario())
    frames.append(svg_to_frame(slack_mockup_svg()))
    durations.append(3200)  # hold the Slack preview
    save_gif(frames, durations, out)


def slack_mockup_svg() -> str:
    """Slack-style preview of a published ADR (mockup ilustrativo)."""
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text

    console = Console(record=True, width=100, height=15)
    side = Text("\n  os-adb demo\n\n  # general\n  # architecture\n  # incidents\n  # engineering\n", style="white on #3F0E40")
    msg = Text()
    msg.append("⬢ OS-ADB APP", style="bold white on #1A1D21")
    msg.append("  10:24 AM\n", style="#7a7a7a on #1A1D21")
    msg.append("📜 [ADR-A1B2C3] Use SQLite per Module\n", style="bold white on #1A1D21")
    msg.append("#architecture · 2026-10-16\n", style="#7a7a7a on #1A1D21")
    msg.append("Eliminates cross-domain coupling and enables fast local migrations.\n", style="white on #1A1D21")
    msg.append("Trade-off: no concurrent writes at scale.\n", style="#bbbbbb on #1A1D21")
    msg.append("💡 Context: Need offline-first local persistence, zero ops.\n\n", style="white on #1A1D21")
    msg.append("  Ver ADR  ", style="black on bright_green")
    msg.append("  ", style="on #1A1D21")
    msg.append("  Abrir en Notion  ", style="black on bright_blue")
    msg.append("  🔖 registrado con os-adb", style="#7a7a7a on #1A1D21")
    layout = Layout()
    layout.split_row(
        Layout(Panel(side, border_style="#3F0E40", style="on #3F0E40"), ratio=1, name="side"),
        Layout(
            Panel(
                msg,
                title="[bold white on #1A1D21]#architecture[/]  [dim](mockup ilustrativo)[/]",
                border_style="#444444",
                style="on #1A1D21",
            ),
            ratio=3,
            name="msg",
        ),
    )
    console.print(layout)
    return console.export_svg(title="Slack · #architecture (mockup)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["cli", "tour", "connectors"], default=None)
    args = parser.parse_args()
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    jobs = {
        "cli": (build_cli_gif, DEMO_DIR / "01-cli-2segundos.gif"),
        "tour": (build_tour_gif, DEMO_DIR / "02-tui-tour.gif"),
        "connectors": (build_connectors_gif, DEMO_DIR / "03-connectors.gif"),
    }
    for name, (fn, out) in jobs.items():
        if args.only and args.only != name:
            continue
        print(f"== {name} ==")
        fn(out)
    mockup_png = DEMO_DIR / "04-slack-mockup.png"
    svg_to_frame(slack_mockup_svg()).save(mockup_png)
    print(f"wrote {mockup_png} ({mockup_png.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Home screen: minimal landing — logo, socials, tagline, Comenzar.
Navigation hub only; all logic lives in Buffer/Engine.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label

from ui.brand import BANNER, SOCIALS, TAGLINE
from ui.dialogs import HelpScreen


class HomeScreen(Screen):
    """Landing for bare `adb`."""

    BINDINGS = [
        Binding("b", "open_buffer", "Comenzar"),
        Binding("enter", "open_buffer", "Comenzar", show=False),
        Binding("question_mark", "help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    CSS = """
    #home-card { width: 100%; height: 1fr; align: center middle; }
    #home-inner { width: auto; height: auto; }
    .home-logo { color: $primary; text-align: center; }
    .home-socials { color: $secondary; margin: 1 0 0 0; text-align: center; }
    .home-tagline { color: $text-muted; text-style: italic; margin: 0 0 2 0; text-align: center; }
    #home-start-row { width: auto; height: auto; align: center middle; }
    #home-start { width: 24; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="home-card"):
            with Vertical(id="home-inner"):
                yield Label(BANNER, classes="home-logo")
                yield Label(SOCIALS, classes="home-socials")
                yield Label(f'“{TAGLINE}”', classes="home-tagline")
                with Horizontal(id="home-start-row"):
                    yield Button("Comenzar", variant="success", id="home-start")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home-start":
            self.action_open_buffer()

    def _buffer(self) -> None:
        from ui.buffer_screen import BufferScreen

        self.app.push_screen(BufferScreen())

    def action_open_buffer(self) -> None:
        self._buffer()

    def action_help(self) -> None:
        if isinstance(self.app.screen, HelpScreen):
            return
        self.app.push_screen(HelpScreen())

    def action_quit(self) -> None:
        self.app.exit()

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

from textual.app import App

from ui.home_screen import HomeScreen


class ADBTuiApp(App):
    """Thin shell: theme + landing. Screens own the UI, Engine owns logic."""

    TITLE = "OS-ADB · Architecture Decision Buffer"
    SUB_TITLE = "Domain -> Engine -> Adapters -> UI"

    CSS = """
    Screen { background: $background; }
    .panel-header { color: $primary; text-style: bold; padding: 1 0; }
    .panel-header-blue { color: $secondary; text-style: bold; padding: 1 0; }
    """

    def __init__(self):
        super().__init__()
        self.theme = os.environ.get("ADB_THEME", "tokyo-night")

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())

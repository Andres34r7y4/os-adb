"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""

from ui.cli import cli_app


def main():
    """Bootstrap entry point for OS-ADB.

    Delegates to the Typer app; its root callback launches the TUI
    when invoked without a subcommand (bare `adb` / `python main.py`).
    """
    cli_app()


if __name__ == "__main__":
    main()

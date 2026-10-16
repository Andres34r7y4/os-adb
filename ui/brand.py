"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Brand: single source of truth for the ASCII banner and the poetic creed,
shared by the CLI (`adb about`) and the TUI help screen (key `?`).
"""

BANNER = r"""
 ██████╗ ███████╗      █████╗ ██████╗ ██████╗
██╔═══██╗██╔════╝     ██╔══██╗██╔══██╗██╔══██╗
██║   ██║███████╗     ███████║██║  ██║██████╔╝
██║   ██║╚════██║     ██╔══██║██║  ██║██╔══██╗
╚██████╔╝███████║     ██║  ██║██████╔╝██████╔╝
 ╚═════╝ ╚══════╝     ╚═╝  ╚═╝╚═════╝ ╚═════╝
"""

TAGLINE = "Ninguna decisión debería morir en un hilo de Slack."

SOCIALS = "GitHub @Andres34r7y4 · LinkedIn andresdelgado-architect"

CREED = """\
Architecture Decision Buffer — registra el porqué, no solo el qué.

  · Domain puro, Engine desacoplado, Adapters intercambiables.
  · Del terminal a Notion/Slack vía n8n en un POST.

Forjado por Andrés Delgado — Architect & Systems Factory Engineer
GitHub @Andres34r7y4 · LinkedIn andresdelgado-architect
"""

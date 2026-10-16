# 🛠️ Open Code Execution Prompt: `os-adb` (Architecture Decision Buffer)

> **Instructions for Open Code / AI Coding Assistant:**
> Please read this document carefully and construct the entire repository structure, Python files, documentation, and tests following the exact specifications, docstrings, and architectural principles outlined below.

---

## 📌 Project Context & Standards

- **Project Name:** `os-adb` (Architecture Decision Buffer)
- **Author / Architect:** Andrés Delgado
- **GitHub Profile:** [https://github.com/Andres34r7y4](https://github.com/Andres34r7y4)
- **LinkedIn Profile:** [https://www.linkedin.com/in/andresdelgado-architect/](https://www.linkedin.com/in/andresdelgado-architect/)
- **Architecture Standard:** Strict Layered Pattern (Domain → Engine → Adapters → UI)
- **Target Language/Version:** Python 3.10+
- **Primary Interface:** Dual Mode — Fast CLI (`Typer` / `Rich`) & Interactive TUI (`Textual`)

### Mandatory File Architecture
Generate the following directory tree and file contents exactly:

```text
os-adb/
├── .github/
│   └── workflows/
│       └── ci.yml
├── domain/
│   ├── __init__.py
│   └── models.py
├── engine/
│   ├── __init__.py
│   └── adr_service.py
├── adapters/
│   ├── __init__.py
│   └── sqlite_repo.py
├── ui/
│   ├── __init__.py
│   ├── cli.py
│   └── tui_app.py
├── tests/
│   ├── __init__.py
│   └── test_core.py
├── .gitignore
├── pyproject.toml
├── main.py
├── LICENSE
└── README.md
```

---

## 🐍 Module Files Specification

### 1. Header Docstring Standard
Every `.py` file **MUST** include this exact header docstring at the very top:

```python
"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""
```

---

### 2. File: `domain/models.py`
```python
"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

@dataclass
class Decision:
    """Pure Domain Entity representing an Architectural Decision Record (ADR).

    Contains ZERO external dependencies or framework imports.
    """
    title: str
    context: str
    justification: str
    tag: str = "general"
    id: str = field(default_factory=lambda: f"ADR-{str(uuid.uuid4())[:6].upper()}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

    def validate(self) -> bool:
        """Enforces domain invariants."""
        if not self.title or not self.title.strip():
            raise ValueError("Decision title cannot be empty or whitespace.")
        if not self.justification or not self.justification.strip():
            raise ValueError("Decision justification is required to ensure architectural transparency.")
        return True
```

---

### 3. File: `adapters/sqlite_repo.py`
```python
"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""

import sqlite3
from typing import List, Optional
from domain.models import Decision

class SQLiteDecisionRepository:
    """Adapter for persisting Decision entities into a local SQLite database."""

    def __init__(self, db_path: str = "adr_buffer.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    context TEXT NOT NULL,
                    justification TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    def save(self, decision: Decision) -> Decision:
        decision.validate()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO decisions (id, title, context, justification, tag, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.id,
                    decision.title,
                    decision.context,
                    decision.justification,
                    decision.tag,
                    decision.created_at,
                )
            )
        return decision

    def get_all(self) -> List[Decision]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, context, justification, tag, created_at FROM decisions ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            return [
                Decision(
                    id=row[0],
                    title=row[1],
                    context=row[2],
                    justification=row[3],
                    tag=row[4],
                    created_at=row[5],
                )
                for row in rows
            ]

    def get_by_id(self, record_id: str) -> Optional[Decision]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, context, justification, tag, created_at FROM decisions WHERE id = ?",
                (record_id,),
            )
            row = cursor.fetchone()
            if row:
                return Decision(
                    id=row[0],
                    title=row[1],
                    context=row[2],
                    justification=row[3],
                    tag=row[4],
                    created_at=row[5],
                )
            return None
```

---

### 4. File: `engine/adr_service.py`
```python
"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""

from typing import List, Optional
from domain.models import Decision

class ADRService:
    """Engine / Use-case Orchestrator for Architecture Decision Buffer.

    Decouples UI mechanisms from storage mechanisms via repository injection.
    """

    def __init__(self, repository):
        self.repository = repository

    def record_decision(self, title: str, context: str, justification: str, tag: str = "general") -> Decision:
        decision = Decision(title=title, context=context, justification=justification, tag=tag)
        return self.repository.save(decision)

    def list_decisions( me) -> List[Decision]:
        return self.repository.get_all()

    def get_decision(self, record_id: str) -> Optional[Decision]:
        return self.repository.get_by_id(record_id)

    def export_to_markdown(self, output_path: str = "ADR_LOG.md") -> str:
        decisions = self.repository.get_all()
        
        md_content = "# 📜 Architecture Decision Records (ADR Log)\n\n"
        md_content += "> Automatically generated by **OS-ADB** (Architecture Decision Buffer)\n\n"
        md_content += "---\n\n"

        if not decisions:
            md_content += "*No architectural decisions recorded yet.*\n"
        else:
            for d in decisions:
                md_content += f"## [{d.id}] {d.title}\n"
                md_content += f"- **Date:** `{d.created_at}` | **Tag:** `#{d.tag}`\n\n"
                md_content += f"### 💡 Context\n{d.context}\n\n"
                md_content += f"### ⚖️ Justification & Trade-offs\n{d.justification}\n\n"
                md_content += "---\n\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return output_path
```

---

### 5. File: `ui/cli.py`
```python
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
from adapters.sqlite_repo import SQLiteDecisionRepository
from engine.adr_service import ADRService

cli_app = typer.Typer(help="OS-ADB: Architecture Decision Buffer CLI")
console = Console()

def get_service() -> ADRService:
    repo = SQLiteDecisionRepository()
    return ADRService(repo)

@cli_app.command("add")
def add_decision(
    title: str = typer.Option(..., "--title", "-t", help="Title of the decision"),
    justification: str = typer.Option(..., "--justification", "-j", help="Justification/Trade-off"),
    context: str = typer.Option("Not specified", "--context", "-c", help="Context or problem statement"),
    tag: str = typer.Option("architecture", "--tag", help="Category tag"),
):
    """Record a new architectural decision in 2 seconds."""
    service = get_service()
    decision = service.record_decision(title=title, context=context, justification=justification, tag=tag)
    console.print(f"[bold green]✔ Saved Decision [/bold green][cyan][{decision.id}][/cyan]: {decision.title}")

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

@cli_app.command("export")
def export_adr(filename: str = typer.Option("ADR_LOG.md", "--output", "-o")):
    """Export all decisions into a clean Markdown ADR file."""
    service = get_service()
    out = service.export_to_markdown(filename)
    console.print(f"[bold emerald]✔ Successfully exported ADR log to:[/bold emerald] [underline]{out}[/underline]")
```

---

### 6. File: `ui/tui_app.py`
```python
"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static, Button, Input
from textual.containers import Horizontal, Vertical
from adapters.sqlite_repo import SQLiteDecisionRepository
from engine.adr_service import ADRService

class ADBTuiApp(App):
    """Interactive TUI Dashboard for Architecture Decision Records."""

    CSS = """
    Screen { background: #090D16; }
    #sidebar { width: 40%; border-right: solid #10B981; }
    #detail-panel { width: 60%; padding: 2; color: #E2E8F0; }
    .panel-header { font-weight: bold; color: #10B981; padding: 1; }
    """

    def __init__(self):
        super().__init__()
        self.service = ADRService(SQLiteDecisionRepository())
        self.decisions = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Vertical(
                Label(" 📋 Decision Buffer Log", classes="panel-header"),
                ListView(id="decision-list"),
                id="sidebar"
            ),
            Vertical(
                Label(" 🔍 Decision Inspector", classes="panel-header"),
                Static("Select a record from the list to inspect context and trade-offs.", id="detail-panel")
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_list()

    def refresh_list(self) -> None:
        list_view = self.query_one("#decision-list", ListView)
        list_view.clear()
        self.decisions = self.service.list_decisions()
        for d in self.decisions:
            list_view.append(ListItem(Label(f"[{d.id}] {d.title}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and idx < len(self.decisions):
            d = self.decisions[idx]
            detail = self.query_one("#detail-panel", Static)
            detail.update(
                f"[bold green]{d.title}[/bold green] ({d.id})\n"
                f"[dim]Date: {d.created_at} | Tag: #{d.tag}[/dim]\n\n"
                f"[bold cyan]Context / Problem:[/bold cyan]\n{d.context}\n\n"
                f"[bold magenta]Justification & Trade-offs:[/bold magenta]\n{d.justification}"
            )
```

---

### 7. File: `main.py`
```python
"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""

import sys
from ui.cli import cli_app
from ui.tui_app import ADBTuiApp

def main():
    """Bootstrap entry point for OS-ADB.

    Executes TUI if launched without flags, or delegates to Typer CLI if subcommands exist.
    """
    if len(sys.argv) > 1:
        cli_app()
    else:
        app = ADBTuiApp()
        app.run()

if __name__ == "__main__":
    main()
```

---

### 8. File: `pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "os-adb"
version = "0.1.0"
description = "Architecture Decision Buffer — Fast CLI/TUI tool to log architectural decisions and export ADRs."
authors = [{ name = "Andrés Delgado", email = "architect@andresdelgado.dev" }]
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "textual>=0.40.0",
]

[project.scripts]
adb = "main:main"
```

---

### 9. File: `README.md`
```markdown
# 🛠️ OS-ADB: Architecture Decision Buffer

[![CI](https://github.com/Andres34r7y4/os-adb/actions/workflows/ci.yml/badge.svg)](https://github.com/Andres34r7y4/os-adb/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Architect](https://img.shields.io/badge/Architect-Andr%C3%A9s%20Delgado-purple.svg)](https://www.linkedin.com/in/andresdelgado-architect/)

> **Log architectural decisions and design trade-offs in 2 seconds directly from your terminal, without breaking your flow.**

---

## 🔴 The Problem
Important architectural choices (ADRs) get scattered across Slack threads, PR comments, or forgotten entirely. Opening heavy web tools or web browsers to record why a trade-off was made creates friction and breaks developer flow.

## 🟢 The Solution
`os-adb` is a sub-second Terminal Tool & Interactive TUI built on a **Strict Layered Pattern** (*Domain → Engine → Adapters → UI*). It persists technical decisions into local SQLite and generates markdown documentation (`ADR_LOG.md`) in one command.

---

## 💻 Visual Interfaces

### 1. Interactive TUI Mode (`Textual`)
Launch the full interactive terminal inspector:
```bash
python main.py
```

### 2. Fast CLI Mode (`Typer` / `Rich`)
Record a decision in a single line:
```bash
python main.py add --title "Use SQLite per Module" --justification "Eliminates cross-domain coupling and enables fast local migrations." --tag "architecture"
```

Export Markdown ADRs:
```bash
python main.py export --output "ADR_LOG.md"
```

---

## 🏗️ Architecture Design

`os-adb` adheres strictly to the **Systems Factory** methodology:

```text
┌─────────────────────────────────────────────────────────┐
│ 🖥️ UI LAYER (main.py, ui/cli.py, ui/tui_app.py)        │
│ Thin Interfaces (Typer CLI / Textual TUI)               │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│ ⚡ ENGINE LAYER (engine/adr_service.py)                  │
│ Orchestration & Markdown Export Use Cases               │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│ 🧩 DOMAIN LAYER (domain/models.py)                       │
│ Pure Entities & Invariants (0 External Dependencies)    │
└────────────────────────────▲────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────┐
│ 🔌 ADAPTERS LAYER (adapters/sqlite_repo.py)             │
│ Interchangeable Storage (SQLite Engine)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 👤 Author & Links

Developed by **Andrés Delgado** — *Architect & Systems Factory Engineer*
- **LinkedIn:** [andresdelgado-architect](https://www.linkedin.com/in/andresdelgado-architect/)
- **GitHub:** [@Andres34r7y4](https://github.com/Andres34r7y4)

---

## 📄 License
Distributed under the MIT License.
```
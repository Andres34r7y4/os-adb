"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Work context: "where am I standing?" — project (git), buffer stats, paths.
Read-only, stdlib only. Never touches adapters directly; talks to the Engine.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from engine.settings import load_settings


@dataclass
class WorkContext:
    project: str
    branch: str
    cwd: str
    db_path: str
    count: int
    last_id: str
    last_title: str
    export_dir: str
    publisher: str
    publisher_ok: bool


def _git_info(cwd: Path) -> tuple[str, str]:
    """Return (repo_name, branch) or fall back to the folder name."""
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        if root.returncode != 0:
            return cwd.name, ""
        repo = Path(root.stdout.strip()).name
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        return repo, branch.stdout.strip() if branch.returncode == 0 else ""
    except Exception:
        return cwd.name, ""


def get_work_context(service, cwd: Optional[Path] = None) -> WorkContext:
    cwd = cwd or Path.cwd()
    project, branch = _git_info(cwd)
    try:
        decisions = service.list_decisions()
    except Exception:
        decisions = []
    settings = load_settings()
    try:
        from adapters.publishers import make_publisher

        make_publisher(settings)
        publisher_ok = True
    except ValueError:
        publisher_ok = False
    last = decisions[0] if decisions else None
    repo = getattr(service, "repository", service)
    return WorkContext(
        project=project,
        branch=branch,
        cwd=str(cwd),
        db_path=getattr(repo, "db_path", ""),
        count=len(decisions),
        last_id=last.id if last else "",
        last_title=last.title if last else "",
        export_dir=settings.export_dir,
        publisher=settings.publisher,
        publisher_ok=publisher_ok,
    )

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

"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

Ports (dependency-inversion): the Engine depends on this Protocol, never on a
concrete adapter. Any storage backend (SQLAlchemy, Postgres, in-memory)
satisfies the port as long as it implements these three use-cases.
"""

from typing import List, Optional, Protocol, runtime_checkable

from domain.models import Decision


@runtime_checkable
class DecisionRepository(Protocol):
    """Storage port for Decision aggregates."""

    def save(self, decision: Decision) -> Decision: ...
    def get_all(self) -> List[Decision]: ...
    def get_by_id(self, record_id: str) -> Optional[Decision]: ...
    def delete(self, record_id: str) -> bool:
        """Remove a decision. Returns True if something was deleted."""
        ...

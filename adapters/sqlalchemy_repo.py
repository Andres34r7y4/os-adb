"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================

SQLAlchemy adapter: the ONLY layer allowed to import the ORM. The ORM-mapped
row (_DecisionRow) is private to this module; every public method translates
to/from the pure domain entity (domain.models.Decision). No SQL strings.
"""

from pathlib import Path
from typing import List, Optional

from sqlalchemy import String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from domain.models import Decision


class _Base(DeclarativeBase):
    pass


class _DecisionRow(_Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    tag: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)


def _to_domain(row: _DecisionRow) -> Decision:
    return Decision(
        id=row.id,
        title=row.title,
        context=row.context,
        justification=row.justification,
        tag=row.tag,
        created_at=row.created_at,
    )


def _from_domain(decision: Decision) -> _DecisionRow:
    return _DecisionRow(
        id=decision.id,
        title=decision.title,
        context=decision.context,
        justification=decision.justification,
        tag=decision.tag,
        created_at=decision.created_at,
    )


class SQLAlchemyDecisionRepository:
    """Adapter persisting Decision entities via SQLAlchemy (SQLite by default).

    Receives its database path explicitly (composition root wires it).
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        parent = Path(self.db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(f"sqlite:///{Path(self.db_path).resolve()}")
        _Base.metadata.create_all(self._engine)

    def _session(self) -> Session:
        return Session(self._engine)

    def save(self, decision: Decision) -> Decision:
        decision.validate()
        with self._session() as session:
            session.add(_from_domain(decision))
            session.commit()
        return decision

    def get_all(self) -> List[Decision]:
        with self._session() as session:
            rows = session.scalars(
                select(_DecisionRow).order_by(_DecisionRow.created_at.desc())
            ).all()
            return [_to_domain(r) for r in rows]

    def get_by_id(self, record_id: str) -> Optional[Decision]:
        with self._session() as session:
            row = session.get(_DecisionRow, record_id)
            return _to_domain(row) if row is not None else None

    def delete(self, record_id: str) -> bool:
        with self._session() as session:
            row = session.get(_DecisionRow, record_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    def find_by_tag(self, tag: str) -> List[Decision]:
        """ORM-level filter, case-insensitive (used by the Engine)."""
        with self._session() as session:
            rows = session.scalars(
                select(_DecisionRow)
                .where(func.lower(_DecisionRow.tag) == tag.strip().lower())
                .order_by(_DecisionRow.created_at.desc())
            ).all()
            return [_to_domain(r) for r in rows]

"""SQLAlchemy ORM models for persisted review records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class ReviewRecord(Base):
    """Stores a single review request/response pair as jsonb."""

    __tablename__ = "review_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    object_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    request_payload: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB,
        nullable=False,
    )
    response_payload: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<ReviewRecord id={self.id} created_at={self.created_at}>"


class ReviewHistoryRecord(Base):
    """Stores a review history entry with summary metadata and full response."""

    __tablename__ = "review_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
        index=True,
    )
    review_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    artifact_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    code_snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    finding_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    overall_assessment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="GO",
    )
    full_response: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB,
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    feedbacks: Mapped[list[FindingFeedback]] = relationship(
        "FindingFeedback",
        back_populates="review",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewHistoryRecord id={self.id} "
            f"review_type={self.review_type} "
            f"assessment={self.overall_assessment}>"
        )


class FindingFeedback(Base):
    """Stores per-finding feedback (helpful / not helpful)."""

    __tablename__ = "finding_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("review_history.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    finding_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    rule_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    helpful: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
    )

    review: Mapped[ReviewHistoryRecord] = relationship(
        "ReviewHistoryRecord",
        back_populates="feedbacks",
    )

    def __repr__(self) -> str:
        return (
            f"<FindingFeedback id={self.id} "
            f"review_id={self.review_id} "
            f"finding_index={self.finding_index} "
            f"helpful={self.helpful}>"
        )

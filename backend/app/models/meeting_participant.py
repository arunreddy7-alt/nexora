from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="invited",
        nullable=False,
    )

    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    meeting = relationship(
        "Meeting",
        back_populates="participants",
    )

    user = relationship(
        "User",
        back_populates="meeting_participations",
    )
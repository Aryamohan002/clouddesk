from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    description = Column(Text, nullable=False)

    priority = Column(String, nullable=False)

    status = Column(
        String,
        nullable=False,
        default="Open"
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    assigned_to = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    # When the ticket was created
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # When the ticket was last updated
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_tickets"
    )

    assignee = relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="assigned_tickets"
    )

    comments = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )
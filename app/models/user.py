from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    # Role relationship
    role = relationship("Role", back_populates="users")

    # Tickets created by this user
    created_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.created_by",
        back_populates="creator"
    )

    # Tickets assigned to this user
    assigned_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_to",
        back_populates="assignee"
    )
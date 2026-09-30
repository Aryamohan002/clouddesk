from datetime import datetime

from pydantic import BaseModel, field_validator


class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str
    assigned_to: int | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value):
        allowed_priorities = [
            "Low",
            "Medium",
            "High",
            "Critical"
        ]

        if value not in allowed_priorities:
            raise ValueError(
                "Priority must be one of: Low, Medium, High, Critical"
            )

        return value


class TicketUpdate(BaseModel):
    title: str
    description: str
    priority: str
    status: str
    assigned_to: int | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value):
        allowed_priorities = [
            "Low",
            "Medium",
            "High",
            "Critical"
        ]

        if value not in allowed_priorities:
            raise ValueError(
                "Priority must be one of: Low, Medium, High, Critical"
            )

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        allowed_statuses = [
            "Open",
            "In Progress",
            "Resolved",
            "Closed"
        ]

        if value not in allowed_statuses:
            raise ValueError(
                "Status must be one of: Open, In Progress, Resolved, Closed"
            )

        return value


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    status: str
    created_by: int
    assigned_to: int | None = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tickets import Ticket
from app.models.user import User

from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse
)

from app.utils.security import (
    get_current_user,
    require_role
)


router = APIRouter()


# =========================================================
# CREATE TICKET
# =========================================================

@router.post(
    "/tickets",
    response_model=TicketResponse
)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Check assigned user
    if ticket.assigned_to is not None:

        assignee = db.query(User).filter(
            User.id == ticket.assigned_to
        ).first()

        if assignee is None:
            raise HTTPException(
                status_code=404,
                detail="Assigned user not found"
            )

        if assignee.role.name != "IT Support":
            raise HTTPException(
                status_code=400,
                detail="Ticket can only be assigned to IT Support"
            )

    new_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        status="Open",
        created_by=current_user.id,
        assigned_to=ticket.assigned_to
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


# =========================================================
# GET ALL TICKETS
#
# Optional filters:
#
# /tickets
# /tickets?status=Open
# /tickets?priority=High
# /tickets?status=Open&priority=High
# =========================================================

@router.get(
    "/tickets",
    response_model=list[TicketResponse]
)
def get_tickets(
    status: str | None = Query(
        default=None
    ),
    priority: str | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    query = db.query(Ticket)

    # User can only see their own tickets
    if current_user.role.name == "User":

        query = query.filter(
            Ticket.created_by == current_user.id
        )

    # Filter by status
    if status is not None:

        allowed_statuses = [
            "Open",
            "In Progress",
            "Resolved",
            "Closed"
        ]

        if status not in allowed_statuses:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Status must be one of: "
                    "Open, In Progress, Resolved, Closed"
                )
            )

        query = query.filter(
            Ticket.status == status
        )

    # Filter by priority
    if priority is not None:

        allowed_priorities = [
            "Low",
            "Medium",
            "High",
            "Critical"
        ]

        if priority not in allowed_priorities:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Priority must be one of: "
                    "Low, Medium, High, Critical"
                )
            )

        query = query.filter(
            Ticket.priority == priority
        )

    tickets = query.all()

    return tickets


# =========================================================
# GET ONE TICKET
# =========================================================

@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if current_user.role.name == "User":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You can only view your own tickets"
            )

    return ticket


# =========================================================
# UPDATE TICKET
# IT Support + Admin
# =========================================================

@router.put(
    "/tickets/{ticket_id}",
    response_model=TicketResponse
)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("IT Support", "Admin")
    )
):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # Validate assigned user
    if ticket_data.assigned_to is not None:

        assignee = db.query(User).filter(
            User.id == ticket_data.assigned_to
        ).first()

        if assignee is None:

            raise HTTPException(
                status_code=404,
                detail="Assigned user not found"
            )

        if assignee.role.name != "IT Support":

            raise HTTPException(
                status_code=400,
                detail="Ticket can only be assigned to IT Support"
            )

    ticket.title = ticket_data.title
    ticket.description = ticket_data.description
    ticket.priority = ticket_data.priority
    ticket.status = ticket_data.status
    ticket.assigned_to = ticket_data.assigned_to

    db.commit()
    db.refresh(ticket)

    return ticket


# =========================================================
# DELETE TICKET
# =========================================================

@router.delete(
    "/tickets/{ticket_id}"
)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # User → own ticket only
    if current_user.role.name == "User":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You can only delete your own tickets"
            )

    # IT Support → cannot delete
    elif current_user.role.name == "IT Support":

        raise HTTPException(
            status_code=403,
            detail="IT Support cannot delete tickets"
        )

    # Admin → any ticket
    elif current_user.role.name == "Admin":

        pass

    else:

        raise HTTPException(
            status_code=403,
            detail="Invalid role"
        )

    db.delete(ticket)
    db.commit()

    return {
        "message": "Ticket deleted successfully"
    }
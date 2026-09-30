from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.comment import TicketComment
from app.models.tickets import Ticket
from app.models.user import User

from app.schemas.comment import (
    CommentCreate,
    CommentResponse
)

from app.utils.security import require_role


router = APIRouter()


# =========================================================
# CREATE COMMENT
#
# IT Support → Can comment
# Admin      → Can comment
# User       → Cannot comment
# =========================================================

@router.post(
    "/tickets/{ticket_id}/comments",
    response_model=CommentResponse
)
def create_comment(
    ticket_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("IT Support", "Admin")
    )
):

    # Check whether ticket exists
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # Create comment
    new_comment = TicketComment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        comment=comment_data.comment
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {
        "id": new_comment.id,
        "ticket_id": new_comment.ticket_id,
        "user_id": new_comment.user_id,
        "user_name": current_user.name,
        "comment": new_comment.comment,
        "created_at": new_comment.created_at
    }


# =========================================================
# GET COMMENTS
#
# User       → Can view comments on their own ticket
# IT Support → Can view comments on any ticket
# Admin      → Can view comments on any ticket
# =========================================================

@router.get(
    "/tickets/{ticket_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("User", "IT Support", "Admin")
    )
):

    # Check whether ticket exists
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # User can only view comments
    # on their own ticket
    if current_user.role.name == "User":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You can only view comments on your own tickets"
            )

    # Get comments with users
    comments = (
        db.query(TicketComment, User)
        .join(
            User,
            TicketComment.user_id == User.id
        )
        .filter(
            TicketComment.ticket_id == ticket_id
        )
        .all()
    )

    # Build response
    result = []

    for comment, user in comments:

        result.append({
            "id": comment.id,
            "ticket_id": comment.ticket_id,
            "user_id": comment.user_id,
            "user_name": user.name,
            "comment": comment.comment,
            "created_at": comment.created_at
        })

    return result
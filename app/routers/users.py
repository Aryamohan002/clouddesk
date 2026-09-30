from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.models.tickets import Ticket
from app.models.comment import TicketComment

from app.schemas.user import UserCreate, UserResponse

from app.utils.security import (
    hash_password,
    require_role
)


router = APIRouter()


# =========================================================
# CREATE USER
# Admin only
# =========================================================

@router.post(
    "/users",
    response_model=UserResponse
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):

    # Check duplicate email
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    # Check role
    role = db.query(Role).filter(
        Role.id == user.role_id
    ).first()

    if role is None:

        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role_id=user.role_id
    )

    try:

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Could not create user. Email may already exist."
        )

    return new_user


# =========================================================
# GET ALL USERS
# Admin only
# =========================================================

@router.get(
    "/users",
    response_model=list[UserResponse]
)
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):

    users = db.query(User).all()

    return users


# =========================================================
# GET ONE USER
# Admin only
# =========================================================

@router.get(
    "/users/{user_id}",
    response_model=UserResponse
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


# =========================================================
# UPDATE USER
# Admin only
# =========================================================

@router.put(
    "/users/{user_id}",
    response_model=UserResponse
)
def update_user(
    user_id: int,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check duplicate email
    existing_user = db.query(User).filter(
        User.email == user_data.email,
        User.id != user_id
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    # Check role
    role = db.query(Role).filter(
        Role.id == user_data.role_id
    ).first()

    if role is None:

        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    user.name = user_data.name
    user.email = user_data.email
    user.password = hash_password(
        user_data.password
    )
    user.role_id = user_data.role_id

    try:

        db.commit()
        db.refresh(user)

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Could not update user. Email may already exist."
        )

    return user


# =========================================================
# DELETE USER
# Admin only
# =========================================================

@router.delete(
    "/users/{user_id}"
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):

    # Find user
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Prevent Admin from deleting their own account
    if user.id == current_user.id:

        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account"
        )

    # Check tickets created by this user
    created_tickets = db.query(Ticket).filter(
        Ticket.created_by == user_id
    ).count()

    if created_tickets > 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete this user because they "
                "have created tickets"
            )
        )

    # Check tickets assigned to this user
    assigned_tickets = db.query(Ticket).filter(
        Ticket.assigned_to == user_id
    ).count()

    if assigned_tickets > 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete this user because "
                "tickets are assigned to them"
            )
        )

    # Check comments
    comments = db.query(TicketComment).filter(
        TicketComment.user_id == user_id
    ).count()

    if comments > 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete this user because "
                "they have added comments"
            )
        )

    # Delete user
    try:

        db.delete(user)
        db.commit()

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Cannot delete this user because they are linked to existing data."
        )

    return {
        "message": "User deleted successfully"
    }
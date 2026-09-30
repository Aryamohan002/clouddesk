from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate, RoleResponse

from app.utils.security import require_role


router = APIRouter()


# =========================================================
# CREATE ROLE
# =========================================================

@router.post(
    "/roles",
    response_model=RoleResponse
)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("Admin"))
):

    existing_role = db.query(Role).filter(
        Role.name == role.name
    ).first()

    if existing_role:
        raise HTTPException(
            status_code=400,
            detail="Role already exists"
        )

    new_role = Role(
        name=role.name,
        description=role.description
    )

    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    return new_role


# =========================================================
# GET ALL ROLES
# =========================================================

@router.get(
    "/roles",
    response_model=list[RoleResponse]
)
def get_roles(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("Admin"))
):

    roles = db.query(Role).all()

    return roles


# =========================================================
# GET ONE ROLE
# =========================================================

@router.get(
    "/roles/{role_id}",
    response_model=RoleResponse
)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("Admin"))
):

    role = db.query(Role).filter(
        Role.id == role_id
    ).first()

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    return role


# =========================================================
# UPDATE ROLE
# =========================================================

@router.put(
    "/roles/{role_id}",
    response_model=RoleResponse
)
def update_role(
    role_id: int,
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("Admin"))
):

    role = db.query(Role).filter(
        Role.id == role_id
    ).first()

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # Prevent renaming built-in roles
    protected_roles = [
        "User",
        "IT Support",
        "Admin"
    ]

    if role.name in protected_roles:

        if role_data.name != role.name:

            raise HTTPException(
                status_code=400,
                detail="Built-in role names cannot be changed"
            )

    # Check duplicate role name
    existing_role = db.query(Role).filter(
        Role.name == role_data.name,
        Role.id != role_id
    ).first()

    if existing_role:
        raise HTTPException(
            status_code=400,
            detail="Role already exists"
        )

    role.name = role_data.name
    role.description = role_data.description

    db.commit()
    db.refresh(role)

    return role


# =========================================================
# DELETE ROLE
# =========================================================

@router.delete(
    "/roles/{role_id}"
)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("Admin"))
):

    role = db.query(Role).filter(
        Role.id == role_id
    ).first()

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # Protect built-in roles
    protected_roles = [
        "User",
        "IT Support",
        "Admin"
    ]

    if role.name in protected_roles:

        raise HTTPException(
            status_code=400,
            detail="Built-in roles cannot be deleted"
        )

    # Check whether users are using this role
    users_using_role = db.query(User).filter(
        User.role_id == role_id
    ).count()

    if users_using_role > 0:

        raise HTTPException(
            status_code=400,
            detail="Cannot delete this role because users are assigned to it"
        )

    db.delete(role)
    db.commit()

    return {
        "message": "Role deleted successfully"
    }
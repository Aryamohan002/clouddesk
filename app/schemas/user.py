from pydantic import BaseModel
from app.schemas.role import RoleResponse


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role_id: int


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: RoleResponse

    class Config:
        from_attributes = True
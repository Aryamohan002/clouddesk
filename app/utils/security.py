import os

from datetime import datetime, timedelta

from dotenv import load_dotenv

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from jose import jwt, JWTError

from passlib.context import CryptContext

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


# =========================
# Load Environment Variables
# =========================

load_dotenv()


# =========================
# Password Hashing
# =========================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# =========================
# JWT Settings
# =========================

SECRET_KEY = os.getenv("SECRET_KEY")
print("JWT SECRET KEY LOADED:", bool(SECRET_KEY))


if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY is not set"
    )

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30


# =========================
# JWT Authentication
# =========================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# =========================
# Get Current Logged-in User
# =========================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:

        raise credentials_exception

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if user is None:
        raise credentials_exception

    return user


# =========================
# Role-based Authorization
# =========================

def require_role(*required_roles: str):

    def role_checker(
        current_user: User = Depends(
            get_current_user
        )
    ):

        if current_user.role.name not in required_roles:

            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker
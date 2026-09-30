from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal

# Models
from app.models.user import User
from app.models.tickets import Ticket
from app.models.role import Role
from app.models.comment import TicketComment

# Routers
from app.routers import users
from app.routers import ticket
from app.routers import roles
from app.routers import auth
from app.routers import comment as comment_router

from app.utils.security import (
    get_current_user,
    hash_password
)

from dotenv import load_dotenv
import os


# =========================================================
# Load Environment Variables
# =========================================================

load_dotenv()


# =========================================================
# Create FastAPI Application
# =========================================================

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Include Routers
# =========================================================

app.include_router(users.router)

app.include_router(ticket.router)

app.include_router(roles.router)

app.include_router(auth.router)

app.include_router(comment_router.router)


# =========================================================
# Create Database Tables
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# Seed Initial Roles and Admin
# =========================================================

def seed_initial_data():

    db: Session = SessionLocal()

    try:

        # -------------------------------------------------
        # Create default roles
        # -------------------------------------------------

        default_roles = [
            {
                "name": "User",
                "description": "Normal Clouddesk user"
            },
            {
                "name": "IT Support",
                "description": "IT Support staff member"
            },
            {
                "name": "Admin",
                "description": "Clouddesk administrator"
            }
        ]

        for role_data in default_roles:

            existing_role = db.query(Role).filter(
                Role.name == role_data["name"]
            ).first()

            if existing_role is None:

                new_role = Role(
                    name=role_data["name"],
                    description=role_data["description"]
                )

                db.add(new_role)

        db.commit()


        # -------------------------------------------------
        # Find Admin role
        # -------------------------------------------------

        admin_role = db.query(Role).filter(
            Role.name == "Admin"
        ).first()

        if admin_role is None:

            raise Exception(
                "Admin role could not be created"
            )


        # -------------------------------------------------
        # Check whether Admin already exists
        # -------------------------------------------------

        admin_email = os.getenv("ADMIN_EMAIL")

        existing_admin = db.query(User).filter(
            User.email == admin_email
        ).first()


        # -------------------------------------------------
        # Create initial Admin
        # -------------------------------------------------

        if existing_admin is None:

            admin_name = os.getenv(
                "ADMIN_NAME"
            )

            admin_password = os.getenv(
                "ADMIN_PASSWORD"
            )

            if not admin_name or not admin_password or not admin_email:

                raise ValueError(
                    "ADMIN_NAME, ADMIN_EMAIL and ADMIN_PASSWORD "
                    "must be set in .env"
                )

            new_admin = User(
                name=admin_name,
                email=admin_email,
                password=hash_password(
                    admin_password
                ),
                role_id=admin_role.id
            )

            db.add(new_admin)
            db.commit()

            print(
                "Initial Admin user created successfully."
            )

        else:

            print(
                "Initial Admin user already exists."
            )

    finally:

        db.close()


# Run initial setup
seed_initial_data()


# =========================================================
# Root
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Welcome to Clouddesk"
    }


# =========================================================
# Profile
# =========================================================

@app.get("/profile")
def profile(
    current_user: User = Depends(
        get_current_user
    )
):
    return {
        "message": "You are logged in",
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.name
    }
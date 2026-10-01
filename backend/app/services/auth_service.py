"""
Business logic for registration, login, and current-user resolution.
Kept separate from the router so routes stay thin and testable.
"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password, verify_password, create_access_token


class AuthError(Exception):
    """Raised for expected auth failures (bad credentials, duplicate email, etc.)."""


def register_user(db: Session, user_in: UserCreate) -> User:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise AuthError("An account with this email already exists.")

    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("Incorrect email or password.")
    return user


def create_token_for_user(user: User) -> str:
    return create_access_token(subject=str(user.id))

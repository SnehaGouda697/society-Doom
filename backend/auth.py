"""Password hashing and JWT helpers used by the GraphQL API."""

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import User

# Set SOCIETY_DOOM_SECRET_KEY to a long random value outside local development.
SECRET_KEY = os.getenv("SOCIETY_DOOM_SECRET_KEY", "local-development-secret-change-before-deploying")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Return a one-way bcrypt hash for a plain password."""
    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a password against its stored hash."""
    try:
        return password_context.verify(plain_password, password_hash)
    except (ValueError, TypeError):
        # Invalid or legacy placeholder hashes must never authenticate.
        return False


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    """Return the matching user only when both email and password are valid."""
    user = session.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(user_id: int) -> str:
    """Create a signed access token with a one-hour expiration."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, SECRET_KEY, algorithm=ALGORITHM)


def user_from_access_token(session: Session, token: str | None) -> User | None:
    """Validate a bearer token and load its user from the database."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            return None
        user_id = int(subject)
    except (JWTError, TypeError, ValueError):
        return None
    return session.get(User, user_id)

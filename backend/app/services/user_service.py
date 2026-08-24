from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.user import User


def create_user(
    db: Session,
    name: str,
    email: str,
    password_hash: str,
) -> User:

    # Check for an existing account first
    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise ValueError(
            "An account with this email already exists."
        )

    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
    )

    db.add(user)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise ValueError(
            "An account with this email already exists."
        )

    db.refresh(user)

    return user


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:

    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )
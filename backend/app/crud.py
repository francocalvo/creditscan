import uuid
from typing import Any

from sqlmodel import Session

from app.domains.users.domain.models import User, UserCreate, UserUpdate
from app.domains.users.repository.user_repository import UserRepository
from app.models import Item, ItemCreate


# User CRUD operations have been moved to the users domain
# These functions are kept for backward compatibility

def create_user(*, session: Session, user_create: UserCreate) -> User:
    """Create a user. Delegates to the user repository."""
    repository = UserRepository(session)
    return repository.create(user_create)


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    """Update a user. Delegates to the user repository."""
    repository = UserRepository(session)
    return repository.update(db_user.id, user_in)


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Get a user by email. Delegates to the user repository."""
    repository = UserRepository(session)
    return repository.get_by_email(email)


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    """Authenticate a user. Delegates to the user repository."""
    repository = UserRepository(session)
    return repository.authenticate(email, password)


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

"""User repository implementation."""

import uuid
from functools import lru_cache
from typing import Any

from sqlmodel import Session, func, select
from sqlmodel.sql.expression import SelectOfScalar

from app.core.security import get_password_hash, verify_password
from app.domains.users.domain.errors import UserNotFoundError
from app.domains.users.domain.models import User, UserCreate, UserUpdate
from app.domains.users.domain.options import SearchOptions, SortOrder
from app.pkgs.database import get_db_session


class UserRepository:
    """Repository for users."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data: User creation data

        Returns:
            User: The created user
        """
        db_obj = User.model_validate(
            user_data, update={"hashed_password": get_password_hash(user_data.password)}
        )
        self.db_session.add(db_obj)
        self.db_session.commit()
        self.db_session.refresh(db_obj)
        return db_obj

    def get_by_id(self, user_id: uuid.UUID) -> User:
        """Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            User: The user

        Raises:
            UserNotFoundError: If user is not found
        """
        user = self.db_session.get(User, user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return user

    def get_by_email(self, email: str) -> User | None:
        """Get a user by email.

        Args:
            email: The user email

        Returns:
            User | None: The user if found, None otherwise
        """
        statement = select(User).where(User.email == email)
        return self.db_session.exec(statement).first()

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[User]:
        """List users with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply

        Returns:
            list[User]: List of users
        """
        query = select(User)

        if filters:
            for field, value in filters.items():
                if hasattr(User, field):
                    query = query.where(getattr(User, field) == value)

        result = self.db_session.exec(query.offset(skip).limit(limit))
        return list(result)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count users with optional filtering.

        Args:
            filters: Optional filters to apply

        Returns:
            int: Number of users matching the filters
        """
        query: SelectOfScalar[User] = select(User)

        if filters:
            for field, value in filters.items():
                if hasattr(User, field):
                    query = query.where(getattr(User, field) == value)

        count_q = (
            query.with_only_columns(func.count())
            .order_by(None)
            .select_from(query.get_final_froms()[0])
        )

        result = self.db_session.exec(count_q)
        for count in result:
            return count  # type: ignore
        return 0

    def update(self, user_id: uuid.UUID, user_data: UserUpdate) -> User:
        """Update a user.

        Args:
            user_id: The user ID
            user_data: User update data

        Returns:
            User: The updated user

        Raises:
            UserNotFoundError: If user is not found
        """
        db_user = self.get_by_id(user_id)

        user_dict = user_data.model_dump(exclude_unset=True)
        extra_data = {}

        if "password" in user_dict:
            password = user_dict["password"]
            hashed_password = get_password_hash(password)
            extra_data["hashed_password"] = hashed_password

        db_user.sqlmodel_update(user_dict, update=extra_data)
        self.db_session.add(db_user)
        self.db_session.commit()
        self.db_session.refresh(db_user)
        return db_user

    def delete(self, user_id: uuid.UUID) -> None:
        """Delete a user.

        Args:
            user_id: The user ID

        Raises:
            UserNotFoundError: If user is not found
        """
        user = self.get_by_id(user_id)
        self.db_session.delete(user)
        self.db_session.commit()

    def search(self, search_options: SearchOptions) -> list[User]:
        """Search users using advanced filtering options.

        This is a DAO-style method that supports searching and filtering
        users by multiple criteria with sorting and pagination.

        Supports:
        - Partial email matching (LIKE query)
        - Partial full name matching (LIKE query)
        - Active/inactive status filtering
        - Superuser status filtering
        - Sorting by any field
        - Pagination

        Args:
            search_options: Search options including filters, pagination, and sorting

        Returns:
            list[User]: List of users matching the search criteria
        """
        query = select(User)

        # Apply email filter (partial match using LIKE)
        if search_options.filters.email:
            email_pattern = f"%{search_options.filters.email}%"
            query = query.where(User.email.like(email_pattern))  # type: ignore

        # Apply full_name filter (partial match using LIKE)
        if search_options.filters.full_name:
            name_pattern = f"%{search_options.filters.full_name}%"
            query = query.where(User.full_name.like(name_pattern))  # type: ignore

        # Apply is_active filter
        if search_options.filters.is_active is not None:
            query = query.where(User.is_active == search_options.filters.is_active)

        # Apply is_superuser filter
        if search_options.filters.is_superuser is not None:
            query = query.where(
                User.is_superuser == search_options.filters.is_superuser
            )

        # Apply sorting
        sort_column = getattr(User, search_options.sorting.field, User.email)
        if search_options.sorting.order == SortOrder.DESC:
            query = query.order_by(sort_column.desc())  # type: ignore
        else:
            query = query.order_by(sort_column.asc())  # type: ignore

        # Apply pagination
        query = query.offset(search_options.pagination.skip).limit(
            search_options.pagination.limit
        )

        result = self.db_session.exec(query)
        return list(result)

    def count_by_search_options(self, search_options: SearchOptions) -> int:
        """Count users matching the search criteria.

        Args:
            search_options: Search options including filters

        Returns:
            int: Number of users matching the search criteria
        """
        query: SelectOfScalar[User] = select(User)

        # Apply email filter (partial match using LIKE)
        if search_options.filters.email:
            email_pattern = f"%{search_options.filters.email}%"
            query = query.where(User.email.like(email_pattern))  # type: ignore

        # Apply full_name filter (partial match using LIKE)
        if search_options.filters.full_name:
            name_pattern = f"%{search_options.filters.full_name}%"
            query = query.where(User.full_name.like(name_pattern))  # type: ignore

        # Apply is_active filter
        if search_options.filters.is_active is not None:
            query = query.where(User.is_active == search_options.filters.is_active)

        # Apply is_superuser filter
        if search_options.filters.is_superuser is not None:
            query = query.where(
                User.is_superuser == search_options.filters.is_superuser
            )

        count_q = (
            query.with_only_columns(func.count())
            .order_by(None)
            .select_from(query.get_final_froms()[0])
        )

        result = self.db_session.exec(count_q)
        for count in result:
            return count  # type: ignore
        return 0

    def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password.

        Args:
            email: The user email
            password: The user password

        Returns:
            User | None: The user if authentication successful, None otherwise
        """
        db_user = self.get_by_email(email=email)
        if not db_user:
            return None
        if not verify_password(password, db_user.hashed_password):
            return None
        return db_user


@lru_cache
def provide() -> UserRepository:
    """Provide an instance of UserRepository.

    Returns:
        UserRepository: An instance of UserRepository with a database session.
    """
    return UserRepository(get_db_session())

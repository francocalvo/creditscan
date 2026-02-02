"""User repository implementation."""

import uuid

from sqlmodel import Session, func, select
from sqlmodel.sql.expression import SelectOfScalar

from app.core.security import get_password_hash
from app.domains.users.domain.errors import UserNotFoundError
from app.domains.users.domain.models import User, UserCreate, UserUpdate
from app.domains.users.domain.options import SearchOptions, SortOrder


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

        db_user.sqlmodel_update(user_dict, update=extra_data)  # pyright: ignore[reportUnknownArgumentType]
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

        result = self.db_session.exec(count_q)  # type: ignore
        for count in result:  # type: ignore
            return count  # type: ignore
        return 0


def provide(session: Session) -> UserRepository:
    """Provide an instance of UserRepository.

    Args:
        session: The database session to use.

    Returns:
        UserRepository: An instance of UserRepository with the given session.
    """
    return UserRepository(session)

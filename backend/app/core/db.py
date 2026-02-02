from typing import TYPE_CHECKING

from sqlmodel import SQLModel

from app.core.config import settings
from app.domains.users.domain import UserCreate
from app.domains.users.service import provide as provide_user_service
from app.domains.users.usecases.create_user import provide as provide_create_user
from app.pkgs.database import get_db_session, get_engine

if TYPE_CHECKING:
    from sqlalchemy import Engine


def init_db(engine: "Engine | None" = None) -> None:
    """Initialize database with tables and first superuser.

    Args:
        engine: Optional engine to use. If not provided, uses the default engine.
    """
    if engine is None:
        engine = get_engine()

    # Import models to ensure all tables are registered with SQLModel.metadata
    import app.models  # noqa: F401  # pyright: ignore[reportUnusedImport]

    SQLModel.metadata.create_all(engine)

    session = get_db_session()
    user_service = provide_user_service(session)
    existing_user = user_service.get_user_by_email(settings.FIRST_SUPERUSER)

    if not existing_user:
        create_user_usecase = provide_create_user(session)

        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )

        create_user_usecase.execute(user_in, send_welcome_email=False)

    session.close()

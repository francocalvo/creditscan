from typing import TYPE_CHECKING

from sqlmodel import SQLModel

from app.domains.users.domain import UserCreate
from app.domains.users.service import provide as provide_user_service
from app.domains.users.usecases.create_user import provide as provide_create_user
from app.pkgs.database import get_db_session, get_engine

if TYPE_CHECKING:
    from sqlalchemy import Engine


DEFAULT_USERS = [
    {
        "email": "dev@francocalvo.ar",
        "password": "calvo123",
        "is_superuser": True,
    },
    {
        "email": "alo@gmail.com",
        "password": "alondra123",
        "is_superuser": False,
    },
]


def init_db(engine: "Engine | None" = None) -> None:
    """Initialize database with tables and default users.

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
    create_user_usecase = provide_create_user(session)

    for user_data in DEFAULT_USERS:
        existing_user = user_service.get_user_by_email(user_data["email"])  # type: ignore[arg-type]
        if not existing_user:
            user_in = UserCreate(
                email=user_data["email"],  # type: ignore[arg-type]
                password=user_data["password"],  # type: ignore[arg-type]
                is_superuser=user_data["is_superuser"],  # type: ignore[arg-type]
            )
            create_user_usecase.execute(user_in, send_welcome_email=False)

    session.close()

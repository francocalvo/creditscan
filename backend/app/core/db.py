from sqlmodel import SQLModel, create_engine

from app.core.config import settings
from app.domains.users.domain import UserCreate
from app.domains.users.service import provide as provide_user_service
from app.domains.users.usecases.create_user import provide as provide_create_user

# Convert MultiHostUrl to string properly
database_url = settings.SQLALCHEMY_DATABASE_URI
engine = create_engine(database_url.unicode_string())


def init_db() -> None:
    """Initialize database with tables and first superuser."""
    SQLModel.metadata.create_all(engine)

    user_service = provide_user_service()
    existing_user = user_service.get_user_by_email(settings.FIRST_SUPERUSER)

    if not existing_user:
        create_user_usecase = provide_create_user()

        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )

        create_user_usecase.execute(user_in, send_welcome_email=False)

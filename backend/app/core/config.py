import secrets
import warnings
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, str) or all(isinstance(i, str) for i in v):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    LEDGER_PATH: str = ""  # Path to your Beancount ledger directory
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn(
            MultiHostUrl.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME  # type: ignore[reportConstantRedefinition]
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool = False

    # S3/Garage storage configuration
    S3_ENDPOINT_URL: str = "http://localhost:3900"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "statements"
    S3_REGION: str = "us-east-1"

    # OpenRouter API configuration
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_OCR_MODELS: str = "google/gemini-flash-1.5,google/gemini-pro-1.5"
    OPENROUTER_STATEMENT_MODELS: str = "google/gemini-pro-1.5,google/gemini-pro-1.5"

    # ZAI API configuration
    ZAI_API_KEY: str = ""
    ZAI_OCR_MODELS: str = "glm-ocr,glm-ocr"
    ZAI_STATEMENT_MODELS: str = "glm-4.5-air,glm-4.5-air"

    # Extraction provider configuration (openrouter | zai)
    EXTRACTION_PROVIDER: str = "openrouter"
    EXTRACTION_OCR_PROVIDER: str = ""
    EXTRACTION_STATEMENT_PROVIDER: str = ""
    EXTRACTION_WAIT_LOG_INTERVAL_SECONDS: float = 10.0

    # Exchange rate API configuration
    EXCHANGE_RATE_API_KEY: str = ""
    CRONISTA_URL: str = "https://www.cronista.com/MercadosOnline/moneda/ARSMEP/"
    RATE_EXTRACTION_HOUR: int = 21  # UTC hour
    RATE_EXTRACTION_MINUTE: int = 0  # UTC minute

    # Ntfy notification configuration
    NTFY_INTERNAL_URL: str = "https://ntfy.sh"
    NOTIFICATION_HOUR: int = 22  # UTC hour
    NOTIFICATION_MINUTE: int = 0  # UTC minute

    @field_validator("NOTIFICATION_HOUR")
    @classmethod
    def validate_hour(cls, v: int) -> int:
        if not 0 <= v <= 23:
            raise ValueError("NOTIFICATION_HOUR must be between 0 and 23")
        return v

    @field_validator("NOTIFICATION_MINUTE")
    @classmethod
    def validate_minute(cls, v: int) -> int:
        if not 0 <= v <= 59:
            raise ValueError("NOTIFICATION_MINUTE must be between 0 and 59")
        return v

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Refuse to run with the placeholder that shipped in the repo. Anyone who
# has read the source could forge a token signed with it.
_PLACEHOLDER_SECRETS = {"SECRET_KEY", "changeme", "secret", ""}


class Settings(BaseSettings):
    # No default: the app must not start without a real signing key.
    # Set SECRET_KEY in the environment (production) or in .env (local).
    # Generate one with:  python -c "import secrets; print(secrets.token_urlsafe(48))"
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./users.db"

    # Comma-separated list of origins allowed to call the API from a browser.
    # In production the frontend is served from the same domain, so this is
    # only needed if something else calls the API cross-origin.
    CORS_ORIGINS: str = "http://localhost:3000"

    @field_validator("SECRET_KEY")
    @classmethod
    def reject_placeholder_secret(cls, value: str) -> str:
        if value.strip() in _PLACEHOLDER_SECRETS:
            raise ValueError(
                "SECRET_KEY is unset or still the placeholder value. Set a real "
                "one in the environment. Generate with: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
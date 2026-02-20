from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./ostrov.db"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Через запятую, например: https://admin.ostrov-vezeniya.ru,https://api.ostrov-vezeniya.ru
    CORS_ORIGINS_STR: str = "https://admin.ostrov-vezeniya.ru,https://api.ostrov-vezeniya.ru"

    POCHTA_API_TOKEN: str = ""
    POCHTA_LOGIN: str = ""
    POCHTA_PASSWORD: str = ""

    USD_RATE_KOPECKS: int = 9250
    MAX_PACKAGE_VALUE_USD: int = 200
    MAX_PACKAGE_WEIGHT_GRAMS: int = 30000
    DEFAULT_CUSTOMS_FEE_KOPECKS: int = 15000
    SENDER_POSTAL_CODE: str = "238311"

    POCHTA_OBJECT_CODE: int = 23030
    POCHTA_MAIL_TYPE: str = "ONLINE_PARCEL"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_must_be_strong(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be set in .env and be at least 32 characters long. "
                "Generate one with: openssl rand -hex 32"
            )
        return v


settings = Settings()

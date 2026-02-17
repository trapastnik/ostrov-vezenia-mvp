from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./ostrov.db"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

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


settings = Settings()

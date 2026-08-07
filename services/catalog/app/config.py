from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://minishop:minishop@localhost:5432/minishop"
    log_level: str = "INFO"
    db_pool_size: int = 5
    db_max_overflow: int = 5

    throttle_mode: str = ""


settings = Settings()

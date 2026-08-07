from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://minishop:minishop@localhost:5432/minishop"
    redis_url: str = "redis://localhost:6379/0"
    catalog_url: str = "http://localhost:8001"
    log_level: str = "INFO"
    db_pool_size: int = 5
    db_max_overflow: int = 5

    experiment_flag: str = ""


settings = Settings()

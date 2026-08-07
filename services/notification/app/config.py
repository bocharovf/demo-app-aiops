from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://minishop:minishop@localhost:5432/minishop"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    db_pool_size: int = 5
    db_max_overflow: int = 5

    # str, not bool: k8s ConfigMaps pass env vars as literal strings, and an
    # explicit "" (as opposed to unset) fails pydantic's bool parsing.
    cache_mode: str = ""


settings = Settings()

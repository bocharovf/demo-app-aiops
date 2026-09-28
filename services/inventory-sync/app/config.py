from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://minishop:minishop@localhost:5432/minishop"
    erp_base_url: str = "http://localhost:8080"
    log_level: str = "INFO"


settings = Settings()

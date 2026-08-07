from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    catalog_url: str = "http://localhost:8001"
    order_url: str = "http://localhost:8002"
    notification_url: str = "http://localhost:8003"
    cookie_secret: str = "minishop-demo-secret-change-me"
    log_level: str = "INFO"


settings = Settings()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {"extra": "ignore", "env_file": ".env"}
    app_name: str = "AI Stock Trading System"

settings = Settings()

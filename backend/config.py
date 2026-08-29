from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI Stock Trading System"
    google_genai_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

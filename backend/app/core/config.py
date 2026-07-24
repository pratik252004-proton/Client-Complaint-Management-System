from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "mysql+pymysql://complaint_app:projectclient369@localhost:3306/complaint_db"

    # CORS
    frontend_origin: str = "http://localhost:5173"

    # Groq / LLM 
    groq_api_key: str = ""
    groq_extraction_model: str = "gemma2-9b-it"
    groq_chat_model: str = "llama-3.3-70b-versatile"

    # App
    app_env: str = "development"
    max_upload_mb: int = 10


settings = Settings()

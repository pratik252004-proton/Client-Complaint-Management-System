from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "mysql+pymysql://complaint_app:projectclient369@localhost:3306/complaint_db"

    # CORS
    frontend_origin: str = "http://localhost:5173"

    # Groq / LLM clear

    groq_api_key: str = ""
    groq_extraction_model: str = "openai/gpt-oss-20b"
    groq_chat_model: str = "llama-3.3-70b-versatile"

    # App
    app_env: str = "development"
    max_upload_mb: int = 10


settings = Settings()

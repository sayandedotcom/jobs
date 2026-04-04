from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "jobs-aggregator/0.1.0"
    GEMINI_API_KEY: str = ""
    CRON_SECRET: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"
    APP_URL: str = ""
    VERCEL_URL: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

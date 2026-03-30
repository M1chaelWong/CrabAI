from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ANTHROPIC_API_KEY: str = ""
    LLM_BASE_URL: str | None = None  # 留空用 Anthropic 官方，填写则用兼容 API（如 Kimi）
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"  # Kimi 用 kimi-k2.5
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/crabai.db"
    UPLOAD_DIR: str = "./uploads"


settings = Settings()

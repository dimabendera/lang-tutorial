from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='./.env', env_file_encoding='utf-8', extra='ignore')

    OPENAI_API_KEY: str
    DUMMY_API_URL: str
    DUMMY_API_SECRET_KEY: str
    OPENAPI_MCP_BIN: str  # шлях до бинарника

settings = Settings()

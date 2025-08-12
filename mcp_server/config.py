from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
#  Конфігураційний модуль. Pydantic Settings дозволяє описати всі потрібні
#  змінні середовища в одному класі та автоматично зчитати їх з .env файлу.
#  Це зручно, коли у проєкті потрібно передавати секретні ключі чи URL.
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    # model_config вказує, де шукати файл зі змінними та як обробляти зайві поля.
    model_config = SettingsConfigDict(env_file='./.env', env_file_encoding='utf-8', extra='ignore')

    # Ключ до OpenAI, URL до нашого Dummy API, секретний ключ для авторизації та
    # шлях до бінарника, який перетворює OpenAPI на MCP-інструменти.
    OPENAI_API_KEY: str
    DUMMY_API_URL: str
    DUMMY_API_SECRET_KEY: str
    OPENAPI_MCP_BIN: str  # шлях до бинарника

# Ініціалізуємо глобальний об'єкт settings, який можна імпортувати з інших модулів.
settings = Settings()

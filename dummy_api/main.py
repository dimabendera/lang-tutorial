from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import os

# ---------------------------------------------------------------------------
#  Цей модуль демонструє створення невеликого REST API за допомогою FastAPI.
#  Ми будуємо сервіс з двома ресурсами (users та items), який захищений
#  простим механізмом авторизації "ключ в заголовку". Коментарі розписані
#  максимально докладно, аби програмісти, що ніколи не працювали з FastAPI,
#  зрозуміли кожен крок.
# ---------------------------------------------------------------------------

# === Налаштування авторизації =================================================
# Назва HTTP-заголовка, в якому клієнт має передавати свій API‑ключ.
API_KEY_NAME = "X-API-Key"

# Об'єкт APIKeyHeader описує, як FastAPI має шукати ключ у запиті.
#   - name: власне назва заголовка
#   - auto_error=True означає, що якщо заголовка немає, автоматично буде
#     згенерована помилка 403. Ми могли б поставити False і обробити її самостійно.
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# === Ініціалізація FastAPI =====================================================
# FastAPI створює об'єкт застосунку, який приймає вхідні HTTP‑запити і
# повертає відповіді. Аргументи title/description/version потрапляють у
# автоматично згенеровану OpenAPI-документацію (ендпоїнти /docs та /openapi.json).
app = FastAPI(
    title="Dummy Product API",
    description="Фіктивний API з авторизацією X-API-Key. Перевірте /openapi.json та /docs.",
    version="1.0.0",
)

# === Моделі даних ==============================================================
# Pydantic BaseModel дозволяє описувати структуру запитів/відповідей та
# автоматично валідує дані. Класи нижче використовуються як схеми для
# повернення інформації про користувача та товар.
class UserInfo(BaseModel):
    user_id: str
    username: str
    roles: list[str]

class Item(BaseModel):
    item_id: str
    name: str
    description: str | None = None

# === Функція перевірки ключа ===================================================
# Security(...) запускає заздалегідь сконфігурований APIKeyHeader, дістає
# значення ключа із заголовка запиту та передає його у параметр api_key.
# Ми порівнюємо його з еталонним значенням із змінної середовища.
async def get_api_key(api_key: str = Security(api_key_header)):
    expected = os.getenv("DUMMY_API_SECRET_KEY", "")
    # Якщо ключ співпадає – повертаємо його, інакше повідомляємо про помилку
    if api_key and api_key == expected:
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")

# === Кореневий ендпоїнт ========================================================
# Найпростіший маршрут, який дозволяє перевірити, що сервер працює.
@app.get("/")
def root():
    return {"message": "Welcome to Dummy API. See /docs or /openapi.json"}

# === Ендпоїнт /users/{user_id} ==================================================
# Декоратор @app.get створює HTTP GET маршрут. Параметр response_model
# повідомляє FastAPI, що відповідь має відповідати схемі UserInfo.
# Параметр tags додає ендпоїнт у відповідну групу в Swagger UI.
@app.get("/users/{user_id}", response_model=UserInfo, tags=["Users"])
async def get_user_info(user_id: str, api_key: str = Depends(get_api_key)):
    # "База даних" користувачів – звичайний словник для прикладу
    users_db = {
        "user123": {"user_id": "user123", "username": "Alice", "roles": ["admin", "user"]},
        "user456": {"user_id": "user456", "username": "Bob", "roles": ["user"]},
    }
    if user_id in users_db:
        return users_db[user_id]
    raise HTTPException(status_code=404, detail="User not found")

# === Ендпоїнт /items/{item_id} ==================================================
@app.get("/items/{item_id}", response_model=Item, tags=["Items"])
async def get_item_info(item_id: str, api_key: str = Depends(get_api_key)):
    items_db = {
        "item_abc": {"item_id": "item_abc", "name": "Laptop", "description": "A powerful machine"},
        "item_def": {"item_id": "item_def", "name": "Mouse", "description": "An ergonomic mouse"},
    }
    if item_id in items_db:
        return items_db[item_id]
    raise HTTPException(status_code=404, detail="Item not found")

# === Точка входу ===============================================================
# Якщо цей файл запускати безпосередньо (python main.py),
# ми піднімаємо веб-сервер Uvicorn. dotenv.load_dotenv() читає файл .env і
# додає змінні середовища, зручні для локального тестування.
if __name__ == "__main__":
    import uvicorn, dotenv
    dotenv.load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8001)

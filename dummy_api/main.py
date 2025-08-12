from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import os

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

app = FastAPI(
    title="Dummy Product API",
    description="Фіктивний API з авторизацією X-API-Key. Перевірте /openapi.json та /docs.",
    version="1.0.0",
)

class UserInfo(BaseModel):
    user_id: str
    username: str
    roles: list[str]

class Item(BaseModel):
    item_id: str
    name: str
    description: str | None = None

async def get_api_key(api_key: str = Security(api_key_header)):
    expected = os.getenv("DUMMY_API_SECRET_KEY", "")
    if api_key and api_key == expected:
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")


@app.get("/")
def root():
    return {"message": "Welcome to Dummy API. See /docs or /openapi.json"}


@app.get("/users/{user_id}", response_model=UserInfo, tags=["Users"])
async def get_user_info(user_id: str, api_key: str = Depends(get_api_key)):
    users_db = {
        "user123": {"user_id": "user123", "username": "Alice", "roles": ["admin", "user"]},
        "user456": {"user_id": "user456", "username": "Bob", "roles": ["user"]},
    }
    if user_id in users_db:
        return users_db[user_id]
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/items/{item_id}", response_model=Item, tags=["Items"])
async def get_item_info(item_id: str, api_key: str = Depends(get_api_key)):
    items_db = {
        "item_abc": {"item_id": "item_abc", "name": "Laptop", "description": "A powerful machine"},
        "item_def": {"item_id": "item_def", "name": "Mouse", "description": "An ergonomic mouse"},
    }
    if item_id in items_db:
        return items_db[item_id]
    raise HTTPException(status_code=404, detail="Item not found")


if __name__ == "__main__":
    import uvicorn, dotenv
    dotenv.load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8001)

import asyncio
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from .config import settings
from .storage import add, history
from .crew_runtime import run_with_mcp

# ---------------------------------------------------------------------------
#  Цей модуль запускає основний FastAPI-сервер, який інтегрує одразу кілька
#  технологій: LLM через CrewAI, механізм RAG та інструменти MCP. Кожен запит
#  від користувача обробляється послідовно, результати зберігаються в SQLite,
#  а відповідь стрімиться символ за символом. Нижче докладно пояснено кожен
#  крок – як у лекції для розробників, які вперше стикаються з цими бібліотеками.
# ---------------------------------------------------------------------------

# === Опис структури вхідного запиту ==========================================
# Pydantic BaseModel описує тіло POST-запиту. Ми очікуємо ідентифікатор клієнта
# (щоб зберігати історію) та текст повідомлення для LLM.
class ChatRequest(BaseModel):
    client_id: str
    message: str

# === Ініціалізація FastAPI ======================================================
app = FastAPI(
    title="MCP + CrewAI Server",
    description="Приймає client_id, message; стрімить відповідь; зберігає історію; використовує RAG і MCP-інструменти.",
    version="1.0.0",
)

# === Основний ендпоїнт =========================================================
# Клієнт надсилає POST /chat/stream з JSON-тілом ChatRequest і заголовком
# X-API-Key, який буде передано далі в MCP-інструмент (авторизація до Dummy API).
@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, x_api_key: str | None = Header(None)):
    # 1) Перевіряємо, що ключ присутній. FastAPI автоматично зчитує заголовок
    #    X-API-Key і передає його в параметр x_api_key.
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is required")

    # 2) Витягуємо останні 20 повідомлень із бази, щоб підтримувати контекст.
    chat_hist = history(req.client_id, limit=20)

    # 3) Запускаємо синхронну функцію run_with_mcp у пулі потоків.
    loop = asyncio.get_event_loop()
    result_text = await loop.run_in_executor(
        None,
        run_with_mcp,  # функція, що поєднує CrewAI + MCP
        req.message,
        chat_hist,
        x_api_key,
    )

    # 4) Створюємо генератор, який "друкує" відповідь поступово.
    async def generator():
        # Виводимо відповідь по символах з невеликою затримкою, імітуючи набір тексту.
        for ch in result_text:
            yield ch
            await asyncio.sleep(0.005)

        # Після завершення зберігаємо історію діалогу в базу даних.
        add(req.client_id, "user", req.message)
        add(req.client_id, "assistant", result_text)

    # 5) Повертаємо StreamingResponse, щоб клієнт міг отримувати текст у реальному часі.
    return StreamingResponse(generator(), media_type="text/plain")

# === Точка входу ===============================================================
if __name__ == "__main__":
    # Uvicorn – ASGI-сервер, який запускає наш FastAPI-додаток.
    uvicorn.run(app, host="0.0.0.0", port=8002)

import asyncio
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from .config import settings
from .storage import add, history
from .crew_runtime import run_with_mcp

app = FastAPI(
    title="MCP + CrewAI Server",
    description="Приймає client_id, message; стрімить відповідь; зберігає історію; використовує RAG і MCP-інструменти.",
    version="1.0.0",
)

class ChatRequest(BaseModel):
    client_id: str
    message: str

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, x_api_key: str | None = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is required")

    # Дістаємо історію
    chat_hist = history(req.client_id, limit=20)

    loop = asyncio.get_event_loop()

    # Запускаємо CrewAI (синхронне kickoff) у thread pool
    result_text = await loop.run_in_executor(
        None,
        run_with_mcp,
        req.message,
        chat_hist,
        x_api_key,
    )

    async def generator():
        # Простий "typewriter": по літерах
        for ch in result_text:
            yield ch
            await asyncio.sleep(0.005)

        # Після завершення — зберігаємо історію
        add(req.client_id, "user", req.message)
        add(req.client_id, "assistant", result_text)

    return StreamingResponse(generator(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)

import os
from urllib.parse import urljoin
from pathlib import Path
import requests
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

from .config import settings
from .rag import build_or_load_retriever
from .export_openapi import write_yaml_openapi

# ---------------------------------------------------------------------------
#  Тут ми поєднуємо кілька складових:
#    * RAG (retrieval-augmented generation) для підказок LLM;
#    * MCP (Model Context Protocol), що автоматично перетворює OpenAPI-ендпоїнти
#      на інструменти;
#    * CrewAI – надбудова над LLM, яка дозволяє керувати агентами та задачами.
#  Коментарі націлені на тих, хто вперше стикається з цими бібліотеками.
# ---------------------------------------------------------------------------

# === Ініціалізація LLM ========================================================
# LLM – обгортка CrewAI, яка знає як викликати модель. Параметр stream=False
# означає, що ми отримуватимемо весь текст одразу. Ключ до OpenAI беремо зі
# змінних середовища (через Settings у config.py).
llm = LLM(model="openai/gpt-4o-mini", stream=False, api_key=settings.OPENAI_API_KEY)

# === Налаштування RAG =========================================================
# build_or_load_retriever() готує індекс із локальних текстових файлів і
# повертає об'єкт, який може швидко знаходити релевантні документи.
_retriever = build_or_load_retriever()

@tool("RAG Search")
def rag_search(query: str) -> str:
    """Повертає релевантні уривки з бази знань для запиту."""
    docs = _retriever.get_relevant_documents(query)
    return "\n\n".join([f"[{i+1}] {d.page_content}" for i, d in enumerate(docs)])

# === Головна функція ==========================================================
# run_with_mcp – точка, де ми збираємо все разом: завантажуємо OpenAPI,
# піднімаємо MCP‑сервер, створюємо агента CrewAI з RAG та інструментами і
# виконуємо задачу.

def run_with_mcp(user_query: str, chat_history: list[tuple[str, str]], client_api_key: str) -> str:
    """
    Підключаємо MCP-сервер (OpenAPI -> інструменти), додаємо RAG і запускаємо Crew.
    Ключ клієнта передаємо в ENV змінній 'API_KEY' stdio-процесу MCP.
    """
    # 1) Переконуємось, що маємо локальну OpenAPI-специфікацію.
    openapi_path = "openapi.yaml"
    if not os.path.exists(openapi_path):
        spec_url = urljoin(settings.DUMMY_API_URL.rstrip("/") + "/", "openapi.json")
        resp = requests.get(spec_url, timeout=15)
        resp.raise_for_status()
        write_yaml_openapi(resp.json(), Path(openapi_path))

    # 2) Готуємо параметри запуску MCP у stdio-режимі. Тут ми передаємо
    #    базову URL нашого Dummy API та API_KEY клієнта.
    serverparams = StdioServerParameters(
        command=settings.OPENAPI_MCP_BIN,
        args=["--base-url", settings.DUMMY_API_URL, openapi_path],
        env={"API_KEY": client_api_key},
    )

    # 3) Піднімаємо MCP-адаптер, який прочитає OpenAPI та перетворить
    #    кожен operationId на інструмент, доступний нашому агенту.
    mcp_adapter = MCPServerAdapter(serverparams)
    try:
        mcp_tools = mcp_adapter.tools  # список інструментів із Dummy API
        tools = [rag_search] + mcp_tools

        # 4) Налаштовуємо агента CrewAI. Він отримує опис ролі, мети, бекграунду
        #    та список інструментів, якими може користуватися.
        agent = Agent(
            role="MCP інтегрований асистент",
            goal=(
                "Використовуй RAG для розуміння як викликати API, "
                "а потім викликай відповідні MCP-інструменти для отримання даних. "
                "Не розкривай секретні ключі; просто використовуй інструменти."
            ),
            backstory=(
                "Ти підключений до внутрішнього Dummy API через MCP, "
                "маєш базу знань і можеш робити авторизовані запити."
            ),
            llm=llm,
            tools=tools,
            allow_delegation=False,
            verbose=True,
        )

        # 5) Формуємо задачу (Task) з урахуванням попередньої історії чату.
        hist_text = "\n".join([f"{r.upper()}: {c}" for r, c in chat_history])
        task = Task(
            description=(
                "Останній запит користувача:\n"
                f"{user_query}\n\n"
                "Історія чату для контексту:\n"
                f"{hist_text}"
            ),
            expected_output="Чітка, коректна відповідь українською з використанням інструментів за потреби.",
            agent=agent,
        )

        # 6) Crew – контейнер, який запускає послідовність задач агентів.
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        return str(result)
    finally:
        # 7) Завжди закриваємо підключення до MCP, щоб не залишати висячі процеси.
        mcp_adapter.stop()

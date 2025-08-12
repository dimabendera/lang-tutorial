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

# LLM (увімкнути справжній стрімінг можна stream=True)
llm = LLM(model="openai/gpt-4o-mini", stream=False, api_key=settings.OPENAI_API_KEY)

# RAG як кастомний тул
_retriever = build_or_load_retriever()

@tool("RAG Search")
def rag_search(query: str) -> str:
    """Повертає релевантні уривки з бази знань для запиту."""
    docs = _retriever.get_relevant_documents(query)
    return "\n\n".join([f"[{i+1}] {d.page_content}" for i, d in enumerate(docs)])

def run_with_mcp(user_query: str, chat_history: list[tuple[str, str]], client_api_key: str) -> str:
    """
    Підключаємо MCP-сервер (OpenAPI -> інструменти), додаємо RAG і запускаємо Crew.
    Ключ клієнта передаємо в ENV змінній 'API_KEY' stdio-процесу MCP.
    """
    # 1) Готуємо локальну YAML-спеку, якщо її ще немає
    openapi_path = "openapi.yaml"
    if not os.path.exists(openapi_path):
        spec_url = urljoin(settings.DUMMY_API_URL.rstrip("/") + "/", "openapi.json")
        resp = requests.get(spec_url, timeout=15)
        resp.raise_for_status()
        write_yaml_openapi(resp.json(), Path(openapi_path))

    # 2) Stdio-параметри MCP: додаємо --base-url (важливо для FastAPI)
    serverparams = StdioServerParameters(
        command=settings.OPENAPI_MCP_BIN,
        args=["--base-url", settings.DUMMY_API_URL, openapi_path],
        env={"API_KEY": client_api_key},
    )

    # 3) Піднімаємо MCP-адаптер та отримуємо інструменти
    mcp_adapter = MCPServerAdapter(serverparams)
    try:
        mcp_tools = mcp_adapter.tools  # список MCP-інструментів із OpenAPI
        tools = [rag_search] + mcp_tools

        # 4) Агент CrewAI
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

        # 5) Завдання з контекстом історії
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

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        return str(result)
    finally:
        # закриваємо stdio-з’єднання з MCP
        mcp_adapter.stop()

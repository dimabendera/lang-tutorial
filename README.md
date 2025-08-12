# lang-tutorial

Приклад запуску
```bash
python -m mcp_server.main
```

Приклад Запиту
```bash
curl -N -X POST http://127.0.0.1:8002/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: MySuperSecretDummyKey" \
  -d '{"client_id":"client_001","message":"Покажи користувача user123"}'

```

Структруа проекту
```
crewai_fastapi_mcp_demo/
├─ .env
├─ requirements.txt
├─ dummy_api/
│  ├─ __init__.py
│  └─ main.py
├─ mcp_server/                 # основний FastAPI сервер (CrewAI + RAG + MCP)
│  ├─ __init__.py
│  ├─ config.py
│  ├─ storage.py
│  ├─ rag.py
│  ├─ crew_runtime.py
│  └─ main.py
├─ .env                        # Секретні ключі та налаштування
├─ requirements.txt            # Залежності проєкту
└─ README.md
```

### MCP-сервер: як автоматично перетворити OpenAPI → інструменти
#### Варіант A
(рекомендований для демо): openapi-mcp (Go-утиліта). Вона зчитує OpenAPI 3.x і миттєво перетворює кожен operationId у MCP-інструмент. Підтримує ключі API, Bearer, Basic, OAuth2; stdio/SSE/HTTP режими; флаг --base-url; env API_KEY тощо. 
https://github.com/jedisct1/openapi-mcp

Встановити Go ≥ 1.21 та зібрати:

```bash
git clone https://github.com/jedisct1/openapi-mcp
cd openapi-mcp
make
# утиліта з’явиться: bin/openapi-mcp
# додайте її у PATH або вкажіть у .env як OPENAPI_MCP_BIN=/absolute/path/to/openapi-mcp
```
Ми запускатимемо її у stdio-режимі на кожен запит та передаватимемо клієнтський API-ключ через env (API_KEY=<ключ_клієнта>). Це критично: ключ не потрапляє в промпт, лише в заголовок HTTP запиту, який робить MCP-сервер. (Саме те, що ви хотіли.) 
GitHub

#### Альтернатива B 
(Node.js ≥ 20): openapi-mcp-generator — генерує готовий MCP-сервер (TypeScript) з вашого OpenAPI; підтримує stdio/SSE/StreamableHTTP і різні схеми авторизації з env-змінних типу API_KEY_<SCHEME_NAME>. Підійде, якщо вам зручніший JS-стек або потрібен веб-режим. 
GitHub
https://github.com/harsha-iiiv/openapi-mcp-generator
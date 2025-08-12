import sqlite3
from pathlib import Path
from typing import Iterable, Tuple

# ---------------------------------------------------------------------------
#  Просте сховище історії повідомлень на SQLite. Ми зберігаємо кожне
#  повідомлення (роль + текст) разом із client_id. Це дозволяє відновлювати
#  контекст діалогу при наступних запитах.
# ---------------------------------------------------------------------------

# Шлях до файлу бази даних: лежить поруч із цим модулем.
_DB = Path(__file__).parent / "chat.db"

# Під час імпорту модуля створюємо таблицю, якщо її ще немає.
def _init():
    with sqlite3.connect(_DB) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            role TEXT NOT NULL,        -- 'user' | 'assistant'
            content TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
_init()

# Додаємо нове повідомлення у базу.
def add(client_id: str, role: str, content: str) -> None:
    with sqlite3.connect(_DB) as con:
        con.execute("INSERT INTO messages(client_id, role, content) VALUES(?,?,?)",
                    (client_id, role, content))

# Повертаємо останні N повідомлень у вигляді [(role, content), ...]
def history(client_id: str, limit: int = 20) -> list[Tuple[str,str]]:
    with sqlite3.connect(_DB) as con:
        rows = con.execute(
            "SELECT role, content FROM messages WHERE client_id=? ORDER BY id DESC LIMIT ?",
            (client_id, limit)
        ).fetchall()
    # У SQLite вибірка йде в зворотному порядку, тому перевертаємо список.
    return list(reversed(rows))

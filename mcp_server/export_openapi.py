import typer
import yaml

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict

# ---------------------------------------------------------------------------
#  Невеликий модуль, що містить утиліти для запису OpenAPI-специфікації у
#  різні формати. Ми використовуємо його в crew_runtime, щоб зберегти
#  отриманий від Dummy API опис у локальний файл. Typer дозволяє легко
#  створювати CLI, хоча тут ми використовуємо лише функції для експорту.
# ---------------------------------------------------------------------------

class OutputTypeEnum(str, Enum):
    json = "JSON"
    yaml = "YAML"
    both = "BOTH"

# Функції нижче приймають словник з даними OpenAPI та шлях до файлу,
# після чого зберігають його як JSON або YAML. Для простоти логування
# використовується стандартний модуль logging.

def write_json_openapi(openapi: Dict[str, Any], output_path: Path) -> None:
    logging.info(f"Writing OpenAPI to {str(output_path)}")
    with output_path.open("w") as f:
        json.dump(openapi, f, indent=2)


def write_yaml_openapi(openapi: Dict[str, Any], output_path: Path) -> None:
    logging.info(f"Writing OpenAPI to {str(output_path)}")
    with output_path.open("w") as f:
        yaml.dump(openapi, f)

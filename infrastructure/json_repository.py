from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_DATA_FILE = Path(__file__).parent.parent / "data" / "tasks.json"


class JsonRepository:
    """Implementación de TaskRepositoryProtocol sobre un fichero JSON local.

    Acepta una ruta opcional para facilitar las pruebas con ficheros temporales
    sin necesidad de parchear módulos (principio D de SOLID).
    """

    def __init__(self, data_file: Path | None = None) -> None:
        self._data_file = data_file or _DEFAULT_DATA_FILE

    def load(self) -> list[dict]:
        if not self._data_file.exists():
            return []
        with self._data_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: list[dict]) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._data_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

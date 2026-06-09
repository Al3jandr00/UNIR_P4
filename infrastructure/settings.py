from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def _load_simple_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


if load_dotenv is not None:
    load_dotenv(ENV_PATH)
else:
    _load_simple_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "350"))
    openai_top_p: float = float(os.getenv("OPENAI_TOP_P", "1.0"))
    openai_system_prompt: str = os.getenv(
        "OPENAI_SYSTEM_PROMPT",
        "Eres un asistente util, claro y preciso. Responde en espanol salvo que el usuario pida otro idioma.",
    )
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_model: str = os.getenv("AZURE_OPENAI_MODEL", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    allow_local_fallback: bool = os.getenv("AI_ALLOW_LOCAL_FALLBACK", "false").lower() == "true"

    @property
    def has_openai_config(self) -> bool:
        return bool(self.openai_api_key and self.openai_model)

    @property
    def has_azure_config(self) -> bool:
        return bool(
            self.azure_openai_api_key
            and self.azure_openai_endpoint
            and self.azure_openai_model
        )


settings = Settings()

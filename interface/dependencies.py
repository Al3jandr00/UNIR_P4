from __future__ import annotations

from functools import lru_cache

from application.ai_task_service import AITaskService
from application.task_manager import TaskManager
from infrastructure.ai_provider import AIProvider
from infrastructure.json_repository import JsonRepository


@lru_cache
def get_repository() -> JsonRepository:
    """Singleton del repositorio JSON — una sola instancia por proceso."""
    return JsonRepository()


@lru_cache
def get_ai_provider() -> AIProvider:
    """Singleton del cliente LLM — evita crear múltiples conexiones HTTP."""
    return AIProvider()


def get_task_manager() -> TaskManager:
    """Proveedor de TaskManager para FastAPI Depends().

    Inyecta el repositorio singleton, cumpliendo el principio D de SOLID:
    el router no conoce JsonRepository, solo TaskManager.
    """
    return TaskManager(get_repository())


def get_ai_service() -> AITaskService:
    """Proveedor de AITaskService para FastAPI Depends().

    Inyecta el proveedor LLM singleton, desacoplando la capa de interfaz
    de la implementación concreta del proveedor de IA.
    """
    return AITaskService(get_ai_provider())

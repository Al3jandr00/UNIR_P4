"""Fixtures compartidos para toda la suite de tests.

El cliente HTTP se construye sobrescribiendo las dependencias de FastAPI
(app.dependency_overrides) en lugar de parchear módulos. Esto sigue el
principio D de SOLID y hace los tests independientes de la implementación
concreta de repositorio y proveedor LLM.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from application.ai_task_service import AITaskService
from application.task_manager import TaskManager
from infrastructure.json_repository import JsonRepository
from interface.dependencies import get_ai_service, get_task_manager
from main import app


class _DummyProvider:
    """Proveedor LLM de prueba — sustituible gracias a AIProviderProtocol."""

    def generate_description(self, task_data: dict) -> str:
        return "Descripcion generada"

    def categorize_task(self, task_data: dict) -> str:
        return "Backend"

    def estimate_effort(self, task_data: dict) -> float:
        return 6.5

    def analyze_risks(self, task_data: dict) -> str:
        return "Riesgo de dependencias."

    def generate_mitigation(self, task_data: dict, risk_analysis: str) -> str:
        return f"Mitigar: {risk_analysis}"


@pytest.fixture
def task_manager(tmp_path):
    """TaskManager con repositorio apuntando a un fichero temporal aislado."""
    return TaskManager(JsonRepository(tmp_path / "tasks_test.json"))


@pytest.fixture
def ai_service():
    """AITaskService con proveedor simulado, sin llamadas reales a LLM."""
    return AITaskService(_DummyProvider())


@pytest.fixture
def client(task_manager, ai_service):
    """TestClient de FastAPI con dependencias sobreescritas para tests.

    Limpia los overrides al finalizar cada test para evitar contaminación
    entre casos de prueba.
    """
    app.dependency_overrides[get_task_manager] = lambda: task_manager
    app.dependency_overrides[get_ai_service] = lambda: ai_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

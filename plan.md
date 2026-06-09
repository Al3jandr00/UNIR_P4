# Plan del Proyecto — Entregable 4

## Objetivo

Contenerizar la API de gestión de tareas (desarrollada en los entregables 1–3) usando
Docker y automatizar el ciclo de build, test y publicación de la imagen mediante un
pipeline de integración continua con GitHub Actions.

---

## Contexto y base de trabajo

| Entregable | Tecnología | Lo que aporta a este proyecto |
|------------|------------|-------------------------------|
| Entregable 1 | FastAPI + JSON | Arquitectura en 4 capas, CRUD de tareas |
| Entregable 2 | FastAPI + OpenAI | Endpoints de IA (describe, categorize, estimate, audit) |
| Entregable 3 | FastAPI + MySQL + Jinja2 | UI web, SQLAlchemy, historias de usuario |
| **Entregable 4** | **FastAPI + Docker + GitHub Actions** | Contenerización y CI/CD |

Se retoma la versión del Entregable 2 como base (sin base de datos externa) para
permitir un contenedor único sin dependencias de infraestructura adicionales.

---

## Pasos planificados

### Fase 1 — Aplicación base ✅

- [x] Copiar y adaptar la arquitectura de 4 capas del Entregable 2:
  - `domain/task.py` — modelo de dominio con enums `Priority` y `Status`
  - `application/task_manager.py` — lógica CRUD
  - `application/ai_task_service.py` — orquestación de IA
  - `infrastructure/settings.py` — configuración desde variables de entorno
  - `infrastructure/json_repository.py` — persistencia en fichero JSON
  - `infrastructure/ai_provider.py` — cliente LLM con soporte Azure OpenAI / OpenAI
  - `interface/routes.py` — router CRUD `/tasks`
  - `interface/ai_routes.py` — router IA `/ai/tasks`
- [x] Añadir `GET /` con mensaje de bienvenida (requisito del entregable)
- [x] Crear `main.py` con la aplicación FastAPI y uvicorn

### Fase 2 — Mejoras SOLID y buenas prácticas ✅

- [x] **Principio I / D** — Añadir `infrastructure/protocols.py` con `TaskRepositoryProtocol`
  y `AIProviderProtocol` para formalizar los contratos entre capas
- [x] **Principio D** — Refactorizar `TaskManager` a clase orientada a instancias con
  inyección del repositorio por constructor (eliminar el singleton de módulo `_repository`)
- [x] **Principio D** — Refactorizar `AITaskService` para requerir el proveedor
  explícitamente; eliminar el parámetro opcional `provider=None`
- [x] **FastAPI DI** — Crear `interface/dependencies.py` con proveedores de dependencias
  (`get_task_manager`, `get_ai_service`) usando `Depends()` y `@lru_cache`
- [x] **Principio D en rutas** — Refactorizar routers para recibir `TaskManager` y
  `AITaskService` como parámetros inyectados (`Annotated[..., Depends(...)]`)
- [x] **Seguridad** — Actualizar `Dockerfile` para ejecutar la aplicación con usuario
  no-root (`appuser`) en lugar de `root`

### Fase 3 — Contenerización ✅

- [x] Crear `Dockerfile` con:
  - Imagen base `python:3.12-slim`
  - Instalación de dependencias desde `requirements.txt`
  - Copia del código fuente
  - Creación del directorio `data/`
  - Usuario no privilegiado `appuser`
  - Exposición del puerto `8000`
  - Comando de arranque con uvicorn
- [x] Crear `.dockerignore` (excluye `venv/`, `tests/`, `.env`, `__pycache__/`, `.git/`)
- [x] Verificar build local: `docker build -t task-manager-api .`
- [x] Verificar ejecución: `docker run -p 8000:8000 task-manager-api`

### Fase 4 — Pipeline CI/CD ✅

- [x] Crear `.github/workflows/docker-ci.yml` con dos jobs secuenciales:
  - **`test`**: checkout → setup Python 3.12 → install deps → `pytest tests/ -v`
  - **`docker-build-push`**: checkout → login Docker Hub → build + push (tags `latest` y SHA)
- [x] Pipeline se activa en `push` y `pull_request` sobre la rama `main`
- [x] El job de publicación solo se ejecuta en `push` a `main` (no en PRs)
- [x] Documentar configuración de secretos `DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN`

### Fase 5 — Tests ✅

- [x] Crear `tests/conftest.py` con fixtures compartidos:
  - `task_manager(tmp_path)` — inyecta repositorio temporal aislado
  - `ai_service()` — inyecta `DummyProvider` sin llamadas LLM reales
  - `client(task_manager, ai_service)` — `TestClient` con `app.dependency_overrides`
- [x] Actualizar `tests/test_task_manager.py` — inyección directa de Mock en constructor
  (sin `@patch` de variables de módulo)
- [x] Actualizar `tests/test_ai_task_service.py` — pruebas de servicio y casos de error
- [x] Actualizar `tests/test_routes.py` — tests de integración con DI overrides
- [x] Mantener `tests/test_task.py` — tests unitarios del modelo de dominio
- [x] Verificar **50/50 tests pasando** en 0.27s

### Fase 6 — Publicación en GitHub y Docker Hub ✅

- [x] Crear repositorio público en GitHub: https://github.com/Al3jandr00/UNIR_P4
- [x] Configurar secretos `DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN` en GitHub
- [x] Push inicial → pipeline Run #1 detectó error de compatibilidad de Starlette
- [x] Fix: `HTTP_422_UNPROCESSABLE_CONTENT` → `HTTP_422_UNPROCESSABLE_ENTITY` (estándar compatible)
- [x] Push del fix → pipeline Run #2 completado ✅ (50/50 tests + imagen publicada)
- [x] Imagen disponible en Docker Hub: `alejandrofral/task-manager-api:latest`

### Fase 7 — Documentación ✅

- [x] Actualizar `README.md` con URLs reales (GitHub + Docker Hub)
- [x] Crear `plan.md` (este fichero) con la planificación y seguimiento completo
- [x] Crear `memoria_tecnica.md` con la narrativa técnica completa para el examinador

---

## Verificación final contra la rúbrica del entregable

| Criterio | Requisito | Estado |
|----------|-----------|--------|
| Creación del Dockerfile | Imagen base Python, `requirements.txt`, puerto expuesto, comando de ejecución | ✅ |
| Configuración del pipeline | Etapas de build, test y push claramente definidas | ✅ |
| Automatización de pruebas | `pytest` ejecutado dentro del pipeline antes del build | ✅ |
| Subida al registro | Imagen publicada en Docker Hub (`alejandrofral/task-manager-api`) | ✅ |
| Documentación en README.md | Instrucciones claras de ejecución con Docker | ✅ |

---

## Decisiones técnicas relevantes

| Decisión | Alternativa descartada | Motivo |
|----------|------------------------|--------|
| FastAPI (no Flask) | Flask (indicado en el enunciado) | Coherencia con los 3 entregables anteriores |
| Puerto 8000 | Puerto 5000 (Flask) | Puerto estándar de uvicorn / FastAPI |
| Contenedor único | docker-compose con MySQL | El entregable pide un solo Dockerfile; la persistencia JSON no requiere DB externa |
| `python:3.12-slim` | Alpine | Menor superficie de ataque que Debian completo, mayor compatibilidad que Alpine |
| Usuario `appuser` (no-root) | Usuario `root` | Buena práctica de seguridad en contenedores |
| `@lru_cache` para singletons | Lifespan de FastAPI | Sencillez sin sacrificar el desacoplamiento para tests |

---

## Estructura final del proyecto

```
Proyecto 4/
├── domain/
│   └── task.py
├── application/
│   ├── task_manager.py
│   └── ai_task_service.py
├── infrastructure/
│   ├── protocols.py          ← NUEVO: contratos formales (Protocols)
│   ├── settings.py
│   ├── json_repository.py    ← ACTUALIZADO: acepta ruta opcional
│   └── ai_provider.py
├── interface/
│   ├── dependencies.py       ← NUEVO: proveedores de DI para FastAPI
│   ├── routes.py             ← ACTUALIZADO: usa Depends()
│   └── ai_routes.py          ← ACTUALIZADO: usa Depends()
├── data/
│   └── tasks.json
├── tests/
│   ├── conftest.py           ← NUEVO: fixtures con DI overrides
│   ├── test_task.py
│   ├── test_task_manager.py  ← ACTUALIZADO: inyección directa de mocks
│   ├── test_ai_task_service.py
│   └── test_routes.py        ← ACTUALIZADO: app.dependency_overrides
├── .github/
│   └── workflows/
│       └── docker-ci.yml
├── Dockerfile                ← ACTUALIZADO: usuario no-root
├── .dockerignore
├── requirements.txt
├── main.py
├── .env.example
├── README.md
├── plan.md                   ← NUEVO
└── memoria_tecnica.md        ← NUEVO
```

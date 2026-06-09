# Task Manager API — Entregable 4

API REST de gestión de tareas con integración de IA generativa, contenerizada con Docker y desplegada automáticamente mediante un pipeline de integración continua con GitHub Actions.

Este proyecto es la continuación directa de los entregables anteriores del módulo:

- **Entregable 1:** API FastAPI con CRUD de tareas y almacenamiento en JSON. Arquitectura en 4 capas (domain, application, infrastructure, interface).
- **Entregable 2:** Integración de endpoints de IA generativa para descripción, categorización, estimación y auditoría de tareas. Soporte para Azure OpenAI y OpenAI.
- **Entregable 3:** Base de datos MySQL, modelos SQLAlchemy, esquemas Pydantic, historias de usuario e interfaz web con Jinja2 y Bootstrap.
- **Entregable 4 (este proyecto):** Contenerización con Docker y pipeline CI/CD con GitHub Actions. Se retoma la versión del Entregable 2 (sin base de datos externa) para simplificar el despliegue en un único contenedor.

---

## Descripción del proyecto

La aplicación expone una API REST construida con **FastAPI** que permite gestionar tareas de software mediante operaciones CRUD y enriquecerlas con ayuda de un modelo de lenguaje (LLM) a través de cuatro endpoints de IA.

### Características principales

- Endpoint de bienvenida en la raíz (`GET /`) que presenta la API y lista los endpoints disponibles.
- CRUD completo de tareas (`GET`, `POST`, `PUT`, `DELETE` sobre `/tasks`).
- Endpoints de IA para generar descripciones, categorizar, estimar esfuerzo y realizar auditoría de riesgos.
- Persistencia en fichero JSON (sin dependencias externas de base de datos).
- Fallback local para los endpoints de IA cuando no hay credenciales configuradas.
- Documentación automática de la API en `/docs` (Swagger UI) y `/redoc`.
- Suite de pruebas automatizadas con **pytest**.
- Imagen Docker lista para producción basada en `python:3.12-slim`.
- Pipeline CI/CD con **GitHub Actions** que ejecuta los tests y publica la imagen en Docker Hub.

---

## Estructura del proyecto

```
Proyecto 4/
├── domain/
│   └── task.py                    # Modelo de dominio Task con enums Priority y Status
├── application/
│   ├── task_manager.py            # Lógica de negocio CRUD de tareas
│   └── ai_task_service.py         # Orquestación de los servicios de IA
├── infrastructure/
│   ├── settings.py                # Configuración desde variables de entorno
│   ├── json_repository.py         # Acceso al fichero JSON de persistencia
│   └── ai_provider.py             # Cliente LLM con soporte Azure OpenAI / OpenAI y fallback local
├── interface/
│   ├── routes.py                  # Router CRUD /tasks
│   └── ai_routes.py               # Router IA /ai/tasks
├── data/
│   └── tasks.json                 # Almacenamiento persistente de tareas
├── tests/
│   ├── test_task.py               # Tests unitarios del modelo Task
│   ├── test_task_manager.py       # Tests unitarios del TaskManager
│   ├── test_ai_task_service.py    # Tests unitarios del AITaskService
│   └── test_routes.py             # Tests de integración de todos los endpoints
├── .github/
│   └── workflows/
│       └── docker-ci.yml          # Pipeline GitHub Actions
├── Dockerfile                     # Imagen Docker de la aplicación
├── .dockerignore
├── requirements.txt
├── main.py                        # Punto de entrada FastAPI con saludo en /
└── .env.example                   # Plantilla de variables de entorno
```

---

## Requisitos previos

- **Docker** instalado y en ejecución.
- **Python 3.12** (solo para desarrollo local sin Docker).
- Cuenta en **Docker Hub** (para publicar la imagen desde el pipeline).
- Cuenta en **GitHub** con acceso a configurar Secrets (para el pipeline).

---

## Ejecución con Docker

### 1. Construir la imagen

```bash
docker build -t task-manager-api .
```

### 2. Ejecutar el contenedor

Sin credenciales de IA (los endpoints `/ai/tasks/*` devolverán 503 salvo activar el fallback):

```bash
docker run -p 8000:8000 task-manager-api
```

Con credenciales de OpenAI:

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e OPENAI_MODEL=gpt-4o-mini \
  task-manager-api
```

Con credenciales de Azure OpenAI:

```bash
docker run -p 8000:8000 \
  -e AZURE_OPENAI_API_KEY=... \
  -e AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com \
  -e AZURE_OPENAI_MODEL=gpt-4o-mini \
  task-manager-api
```

### 3. Verificar que la aplicación responde

```bash
curl http://localhost:8000/
```

Respuesta esperada:

```json
{
  "message": "Bienvenido a la API de Gestión de Tareas",
  "version": "4.0.0",
  "descripcion": "...",
  "docs": "/docs",
  "endpoints": { ... }
}
```

La documentación interactiva estará disponible en `http://localhost:8000/docs`.

---

## Ejecución local (sin Docker)

```bash
# Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# Instalar dependencias
pip install -r requirements.txt

# Copiar y configurar variables de entorno
cp .env.example .env

# Ejecutar la aplicación
python main.py
```

La API estará disponible en `http://localhost:8000`.

---

## Endpoints de la API

### Bienvenida

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/`  | Mensaje de bienvenida con listado de endpoints disponibles |

### CRUD de Tareas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/tasks` | Listar todas las tareas |
| POST   | `/tasks` | Crear una nueva tarea |
| GET    | `/tasks/{id}` | Obtener una tarea por ID |
| PUT    | `/tasks/{id}` | Actualizar una tarea existente |
| DELETE | `/tasks/{id}` | Eliminar una tarea |

#### Modelo de tarea (POST/PUT body)

```json
{
  "title": "Implementar autenticación JWT",
  "description": "Crear sistema de autenticación con tokens JWT",
  "priority": "alta",
  "effort_hours": 8.0,
  "status": "pendiente",
  "assigned_to": "Ana García",
  "category": "Seguridad",
  "risk_analysis": "",
  "risk_mitigation": ""
}
```

Valores válidos para `priority`: `baja`, `media`, `alta`, `bloqueante`.  
Valores válidos para `status`: `pendiente`, `en progreso`, `en revisión`, `completada`.

### Endpoints de IA

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST   | `/ai/tasks/describe`   | Genera la descripción de una tarea a partir de su título y otros campos |
| POST   | `/ai/tasks/categorize` | Clasifica la tarea en una categoría: Frontend, Backend, Testing, Infra, etc. |
| POST   | `/ai/tasks/estimate`   | Estima el esfuerzo en horas a partir del título, descripción y categoría |
| POST   | `/ai/tasks/audit`      | Genera el análisis de riesgos y el plan de mitigación de la tarea |

---

## Pipeline de integración continua (GitHub Actions)

El fichero `.github/workflows/docker-ci.yml` define dos jobs que se ejecutan de forma secuencial:

### Job `test` — Pruebas automatizadas

Se ejecuta en cada `push` y `pull_request` sobre la rama `main`:

1. Descarga el código (`actions/checkout@v4`).
2. Configura Python 3.12 (`actions/setup-python@v5`).
3. Instala las dependencias con `pip install -r requirements.txt`.
4. Ejecuta la suite de tests con `pytest tests/ -v` (con `AI_ALLOW_LOCAL_FALLBACK=true`).

### Job `docker-build-push` — Construcción y publicación de la imagen

Se ejecuta solo en `push` a `main`, tras el job `test`:

1. Descarga el código.
2. Se autentica en Docker Hub con los secretos configurados.
3. Construye la imagen Docker y la publica con dos tags:
   - `latest`
   - El SHA del commit (`${{ github.sha }}`)

### Configuración de secretos en GitHub

Para que el pipeline pueda publicar en Docker Hub, configura dos secretos en el repositorio (`Settings → Secrets and variables → Actions → New repository secret`):

| Secret | Valor |
|--------|-------|
| `DOCKERHUB_USERNAME` | Tu nombre de usuario en Docker Hub |
| `DOCKERHUB_TOKEN`    | Token de acceso generado en Docker Hub (`Account Settings → Security → New Access Token`) |

---

## Ejecución de los tests

```bash
# Instalar dependencias (si no están instaladas)
pip install -r requirements.txt

# Ejecutar todos los tests
pytest tests/ -v

# Con fallback de IA activado (necesario para los tests que prueban el proveedor de IA)
AI_ALLOW_LOCAL_FALLBACK=true pytest tests/ -v
```

Los tests cubren:

- Modelo `Task`: creación, validación de campos, serialización y deserialización.
- `TaskManager`: CRUD completo con repositorio mockeado.
- `AITaskService`: los cuatro flujos de IA con un proveedor simulado (DummyProvider).
- Endpoints HTTP: todos los endpoints incluyendo `GET /` con `TestClient` de FastAPI.

---

## Imagen Docker en Docker Hub

Una vez ejecutado el pipeline con éxito, la imagen estará disponible en:

```bash
docker pull <DOCKERHUB_USERNAME>/task-manager-api:latest
```

Para desplegarla en cualquier entorno:

```bash
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  <DOCKERHUB_USERNAME>/task-manager-api:latest
```

---

## Variables de entorno

Consulta `.env.example` para ver todas las variables disponibles. Las más relevantes:

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `OPENAI_API_KEY` | Clave API de OpenAI | — |
| `OPENAI_MODEL` | Modelo a utilizar | `gpt-4o-mini` |
| `AZURE_OPENAI_API_KEY` | Clave API de Azure OpenAI | — |
| `AZURE_OPENAI_ENDPOINT` | Endpoint de Azure OpenAI | — |
| `AZURE_OPENAI_MODEL` | Nombre del deployment en Azure | — |
| `AI_ALLOW_LOCAL_FALLBACK` | Activa respuestas heurísticas cuando no hay credenciales | `false` |

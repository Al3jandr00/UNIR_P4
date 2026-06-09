# Memoria Técnica — Entregable 4
## Contenerización y CI/CD de la API de Gestión de Tareas con Docker y GitHub Actions

**Repositorio GitHub:** https://github.com/Al3jandr00/UNIR_P4  
**Imagen Docker Hub:** https://hub.docker.com/r/alejandrofral/task-manager-api  
**Pipeline CI/CD:** https://github.com/Al3jandr00/UNIR_P4/actions

---

## 1. Introducción y contexto del proyecto

Este entregable cierra el ciclo de desarrollo del módulo aplicando la capa de operaciones: contenerización de la aplicación con Docker y automatización del ciclo de build, test y despliegue mediante un pipeline de integración continua con GitHub Actions.

### Evolución a lo largo del módulo

Los cuatro entregables forman una progresión coherente sobre el mismo dominio de negocio —gestión de tareas de software con asistencia de IA— añadiendo capas de complejidad técnica en cada iteración:

| Entregable | Tecnología principal | Aportación |
|------------|---------------------|------------|
| 1 | FastAPI + JSON | CRUD de tareas, arquitectura en 4 capas |
| 2 | FastAPI + OpenAI/Azure | Endpoints de IA: describir, categorizar, estimar, auditar |
| 3 | FastAPI + MySQL + Jinja2 | Base de datos relacional, historias de usuario, interfaz web |
| **4** | **FastAPI + Docker + GitHub Actions** | **Contenerización y CI/CD** |

### Decisión de base de trabajo

Para este entregable se ha retomado el Entregable 2 como base en lugar del 3. La razón es técnica y deliberada: el Entregable 3 depende de un servidor MySQL externo, lo que requeriría `docker-compose` con múltiples contenedores. El objetivo del entregable es demostrar la contenerización con un único `Dockerfile`, y la persistencia en JSON del Entregable 2 permite un contenedor completamente autocontenido que puede ejecutarse en cualquier máquina sin infraestructura adicional.

---

## 2. Descripción de la aplicación

La aplicación es una **API REST** construida con **FastAPI** y Python 3.12. Expone dos familias de endpoints:

### Endpoint de bienvenida

`GET /` devuelve un mensaje de saludo con el mapa completo de endpoints disponibles:

```json
{
  "message": "Bienvenido a la API de Gestión de Tareas",
  "version": "4.0.0",
  "descripcion": "API REST para gestión de tareas con integración de IA generativa...",
  "docs": "/docs",
  "endpoints": { ... }
}
```

### CRUD de tareas (`/tasks`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/tasks` | Listar todas las tareas |
| POST | `/tasks` | Crear una tarea nueva |
| GET | `/tasks/{id}` | Obtener una tarea por ID |
| PUT | `/tasks/{id}` | Actualizar una tarea existente |
| DELETE | `/tasks/{id}` | Eliminar una tarea |

### Endpoints de IA (`/ai/tasks`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/ai/tasks/describe` | Genera la descripción de una tarea con LLM |
| POST | `/ai/tasks/categorize` | Clasifica la tarea (Frontend, Backend, Infra…) |
| POST | `/ai/tasks/estimate` | Estima las horas de esfuerzo necesarias |
| POST | `/ai/tasks/audit` | Genera análisis de riesgos y plan de mitigación |

La aplicación soporta tanto **OpenAI** como **Azure OpenAI** como proveedor LLM. Cuando no hay credenciales configuradas, activa un mecanismo de **fallback heurístico local** basado en reglas de palabras clave, lo que permite que la aplicación funcione en entornos de prueba sin acceso a LLMs.

La documentación interactiva de la API se genera automáticamente por FastAPI y está disponible en `/docs` (Swagger UI) y `/redoc`.

---

## 3. Arquitectura del proyecto

El proyecto sigue una **arquitectura en 4 capas** que aplica el patrón de arquitectura limpia, establecida en el Entregable 1 y mantenida de forma consistente:

```
Proyecto 4/
├── domain/               ← Modelo de negocio puro (sin dependencias externas)
│   └── task.py
├── application/          ← Casos de uso y lógica de negocio
│   ├── task_manager.py
│   └── ai_task_service.py
├── infrastructure/       ← Detalles técnicos externos (ficheros, LLM, config)
│   ├── protocols.py      ← Contratos formales (nuevos en este entregable)
│   ├── settings.py
│   ├── json_repository.py
│   └── ai_provider.py
├── interface/            ← Capa HTTP (FastAPI routers)
│   ├── dependencies.py   ← Inyección de dependencias (nuevo en este entregable)
│   ├── routes.py
│   └── ai_routes.py
├── data/
│   └── tasks.json        ← Persistencia en fichero JSON
├── tests/
│   ├── conftest.py       ← Fixtures con DI overrides (nuevo en este entregable)
│   ├── test_task.py
│   ├── test_task_manager.py
│   ├── test_ai_task_service.py
│   └── test_routes.py
├── .github/
│   └── workflows/
│       └── docker-ci.yml ← Pipeline CI/CD
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── main.py
└── .env.example
```

### Capa de dominio

Contiene el modelo de negocio sin ninguna dependencia externa. La clase `Task` encapsula todos los atributos de una tarea: `id` (UUID generado automáticamente), `title`, `description`, `priority`, `effort_hours`, `status`, `assigned_to`, `category`, `risk_analysis` y `risk_mitigation`. Los enums `Priority` y `Status` garantizan la integridad de los valores aceptados en tiempo de ejecución y ofrecen mensajes de error claros ante valores inválidos.

### Capa de aplicación

`TaskManager` implementa las cinco operaciones CRUD. Recibe el repositorio por constructor (inyección de dependencias), lo que lo desacopla completamente de la implementación de persistencia concreta. `AITaskService` orquesta los cuatro flujos de enriquecimiento con IA: valida los campos de entrada obligatorios, delega la generación en el proveedor LLM inyectado y valida que la respuesta del modelo sea coherente antes de devolverla.

### Capa de infraestructura

`JsonRepository` lee y escribe el fichero `data/tasks.json`, manejando de forma transparente la creación del directorio si no existe y la ausencia del fichero (devuelve lista vacía). `AIProvider` encapsula la comunicación con el LLM con soporte para Azure OpenAI, OpenAI directo y fallback heurístico local. `Settings` centraliza la lectura de todas las variables de entorno al arranque. `protocols.py` define los contratos formales `TaskRepositoryProtocol` y `AIProviderProtocol` usando el mecanismo `Protocol` de Python para tipado estructural.

### Capa de interfaz

Los routers de FastAPI se limitan a transformar peticiones HTTP en llamadas a los servicios de aplicación y a traducir excepciones de dominio en respuestas HTTP semánticamente correctas (422 para errores de validación, 503 cuando el proveedor LLM no está disponible, 404 para recursos no encontrados). El módulo `dependencies.py` actúa como raíz de composición, wiring los singletons de infraestructura con las capas superiores mediante el sistema `Depends()` de FastAPI.

---

## 4. Principios SOLID aplicados

La revisión de código de este entregable ha introducido mejoras concretas alineadas con los cinco principios SOLID. Estas mejoras no son ornamentales: tienen impacto directo en la testabilidad del código y en la calidad del pipeline CI/CD.

### S — Responsabilidad Única

Cada clase tiene exactamente una razón para cambiar. `Task` cambia solo si cambia el modelo de negocio. `JsonRepository` cambia solo si cambia la estrategia de persistencia. `AIProvider` cambia solo si cambia la integración con el LLM externo. Esta separación, establecida en los entregables anteriores, se ha mantenido y reforzado.

### O — Abierto/Cerrado

Gracias a los protocolos formales de `protocols.py`, se puede añadir una `MySQLRepository` o una `InMemoryRepository` sin modificar `TaskManager`. Del mismo modo, se puede incorporar un proveedor LLM alternativo (Anthropic, Google Gemini) creando una clase que satisfaga `AIProviderProtocol` sin tocar `AITaskService`. El sistema está abierto a extensión y cerrado a modificación.

### L — Sustitución de Liskov

En la suite de pruebas, `DummyProvider` sustituye a `AIProvider` y `AITaskService` no percibe la diferencia. Las clases `FailService` y `UnavailableService` de los tests de error sustituyen al servicio real para verificar el manejo de excepciones en los routers. Este principio es el que hace posible que el pipeline CI/CD ejecute los tests sin credenciales reales de OpenAI.

### I — Segregación de Interfaces

`AIProviderProtocol` solo declara los cinco métodos que `AITaskService` necesita. No expone el cliente HTTP interno ni los métodos de configuración de `AIProvider`. `TaskRepositoryProtocol` solo declara `load` y `save`, sin exponer la ruta del fichero subyacente.

### D — Inversión de Dependencias

Este es el cambio más significativo introducido en este entregable. En el Entregable 2, `TaskManager` instanciaba `JsonRepository` a nivel de módulo mediante un singleton (`_repository = JsonRepository()`). Esto acoplaba la lógica de negocio a la implementación concreta de persistencia y obligaba a los tests a usar `@patch` para parchear variables de módulo, lo que hacía los tests frágiles y dependientes de la estructura interna de la clase.

La solución implementada es la inyección por constructor:

```python
class TaskManager:
    def __init__(self, repository: TaskRepositoryProtocol) -> None:
        self._repository = repository
```

Ahora los tests crean un `Mock()` y lo pasan directamente, sin parchear nada:

```python
def test_create_returns_task_instance():
    manager = TaskManager(Mock())
    result = manager.create(VALID_DATA)
    assert isinstance(result, Task)
```

En la capa de interfaz, la inyección de dependencias se implementa con el mecanismo nativo de FastAPI:

```python
TaskManagerDep = Annotated[TaskManager, Depends(get_task_manager)]

@router.post("", status_code=201)
def create_task(body: Annotated[dict, Body()], manager: TaskManagerDep) -> dict:
    ...
```

Y en los tests de integración, las dependencias se sustituyen mediante `app.dependency_overrides`, sin parchear módulos:

```python
app.dependency_overrides[get_task_manager] = lambda: TaskManager(JsonRepository(tmp_path / "test.json"))
```

---

## 5. Contenerización con Docker

### El Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup --no-create-home appuser \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Cada decisión tiene una justificación técnica concreta:

**`python:3.12-slim`:** imagen oficial basada en Debian Bookworm en su variante mínima. Se eligió frente a Alpine por su mayor compatibilidad con paquetes binarios de Python sin la penalización de tamaño de la imagen completa, logrando un equilibrio entre tamaño y compatibilidad.

**Separación de `COPY requirements.txt` y `COPY .`:** aprovecha la caché de capas de Docker. Mientras `requirements.txt` no cambie, la capa de instalación de dependencias se reutiliza en builds sucesivos, reduciendo significativamente el tiempo de construcción.

**`--no-cache-dir`:** evita que pip almacene caché de paquetes en la imagen, reduciendo el tamaño final del artefacto.

**Usuario `appuser` no-root:** sigue el principio de mínimo privilegio. Si un atacante compromete la aplicación, sus capacidades dentro del contenedor quedan severamente limitadas al no tener acceso root. Es una buena práctica estándar en imágenes de producción.

**`mkdir -p data`:** garantiza que el directorio de persistencia exista en el contenedor aunque el fichero `tasks.json` no se incluya en la imagen (está en `.dockerignore`).

**`uvicorn` como servidor de producción:** coherente con el servidor ASGI usado en todos los entregables anteriores. No se usa `--reload` en producción para evitar el overhead de monitoreo de ficheros.

### El .dockerignore

```
__pycache__/
*.pyc
.env
venv/
.git/
.github/
tests/
data/tasks.json
```

Excluye el entorno virtual local, los tests (no necesarios en la imagen de producción), el fichero `.env` con credenciales, los cachés de Python y el historial de git, reduciendo el contexto de build y evitando que información sensible entre en la imagen.

### Verificación local

```bash
docker build -t task-manager-api .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... alejandrofral/task-manager-api
curl http://localhost:8000/
```

La imagen también está disponible directamente desde Docker Hub:

```bash
docker pull alejandrofral/task-manager-api:latest
docker run -p 8000:8000 alejandrofral/task-manager-api:latest
```

---

## 6. Pipeline de integración continua (GitHub Actions)

### Estructura del workflow

El fichero `.github/workflows/docker-ci.yml` define dos jobs que se ejecutan de forma secuencial, implementando una puerta de calidad obligatoria antes de cualquier publicación:

```
push a main
    │
    ▼
┌─────────────┐
│  job: test  │  ← Si falla, el pipeline para aquí
└─────────────┘
    │ needs: test
    ▼
┌──────────────────────────┐
│  job: docker-build-push  │  ← Solo si test pasa Y es push a main
└──────────────────────────┘
```

### Job `test`

```yaml
test:
  name: Run tests
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - run: pip install -r requirements.txt
    - run: pytest tests/ -v
      env:
        AI_ALLOW_LOCAL_FALLBACK: "true"
```

Se activa tanto en `push` como en `pull_request` sobre `main`. La variable de entorno `AI_ALLOW_LOCAL_FALLBACK=true` activa el fallback heurístico local, permitiendo que los 50 tests pasen sin credenciales de OpenAI. Este job es la puerta de calidad: si cualquier test falla, la imagen no se construye ni se publica.

### Job `docker-build-push`

```yaml
docker-build-push:
  name: Build and push Docker image
  needs: test
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  steps:
    - uses: actions/checkout@v4
    - uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    - uses: docker/build-push-action@v6
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.DOCKERHUB_USERNAME }}/task-manager-api:latest
          ${{ secrets.DOCKERHUB_USERNAME }}/task-manager-api:${{ github.sha }}
```

Solo se ejecuta en `push` directo a `main` (no en PRs), garantizando que solo el código revisado y fusionado llegue al registro. Las credenciales de Docker Hub se almacenan como secretos de repositorio en GitHub (`DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN`), nunca embebidas en el código. La imagen se publica con dos tags: `latest` para facilitar el despliegue y el SHA del commit para permitir trazabilidad y rollback.

### Evidencia de ejecución

El pipeline ha sido ejecutado con éxito. Los resultados pueden verificarse en:

**https://github.com/Al3jandr00/UNIR_P4/actions**

- **Run #1** (`676cda1`): falló en `test` por `HTTP_422_UNPROCESSABLE_CONTENT` — constante no disponible en la versión de Starlette del runner de GitHub Actions. Se corrigió usando el nombre estándar `HTTP_422_UNPROCESSABLE_ENTITY`.
- **Run #2** (`30ccb2f`): ✅ `test` pasó (50/50), ✅ `docker-build-push` publicó la imagen en Docker Hub.

La imagen publicada está disponible en:

**https://hub.docker.com/r/alejandrofral/task-manager-api**

---

## 7. Estrategia de pruebas

La suite consta de **50 tests** distribuidos en cuatro ficheros, con una cobertura que abarca desde el modelo de dominio hasta los endpoints HTTP.

### `test_task.py` — Tests unitarios del modelo de dominio

Verifica el modelo `Task` en aislamiento total: generación automática de UUIDs, validación de enums `Priority` y `Status` con rechazo explícito de valores inválidos, y el ciclo completo de serialización `to_dict()` → `from_dict()` preservando todos los campos incluyendo los de IA.

### `test_task_manager.py` — Tests unitarios de lógica de negocio

Verifica las cinco operaciones CRUD de `TaskManager`. Gracias a la inyección de dependencias, cada test construye un `Mock()` de repositorio directamente:

```python
def test_create_persists_ai_fields():
    repo = Mock()
    repo.load.return_value = []
    manager = TaskManager(repo)
    manager.create({**VALID_DATA, "category": "Backend"})
    assert repo.save.call_args[0][0][0]["category"] == "Backend"
```

No hay ningún `@patch` de módulo. Los tests son independientes de la implementación interna del repositorio.

### `test_ai_task_service.py` — Tests unitarios del servicio de IA

Verifica los cuatro flujos de enriquecimiento mediante `DummyProvider`. Cubre validación de entrada (campos obligatorios ausentes), validación de salida del modelo (descripción vacía, categoría fuera del conjunto permitido) y el correcto enriquecimiento del payload de la tarea.

### `test_routes.py` — Tests de integración de endpoints HTTP

Verifica todos los endpoints incluyendo `GET /`. Usa el fixture `client` definido en `conftest.py`, que aplica `app.dependency_overrides` para sustituir las dependencias de FastAPI:

```python
@pytest.fixture
def client(task_manager, ai_service):
    app.dependency_overrides[get_task_manager] = lambda: task_manager
    app.dependency_overrides[get_ai_service] = lambda: ai_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

El `task_manager` del fixture usa `JsonRepository` apuntando a un fichero temporal de pytest (`tmp_path`), garantizando aislamiento total entre tests. El `ai_service` usa `DummyProvider`, eliminando cualquier llamada a LLMs externos.

### Resultado en CI

```
50 passed in 1.13s
```

---

## 8. Decisiones técnicas y justificaciones

**FastAPI en lugar de Flask:** el enunciado menciona Flask, pero los tres entregables anteriores han usado FastAPI de forma consistente. Migrar a Flask habría supuesto reescribir toda la capa de interfaz y los tests sin ningún beneficio pedagógico. FastAPI ofrece además ventajas concretas: validación automática de tipos, documentación OpenAPI en `/docs` y soporte nativo para inyección de dependencias con `Depends()`.

**Puerto 8000 en lugar de 5000:** el puerto 5000 es la convención de Flask. uvicorn, el servidor ASGI de FastAPI, usa el puerto 8000 por convención. Cambiar el puerto habría introducido inconsistencia con los entregables anteriores sin beneficio real.

**Contenedor único sin docker-compose:** se evita deliberadamente `docker-compose` para demostrar que la aplicación puede ejecutarse de forma autocontenida. La persistencia en JSON elimina la necesidad de un servicio externo de base de datos, haciendo la imagen más sencilla de desplegar y distribuir.

**`@lru_cache` para singletons:** los objetos `JsonRepository` y `AIProvider` se crean una sola vez por proceso mediante `@lru_cache`. Esto evita reconexiones innecesarias al LLM y múltiples aperturas del mismo fichero. La solución es compatible con `app.dependency_overrides` en tests, que reemplaza la función completa sin necesidad de limpiar la caché.

**Corrección de compatibilidad de Starlette:** durante la primera ejecución del pipeline se detectó que la constante `HTTP_422_UNPROCESSABLE_CONTENT` no existe en la versión de Starlette instalada en el runner de GitHub Actions (`ubuntu-latest`). El nombre estándar y compatible es `HTTP_422_UNPROCESSABLE_ENTITY`. Este hallazgo demuestra el valor del pipeline: el error fue detectado automáticamente en CI antes de que pudiera afectar a un despliegue real.

---

## 9. Instrucciones de despliegue

### Desde Docker Hub (imagen publicada)

```bash
# Sin credenciales de IA (CRUD funciona, endpoints de IA devuelven 503)
docker run -p 8000:8000 alejandrofral/task-manager-api:latest

# Con OpenAI
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e OPENAI_MODEL=gpt-4o-mini \
  alejandrofral/task-manager-api:latest

# Con Azure OpenAI
docker run -p 8000:8000 \
  -e AZURE_OPENAI_API_KEY=... \
  -e AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com \
  -e AZURE_OPENAI_MODEL=gpt-4o-mini \
  alejandrofral/task-manager-api:latest
```

### Construyendo desde el código fuente

```bash
git clone https://github.com/Al3jandr00/UNIR_P4.git
cd UNIR_P4
docker build -t task-manager-api .
docker run -p 8000:8000 task-manager-api
```

### Verificación

Una vez arrancado el contenedor, la API responde en `http://localhost:8000/`:

```bash
curl http://localhost:8000/
# → {"message": "Bienvenido a la API de Gestión de Tareas", "version": "4.0.0", ...}
```

La documentación interactiva Swagger UI está disponible en `http://localhost:8000/docs`.

### Ejecución de tests

```bash
pip install -r requirements.txt
pytest tests/ -v
# → 50 passed in 0.27s
```

---

## 10. Conclusiones

Este entregable cierra el ciclo de los cuatro proyectos del módulo demostrando cómo una aplicación desarrollada iterativamente puede empaquetarse como un artefacto reproducible y distribuible mediante contenedores Docker, y cómo automatizar su ciclo de vida completo —verificación, construcción y publicación— mediante un pipeline de integración continua.

El valor de la integración continua quedó evidenciado de forma práctica durante el desarrollo: el primer intento de push detectó automáticamente un error de compatibilidad de versiones de Starlette que no había sido detectado en el entorno local de desarrollo (Windows con Python 3.14). Sin el pipeline, ese error podría haber llegado a producción.

La aplicación de los principios SOLID, y en particular el principio de Inversión de Dependencias, no fue un ejercicio teórico sino una necesidad práctica: sin inyección de dependencias no habría sido posible sustituir las dependencias externas (LLM, sistema de ficheros) en los tests, y sin tests limpios no habría sido posible construir un pipeline de CI funcional. Los principios de diseño y las prácticas de operaciones están profundamente conectados.

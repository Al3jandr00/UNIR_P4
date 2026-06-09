# Memoria Técnica — Entregable 4
## Contenerización y CI/CD de la API de Gestión de Tareas

---

## 1. Introducción y contexto del proyecto

Este entregable cierra el ciclo de desarrollo iniciado en los tres entregables anteriores del módulo, añadiendo la capa de operaciones: contenerización con Docker y automatización del ciclo de vida de la aplicación mediante integración continua con GitHub Actions.

A lo largo del módulo se ha construido de forma incremental una API REST de gestión de tareas enriquecida con inteligencia artificial generativa. En el Entregable 1 se estableció la arquitectura base y el CRUD de tareas usando FastAPI con persistencia en JSON. En el Entregable 2 se incorporaron cuatro endpoints de IA (descripción, categorización, estimación de esfuerzo y auditoría de riesgos) apoyados en Azure OpenAI u OpenAI. En el Entregable 3 la aplicación evolucionó hacia una arquitectura más compleja con base de datos MySQL, modelos SQLAlchemy, esquemas Pydantic e interfaz web con Jinja2 y Bootstrap para gestionar historias de usuario y sus tareas asociadas.

Para el Entregable 4 se ha tomado la decisión deliberada de retomar la versión del Entregable 2 como punto de partida. La razón es técnica: el requisito central del entregable es demostrar contenerización con un único Dockerfile, sin dependencias externas de infraestructura. Incluir MySQL en el contenedor o añadir un `docker-compose.yml` habría desviado el foco del objetivo principal. La persistencia en JSON permite un contenedor autocontenido que puede ejecutarse en cualquier máquina sin configuración adicional.

---

## 2. Arquitectura de la aplicación

La aplicación mantiene la arquitectura en cuatro capas establecida en los entregables anteriores, un diseño que refleja el patrón de arquitectura limpia y que facilita el cumplimiento de los principios SOLID:

**Capa de dominio (`domain/`):** contiene el modelo de negocio puro. La clase `Task` representa una tarea con todos sus atributos: identificador UUID, título, descripción, prioridad, horas de esfuerzo estimadas, estado, responsable, categoría, análisis de riesgos y plan de mitigación. Los enums `Priority` y `Status` garantizan la integridad de los valores en tiempo de ejecución. Esta capa no tiene ninguna dependencia externa.

**Capa de aplicación (`application/`):** orquesta los casos de uso del sistema. `TaskManager` implementa las operaciones CRUD delegando la persistencia en el repositorio que recibe por constructor. `AITaskService` coordina los flujos de enriquecimiento con IA: valida la entrada, delega la generación de contenido en el proveedor LLM inyectado y valida que la salida sea coherente antes de devolvérsela al cliente.

**Capa de infraestructura (`infrastructure/`):** contiene los detalles técnicos de comunicación con el exterior. `JsonRepository` gestiona la lectura y escritura del fichero `data/tasks.json`. `AIProvider` encapsula las llamadas al LLM configurado (Azure OpenAI u OpenAI directo), con lógica de fallback local para entornos sin credenciales. `Settings` centraliza toda la configuración desde variables de entorno. El módulo `protocols.py`, añadido en este entregable, define los contratos formales de ambas implementaciones.

**Capa de interfaz (`interface/`):** expone la API HTTP mediante FastAPI. Los routers `routes.py` y `ai_routes.py` se limitan a transformar peticiones HTTP en llamadas a los servicios de aplicación y a traducir excepciones en respuestas HTTP apropiadas. El módulo `dependencies.py` centraliza la configuración del sistema de inyección de dependencias.

---

## 3. Aplicación de principios SOLID

La revisión de código realizada en este entregable ha llevado a mejoras concretas orientadas a los cinco principios SOLID:

**Principio de Responsabilidad Única (S):** cada clase tiene una única razón para cambiar. `Task` solo cambia si cambia el modelo de negocio. `JsonRepository` solo cambia si cambia la estrategia de persistencia. `AIProvider` solo cambia si cambia la integración con el LLM. Esta separación ya existía en los entregables anteriores y se ha mantenido intacta.

**Principio Abierto/Cerrado (O):** gracias a los protocolos formales definidos en `protocols.py`, es posible añadir nuevas implementaciones de repositorio (por ejemplo, una `MySQLRepository` o una `InMemoryRepository`) sin modificar `TaskManager`. Del mismo modo, se puede incorporar un proveedor LLM alternativo (Anthropic, Gemini) creando una nueva clase que cumpla `AIProviderProtocol` sin tocar `AITaskService`.

**Principio de Sustitución de Liskov (L):** en la suite de pruebas, `DummyProvider` sustituye a `AIProvider` sin que `AITaskService` perciba la diferencia. Esto funciona porque ambos implementan estructuralmente `AIProviderProtocol`. La misma propiedad se verifica con `FailService` y `UnavailableService` en los tests de error de los routers.

**Principio de Segregación de Interfaces (I):** `AIProviderProtocol` solo declara los cinco métodos que `AITaskService` necesita; no incluye métodos de configuración del cliente ni de gestión de tokens que son internos de `AIProvider`. `TaskRepositoryProtocol` solo expone `load` y `save`; no expone detalles del fichero subyacente.

**Principio de Inversión de Dependencias (D):** este es el cambio más significativo del entregable. En los entregables anteriores, `TaskManager` instanciaba `JsonRepository` directamente a nivel de módulo mediante un singleton (`_repository = JsonRepository()`). Esto acoplaba la lógica de negocio a la implementación de persistencia y dificultaba las pruebas unitarias, que necesitaban parchear el módulo entero con `unittest.mock.patch`. Ahora `TaskManager` recibe el repositorio por constructor, lo que permite inyectar cualquier implementación compatible. Lo mismo aplica a `AITaskService`, que ahora requiere el proveedor explícitamente en lugar de instanciarlo internamente con un parámetro opcional.

En la capa de interfaz, la inyección de dependencias se implementa con el mecanismo nativo de FastAPI: `Depends()`. Los routers declaran sus dependencias como parámetros anotados con `Annotated[TaskManager, Depends(get_task_manager)]`. El módulo `interface/dependencies.py` actúa como composición root, wiring las implementaciones concretas de la capa de infraestructura con las abstracciones que esperan las capas superiores.

---

## 4. Contenerización con Docker

El `Dockerfile` sigue las buenas prácticas estándar del sector:

Se parte de `python:3.12-slim`, una imagen oficial basada en Debian Bookworm en su variante mínima. Se eligió frente a Alpine porque ofrece mayor compatibilidad con paquetes binarios de Python sin el overhead de la imagen completa, lo que resulta en imágenes más ligeras con menos superficie de ataque.

La instrucción `COPY requirements.txt .` seguida de `RUN pip install` aprovecha la caché de capas de Docker: mientras el fichero de requisitos no cambie, Docker reutilizará la capa de instalación de dependencias en builds sucesivos, reduciendo significativamente el tiempo de construcción durante el desarrollo.

Se ha añadido la creación de un usuario del sistema sin privilegios (`appuser`) y la transferencia de propiedad del directorio de trabajo. La instrucción `USER appuser` garantiza que el proceso de la aplicación no se ejecuta como `root` dentro del contenedor, siguiendo el principio de mínimo privilegio. Si un atacante consiguiera comprometer la aplicación, sus capacidades dentro y fuera del contenedor quedarían severamente limitadas.

El directorio `data/` se crea explícitamente durante el build para garantizar que el fichero `tasks.json` pueda escribirse aunque no exista previamente. El `.dockerignore` excluye el entorno virtual (`venv/`), el directorio de tests, los ficheros `.env` con credenciales, los cachés de Python y el directorio `.git`, reduciendo el contexto de build y evitando filtrar información sensible en la imagen.

El comando de arranque utiliza uvicorn directamente en lugar de Flask's development server o gunicorn, por coherencia con el servidor ASGI que usa la aplicación en local y en los entregables anteriores.

---

## 5. Pipeline de integración continua

El pipeline está definido en `.github/workflows/docker-ci.yml` y consta de dos jobs que se ejecutan de forma secuencial gracias a la directiva `needs: test`.

El primer job, `test`, se activa tanto en `push` como en `pull_request` sobre `main`. Configura un entorno Python 3.12, instala las dependencias y ejecuta la suite completa de tests con `pytest tests/ -v`. La variable de entorno `AI_ALLOW_LOCAL_FALLBACK=true` activa las respuestas heurísticas del proveedor de IA para que los tests pasen sin credenciales reales. Este job actúa como puerta de calidad: si algún test falla, el pipeline se detiene y la imagen nunca se construye ni se publica.

El segundo job, `docker-build-push`, solo se ejecuta cuando el evento es un `push` directo a `main` (no en PRs), garantizando que solo el código revisado y aprobado llegue al registro. Utiliza las acciones oficiales `docker/login-action@v3` y `docker/build-push-action@v6`. La imagen se publica con dos tags: `latest` para facilitar el despliegue manual, y el SHA del commit para permitir trazabilidad y rollback a versiones anteriores.

Las credenciales de Docker Hub (usuario y token de acceso) se almacenan como secretos de repositorio en GitHub (`DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN`), siguiendo la buena práctica de nunca embeber credenciales en el código fuente ni en los ficheros del pipeline.

---

## 6. Estrategia de pruebas

La suite de pruebas consta de 50 tests distribuidos en cuatro módulos:

`test_task.py` verifica el modelo de dominio en aislamiento: generación de UUID, validación de enums, serialización y deserialización completa del ciclo `to_dict` → `from_dict`.

`test_task_manager.py` verifica la lógica de negocio CRUD. Aprovechando la inyección de dependencias, cada test crea un `Mock()` de repositorio y lo pasa directamente al constructor de `TaskManager`. Esto elimina la necesidad de `@patch` de módulo, hace los tests más legibles y los desacopla de la implementación interna del repositorio.

`test_ai_task_service.py` verifica los cuatro flujos de enriquecimiento con IA mediante un `DummyProvider` inyectado. Se prueba explícitamente la validación de la entrada (campos obligatorios), la validación de la salida del modelo (descripción vacía, categoría inválida) y los flujos de datos entre el servicio y el proveedor.

`test_routes.py` realiza pruebas de integración sobre todos los endpoints HTTP. El fichero `tests/conftest.py` define tres fixtures que se componen automáticamente: `task_manager` instancia un `TaskManager` con un `JsonRepository` apuntando a un fichero temporal de pytest (se crea y destruye por test, garantizando aislamiento); `ai_service` instancia un `AITaskService` con `DummyProvider`; y `client` sobrescribe las dependencias de FastAPI mediante `app.dependency_overrides` antes de crear el `TestClient` y las limpia al finalizar. Para los casos de error de la capa de IA (422 y 503), los tests crean sus propias instancias de servicio fallido y las aplican mediante `app.dependency_overrides` directamente dentro del test.

---

## 7. Decisiones técnicas y justificaciones

**FastAPI en lugar de Flask:** el enunciado del entregable menciona Flask, pero los tres entregables anteriores han utilizado FastAPI consistentemente. Migrar a Flask habría supuesto reescribir toda la capa de interfaz y los tests de integración sin ningún beneficio pedagógico, perdiendo además las ventajas de FastAPI: validación automática, generación de documentación OpenAPI en `/docs` y soporte nativo para inyección de dependencias.

**Puerto 8000 en lugar de 5000:** uvicorn, el servidor ASGI que FastAPI recomienda, utiliza el puerto 8000 por convención. Cambiar a 5000 solo para alinearse con la mención de Flask en el enunciado habría introducido inconsistencia con los entregables anteriores.

**Contenedor único sin docker-compose:** se evita deliberadamente añadir docker-compose para demostrar que la aplicación puede ejecutarse de forma completamente autocontenida. La persistencia en JSON elimina la necesidad de un servicio de base de datos externo, lo que hace la imagen más sencilla de desplegar, probar y distribuir.

**`@lru_cache` para singletons de infraestructura:** en FastAPI existen varias formas de gestionar singletons (lifespan events, variables de módulo, `@lru_cache`). Se eligió `@lru_cache` por ser la opción que mejor combina sencillez con testabilidad: permite que `app.dependency_overrides` reemplace la función cacheada sin necesidad de modificar el estado global del módulo.

---

## 8. Instrucciones de despliegue resumidas

Para construir y ejecutar la imagen localmente:

```bash
docker build -t task-manager-api .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... task-manager-api
```

La API responderá en `http://localhost:8000/` y la documentación interactiva estará disponible en `http://localhost:8000/docs`.

Para verificar que el pipeline CI/CD funciona correctamente, basta con hacer un `push` a la rama `main` del repositorio. GitHub Actions ejecutará la suite de tests y, si todos pasan, publicará la imagen en Docker Hub bajo el usuario configurado en los secretos del repositorio.

---

## 9. Conclusiones

Este entregable demuestra cómo una aplicación desarrollada iterativamente puede empaquetarse como un artefacto reproducible y distribuible mediante contenedores, y cómo automatizar su ciclo de vida mediante pipelines de CI/CD. La aplicación de los principios SOLID, especialmente la inversión de dependencias, no solo mejora la calidad del código sino que habilita una estrategia de pruebas más robusta y mantenible. La separación entre el job de tests y el job de publicación en el pipeline refleja el principio de que el código que llega al registro de imágenes siempre ha pasado por una verificación automatizada de calidad.

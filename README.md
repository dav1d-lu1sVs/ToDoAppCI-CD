# To-Do List (FastAPI)

Aplicación de tareas: **API REST con FastAPI + SQLModel + SQLite** y un **frontend en
HTML/CSS/JS** servido por la misma API. Incluye pruebas con **pytest**.

## Puesta en marcha (Windows / PowerShell)

```powershell
# 1. Crear el entorno virtual (una sola vez por proyecto)
py -3 -m venv .venv

# 2. Activarlo (cada vez que abras una terminal nueva)
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements-dev.txt

# 4. Levantar en modo desarrollo (se recarga al guardar)
fastapi dev app/main.py
```

| URL | Qué es |
|---|---|
| <http://127.0.0.1:8000> | La aplicación (frontend) |
| <http://127.0.0.1:8000/docs> | Documentación interactiva (Swagger) |
| <http://127.0.0.1:8000/health> | Estado del servicio |

Al arrancar por primera vez se crea `tareas.db` con **6 tareas de ejemplo**.
Para empezar de cero: detén el servidor, borra `tareas.db` y vuelve a levantarlo.

> Si PowerShell bloquea `Activate.ps1`, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Comandos útiles

| Qué | Comando |
|---|---|
| Servidor de desarrollo | `fastapi dev app/main.py` |
| Servidor "producción" | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Cargar datos de ejemplo a mano | `python -m app.seed` |
| Pruebas | `pytest` |
| Pruebas + cobertura | `pytest --cov=app --cov-report=term-missing` |
| Linter | `ruff check .` |
| Formatear código | `ruff format .` |

## Endpoints

| Método | Ruta | Acción | Respuesta OK |
|---|---|---|---|
| GET | `/health` | Estado de la API | 200 |
| POST | `/tareas` | Crear | 201 |
| GET | `/tareas?completada=&prioridad=&q=&offset=&limit=` | Listar / filtrar / buscar | 200 |
| GET | `/tareas/{id}` | Obtener una | 200 / 404 |
| PUT | `/tareas/{id}` | Reemplazar completa | 200 / 404 |
| PATCH | `/tareas/{id}` | Actualizar parcial | 200 / 404 |
| DELETE | `/tareas/{id}` | Eliminar | 204 / 404 |

Una tarea: `titulo` (1–100), `descripcion` (opcional, ≤500), `completada` (bool),
`prioridad` (`baja` | `media` | `alta`), `id` y `fecha_creacion` (los genera el servidor).

## Estructura

```
FastApiCrud/
├── app/                        # BACKEND (monolito por capas)
│   ├── main.py                 # crea la app, monta routers y frontend, arranque
│   ├── config.py               # configuración desde variables de entorno
│   ├── database.py             # engine, sesión y dependencia SessionDep
│   ├── models.py               # tabla Tarea + esquemas de entrada/salida
│   ├── seed.py                 # datos de ejemplo
│   ├── routers/tareas.py       # capa HTTP: endpoints  (≈ @RestController)
│   └── services/tareas.py      # lógica de negocio     (≈ @Service)
├── frontend/                   # FRONTEND (servido en "/")
│   ├── index.html              # estructura + plantillas + diálogos
│   ├── css/styles.css          # estilos (tema claro/oscuro, responsive)
│   └── js/
│       ├── app.js              # estado y eventos (orquesta todo)
│       ├── api.js              # ÚNICO archivo que hace fetch a la API
│       └── ui.js               # funciones que pintan en pantalla
├── tests/                      # pruebas (BD en memoria por test)
├── requirements.txt            # dependencias de ejecución (EC2)
├── requirements-dev.txt        # + herramientas de desarrollo (CI)
└── pyproject.toml              # configuración de pytest y ruff
```

Flujo de una petición:

```
Navegador ─fetch─► routers/tareas.py ─► services/tareas.py ─► SQLModel ─► tareas.db
   ▲                     │ (valida con models.py, responde con códigos HTTP)
   └──────── JSON ───────┘
```

## Configuración (variables de entorno)

| Variable | Por defecto | Uso |
|---|---|---|
| `DATABASE_URL` | `sqlite:///<proyecto>/tareas.db` | Cambiar de BD sin tocar código |
| `SEED_DATA` | `true` | Cargar tareas de ejemplo si la BD está vacía |
| `CORS_ORIGINS` | *(vacío)* | Orígenes permitidos si el frontend vive en otro dominio, separados por coma |

## CI/CD con GitLab y AWS EC2

El pipeline definido en `.gitlab-ci.yml` usa Python 3.12 y contiene cinco etapas:

1. **prepare:** instala las dependencias de desarrollo y comprueba que sean compatibles.
2. **build:** ejecuta Ruff y comprueba que los módulos de la aplicación compilen.
3. **test:** ejecuta pytest con cobertura y publica `coverage.xml` como reporte.
4. **package:** crea `dist/todo-app.tar.gz` con la aplicación, el frontend y los archivos de configuración necesarios. Excluye archivos `.db`, `.git`, entornos virtuales, cachés y credenciales.
5. **deploy:** solo se ejecuta automáticamente en `main`. Transfiere el paquete por SCP y llama `scripts/deploy_ec2.sh` por SSH.

### Variables protegidas de GitLab

En **Settings > CI/CD > Variables**, crea las variables siguientes. Marca todas como **Protected** y limita el despliegue a la rama protegida `main`:

| Variable | Tipo | Valor |
|---|---|---|
| `EC2_HOST` | Variable | DNS público o IP de EC2 |
| `EC2_USER` | Variable (opcional) | `ec2-user` (valor predeterminado) |
| `SSH_PRIVATE_KEY` | File | Clave privada SSH autorizada para `ec2-user`; enmascarar si GitLab permite el formato |
| `SSH_KNOWN_HOSTS` | File | Host key de EC2 conocida y verificada |
| `APP_DIR` | Variable (opcional) | `/home/ec2-user/todo-app` (valor predeterminado) |
| `HEALTH_URL` | Variable (opcional) | `http://127.0.0.1:8000/health` (valor predeterminado) |

No guardes la clave privada dentro del repositorio ni generes `known_hosts` confiando ciegamente en `ssh-keyscan` durante el job. Obtén y verifica la host key por un canal confiable antes de guardarla en `SSH_KNOWN_HOSTS`. La clave pública correspondiente a `SSH_PRIVATE_KEY` debe estar en `~ec2-user/.ssh/authorized_keys`.

El runner debe poder conectarse por SSH al puerto 22 de la instancia; configura el Security Group para permitir ese acceso desde la red/IP del runner. En EC2 deben existir Python 3.12, `curl`, el servicio systemd `todo-app.service` y permisos para que `ec2-user` ejecute `sudo systemctl restart` y `sudo systemctl is-active` sobre ese servicio.

### Conservación de SQLite y verificación

El artefacto excluye todos los archivos `*.db`, y el script remoto rechaza un paquete que contenga alguno. El despliegue copia archivos sin `--delete` ni limpieza del directorio de aplicación, por lo que conserva `/home/ec2-user/todo-app/tareas.db`. El script instala las dependencias en `/home/ec2-user/todo-app/venv`, reinicia `todo-app.service`, verifica que systemd lo reporte activo y consulta `/health` hasta 12 veces, con pausas de 5 segundos. Si el servicio o el health check falla, el job termina como fallido y muestra el estado de systemd.

El endpoint `/health` verifica que la API responda; no comprueba directamente la integridad ni la disponibilidad de SQLite. Las pruebas CI usan una base de datos en memoria y no acceden a la base de producción.

## Conceptos clave de FastAPI

1. **Tipos = validación.** `def crear(datos: TareaCrear)` → FastAPI lee el JSON, lo valida
   con Pydantic y, si está mal, responde **422** solo.
2. **Parámetros:** `/{tarea_id}` en la ruta → parámetro de ruta. Un argumento simple que no
   está en la ruta (`completada: bool | None = None`) → query string (`?completada=true`).
   Un modelo Pydantic → cuerpo JSON.
3. **`response_model`** filtra lo que se devuelve: solo salen los campos de `TareaPublica`.
4. **Inyección de dependencias (`Depends`)**: `session: SessionDep` hace que FastAPI cree
   y cierre la sesión de BD por ti. En las pruebas se reemplaza con `dependency_overrides`.
5. **`HTTPException`** para errores controlados (404, 400…), solo en la capa de routers.
6. **`APIRouter`** para separar endpoints por recurso y montarlos con `include_router`.
7. **`lifespan`** para código de arranque / apagado (crear tablas, datos de ejemplo).
8. **Varios modelos por entidad** (Crear / Actualizar / Pública / Tabla) para que el cliente
   no pueda enviar campos que genera el servidor (`id`, `fecha_creacion`).
9. **`StaticFiles`** sirve el frontend desde la misma app: un solo proceso y un solo puerto,
   así no hace falta CORS.
10. **`def` vs `async def`:** usa `def` normal si llamas librerías síncronas (como SQLModel);
    FastAPI las corre en un pool de hilos. Usa `async def` solo con librerías async.

# ToDoAppCI-CD
Integrantes: Bruno Moreno, Luis Vasquez, Mateo Tipan y Jose Freire
# ToDoApp CI/CD

Aplicación web para la gestión de tareas desarrollada con **FastAPI**, con un proceso de integración continua y despliegue continuo (CI/CD) mediante **GitLab CI/CD** y **AWS EC2**.

## Descripción del proyecto

ToDoApp permite gestionar tareas mediante operaciones CRUD (crear, consultar, actualizar y eliminar). El proyecto incorpora un pipeline automatizado que valida el código, ejecuta pruebas, genera un paquete de despliegue y actualiza la aplicación en un servidor EC2.

## Tecnologías utilizadas

- **Python 3.12:** lenguaje de programación.
- **FastAPI:** desarrollo de la API REST.
- **Pytest:** ejecución de pruebas automatizadas.
- **Ruff:** análisis y validación del código.
- **Git y GitHub:** control de versiones y alojamiento del código.
- **GitLab CI/CD:** automatización del pipeline.
- **AWS EC2:** alojamiento de la aplicación.
- **Linux y Systemd:** administración del servicio en el servidor.

## Pipeline CI/CD

El pipeline está definido en el archivo `.gitlab-ci.yml` y se organiza en cinco etapas:

| Etapa | Descripción |
|---|---|
| Prepare | Prepara el entorno e instala las dependencias. |
| Build | Verifica la calidad y compilación del código. |
| Test | Ejecuta las pruebas automatizadas y genera el reporte de cobertura. |
| Package | Genera un archivo comprimido con los archivos necesarios para el despliegue. |
| Deploy | Transfiere el paquete a AWS EC2, actualiza la aplicación y verifica su funcionamiento. |

## Despliegue en AWS EC2

La aplicación se despliega automáticamente en una instancia EC2 de AWS mediante conexión SSH.

El proceso de despliegue:
- Transfiere el paquete generado por el pipeline.
- Actualiza los archivos de la aplicación.
- Instala las dependencias necesarias.
- Reinicia el servicio mediante Systemd.
- Comprueba que la aplicación esté activa.

También se realiza una verificación mediante el endpoint `/health` para comprobar que el servicio responde correctamente.

## Estructura del proyecto

```text
ToDoAppCI-CD/
├── app/
├── frontend/
├── tests/
├── scripts/
│   └── deploy_ec2.sh
├── .gitlab-ci.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

## Variables de CI/CD

Para ejecutar el despliegue deben configurarse las siguientes variables en GitLab:

| Variable | Descripción |
|---|---|
| `EC2_HOST` | Dirección IP pública de la instancia EC2. |
| `EC2_USER` | Usuario SSH del servidor. |
| `APP_DIR` | Directorio de instalación de la aplicación. |
| `SSH_PRIVATE_KEY` | Clave privada para la conexión SSH. |
| `SSH_KNOWN_HOSTS` | Clave pública del servidor para verificar su identidad. |

Las variables sensibles deben configurarse como protegidas y las claves privadas no deben incluirse en el repositorio.

## Ejecución local

1. Clonar el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd ToDoAppCI-CD
```

2. Crear y activar un entorno virtual:

```bash
python -m venv .venv
```

En Windows:

```powershell
.venv\Scripts\Activate.ps1
```

3. Instalar las dependencias:

```bash
pip install -r requirements-dev.txt
```

4. Ejecutar la aplicación:

```bash
uvicorn app.main:app --reload
```

5. Abrir en el navegador:

```text
http://127.0.0.1:8000
```

## Verificación del servicio

El endpoint de salud permite comprobar que la aplicación está funcionando:

```text
GET /health
```

Respuesta esperada:

```json
{
  "status": "ok"
}
```
## Objetivo del proyecto

Implementar un flujo automatizado de integración y despliegue continuo que permita mejorar la calidad del software, reducir las tareas manuales y facilitar la publicación de nuevas versiones de la aplicación.

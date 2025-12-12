# TravelSmart-AI-API

Backend de TravelSmart, la plataforma para crear tu viaje ideal sin morir en el intento, potenciada por IA.

Este repositorio contiene la API de backend construida con FastAPI que da servicio a la aplicación [TravelSmart Frontend](https://github.com/santipdmonte/travelsmart) 

La API se encarga de:
-   Generar itinerarios de viaje personalizados usando agentes de IA (LangGraph).
-   Gestionar usuarios, autenticación (JWT y Google OAuth) y perfiles.
-   Manejar la lógica del "Test del Viajero" para definir perfiles de usuario.
-   Proveer endpoints para CRUD de itinerarios, alojamientos y transporte.
-   Analizar documentos de viaje (ej. reservas) para extraer información.

## Tecnologías Usadas

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **IA / Agentes:** [LangChain](https://www.langchain.com/) y [LangGraph](https://langchain-ai.github.io/langgraph/)
* **Base de Datos:** [SQLAlchemy](https://www.sqlalchemy.org/) (con [Alembic](https://alembic.sqlalchemy.org/en/latest/) para migraciones)
* **Validación:** [Pydantic](https://docs.pydantic.dev/latest/)
* **Autenticación:** JWT (JSON Web Tokens) y Google OAuth

## Getting Started

Sigue estos pasos para configurar y ejecutar el proyecto localmente.

### Prerrequisitos

* Python 3.10 o superior
* `pip` y `venv` (o tu manejador de entornos preferido)
* Una base de datos SQL compatible con SQLAlchemy (ej. PostgreSQL, SQLite). En nuestro caso utilizamos PostgreSQL.

### Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/santipdmonte/TravelSmart-AI-API.git](https://github.com/santipdmonte/TravelSmart-AI-API.git)
    cd TravelSmart-AI-API
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    # Para macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
   

4.  **Configurar variables de entorno:**
    Copia el archivo de ejemplo y edita el `.env` resultante con tus propias claves.
    ```bash
    cp env.example .env
    ```
    Deberás configurar, como mínimo:
    * `DATABASE_URL`: La cadena de conexión a tu base de datos (ej. `postgresql://user:pass@localhost/travelsmartdb`).
    * `OPENAI_API_KEY`: Tu clave de API de OpenAI.
    * `SECRET_KEY`: Una clave secreta para la firma de JWT (puedes generar una con `openssl rand -hex 32`).
    * `GOOGLE_CLIENT_ID`: Tu Client ID de Google para OAuth.
    * `GOOGLE_CLIENT_SECRET`: Tu Client Secret de Google para OAuth.

### Base de Datos (Alembic)

Este proyecto usa Alembic para gestionar las migraciones de la base de datos.

1.  **Crear la base de datos:** Asegúrate de haber creado la base de datos que especificaste en tu `DATABASE_URL`.

2.  **Aplicar migraciones:** Para actualizar el esquema de tu BBDD a la última versión:
    ```bash
    alembic upgrade head
    ```
   

3.  **Crear una nueva migración:** (Si haces cambios en los archivos de `models/`)
    ```bash
    alembic revision --autogenerate -m "Descripción breve de la migración"
    ```

### Ejecución

Una vez instaladas las dependencias y configurada la base de datos, puedes iniciar el servidor:

```bash
uvicorn main:app --reload --port 8001
```
* --reload: Reinicia el servidor automáticamente con cada cambio en el código.
* --port 8001: Ejecuta el servidor en el puerto 8001 (el puerto que espera el frontend por defecto).

La API estará disponible en http://localhost:8001. Puedes ver la documentación interactiva de la API (generada por FastAPI) en: http://localhost:8001/docs 

### Estructura del Proyecto

TravelSmart-AI-API/
| Carpeta / Archivo     | Descripción                                               |
| --------------------- | --------------------------------------------------------- |
| `📂 alembic/`         | Configuración y versiones de migraciones de **Alembic**   |
| `└── 📂 versions/`    | Archivos de migración generados automáticamente           |
| `📂 graphs/`          | Definiciones de grafos de **LangGraph** (agentes de IA)   |
| `📂 models/`          | Modelos de **SQLAlchemy** (esquema de la base de datos)   |
| `📂 prompts/`         | Plantillas de **prompts** para los modelos LLM            |
| `📂 routes/`          | Endpoints de la API (routers de **FastAPI**)              |
| `📂 schemas/`         | Modelos de **Pydantic** para validación de datos          |
| `📂 services/`        | Lógica de negocio (separada de los endpoints)             |
| `📂 tools/`           | Herramientas personalizadas para agentes de **LangChain** |
| `📂 utils/`           | Funciones de utilidad (LLM, JWT, email, etc.)             |
| `📄 env.example`      | Archivo de ejemplo para configurar variables de entorno   |
| `📄 alembic.ini`      | Configuración principal de Alembic                        |
| `📄 database.py`      | Configuración de conexión y sesión de **SQLAlchemy**      |
| `📄 main.py`          | Punto de entrada principal de la aplicación **FastAPI**   |
| `📄 requirements.txt` | Lista de dependencias del proyecto en Python              |

### Endpoints Principales

Esta API provee varios endpoints para la gestión de viajes. Para una lista completa y detallada, consulta la [documentación de Swagger](https://www.google.com/search?q=http://localhost:8001/docs) (mientras el servidor esté corriendo).

🔐 Autenticación (/auth/...)

POST /auth/register
👉 Registro de nuevos usuarios.

POST /auth/login
👉 Login con email/contraseña (retorna JWT).

GET /auth/google
👉 Inicio de sesión con Google (OAuth).

🧳 Itinerarios (/api/itineraries/...)

POST /api/itineraries/generate
👉 Genera un nuevo itinerario (input principal de la IA).

GET /api/itineraries/{itinerary_id}
👉 Obtiene un itinerario específico.

GET /api/itineraries/session/{session_id}
👉 Obtiene todos los itinerarios de una sesión de usuario.

🧠 Test del Viajero (/api/traveler-test/...)

GET /api/traveler-test/questions
👉 Obtiene todas las preguntas del test.

POST /api/traveler-test/submit
👉 Envía las respuestas del test y calcula el tipo de viajero.

📄 Análisis de Documentos (/api/document-analyzer/...)

POST /api/document-analyzer/analyze
👉 Recibe un archivo (PDF, PNG, etc.) y extrae información de la reserva.

## Esquema base de datos

```mermaid
erDiagram
    Users {
        UUID id PK
        string email UK
        string password_hash
        string username UK
        string display_name
        UUID traveler_type_id FK
        string status
        string role
        bool email_verified
    }

    TravelerTypes {
        UUID id PK
        string name UK
        string description
        string prompt_description
    }

    UserTravelerTests {
        UUID id PK
        UUID user_id FK
        UUID traveler_type_id FK
        datetime started_at
        datetime completed_at
    }

    Questions {
        UUID id PK
        string question
        int order
        string category
        bool multi_select
    }

    QuestionOptions {
        UUID id PK
        UUID question_id FK
        string option
    }

    UserAnswers {
        UUID id PK
        UUID user_traveler_test_id FK
        UUID question_option_id FK
    }

    QuestionOptionScores {
        UUID id PK
        UUID question_option_id FK
        UUID traveler_type_id FK
        int score
    }

    Itineraries {
        UUID itinerary_id PK
        string user_id FK "Nullable"
        UUID session_id "Nullable"
        string trip_name
        json details_itinerary
        string status
        string visibility
    }

    Users ||--o{ UserTravelerTests : "takes"
    Users ||--o{ Itineraries : "creates"
    TravelerTypes ||--|{ Users : "has a"
    TravelerTypes ||--o{ UserTravelerTests : "results in"
    UserTravelerTests ||--|{ UserAnswers : "is composed of"
    Questions ||--|{ QuestionOptions : "has"
    QuestionOptions ||--|{ UserAnswers : "is chosen in"
    QuestionOptions ||--o{ QuestionOptionScores : "has"
    TravelerTypes ||--o{ QuestionOptionScores : "is scored by"
```

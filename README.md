# Molecules API 🧪

This is a high-performance, asynchronous API for storing, managing, and searching chemical molecules.

It is built with a modern Python stack and is fully containerized with Docker, allowing for easy setup and development. The API supports standard CRUD operations and a powerful, asynchronous substructure search using RDKit and Celery.

## Features

FastAPI: For a high-speed, modern RESTful API.

PostgreSQL: As the primary relational database, managed with asyncpg.

SQLAlchemy 2.0: For asynchronous ORM and database communication.

Alembic: For managing database migrations.

RDKit: For all core cheminformatics logic, including substructure searching.

Celery: For running heavy search tasks asynchronously in the background.

Redis: Serves as both the Celery broker and a caching layer.

Docker & Docker Compose: Fully containerized for one-command setup.

Layered Architecture: Clear separation of concerns (Router, Service, Repository).

## Project Structure

The project uses a layered architecture to separate concerns:

.
├── alembic/           # Database migration scripts
├── logs/              # Persistent log files
├── src/               # All Python source code
│   ├── core/          # Core app logic: config, db, redis, celery
│   ├── molecules/     # Feature module: routers, services, models, tasks
│   └── main.py        # Main FastAPI app entrypoint
├── tests/             # Unit and integration tests
├── alembic.ini        # Alembic configuration
├── .env.example       # Example environment variables
├── docker-compose.yml # Main Docker orchestration file
├── Dockerfile         # Docker build file for the app/worker
└── requirements.txt   # Python dependencies


## 🚀 Getting Started (First-Time Launch)

Follow these steps to get the entire application stack running on your local machine.

### Prerequisites

Docker

Docker Compose

Git

### Step 1: Clone the Repository

git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name


### Step 2: Create the Configuration File

Copy the example environment file. The default values are already set up to work with Docker Compose.

cp .env.example .env


### Step 3: Create the Initial Database Migration

This is a critical one-time step. We must create the first migration script before the app runs.

Start only the database so Alembic can connect to it:

docker-compose up -d postgres_db


(Wait 10-15 seconds for the database to initialize)

Generate the migration script. This command runs Alembic inside a new container, which will inspect your models.py file and create the initial migration script in alembic/versions/.

docker-compose run --rm app python -m alembic revision --autogenerate -m "Initial molecules table"


(You will see a new file appear in alembic/versions/)

### Step 4: Build and Run the Full Application

Now you can build the images and run all services (Nginx, FastAPI, Celery, Redis, Postgres) at once.

docker-compose up --build

The app container will start, and its startup command will automatically run alembic upgrade head, applying the migration you just created.

You should see logs from all services. Once the app logs show Application startup complete, the API is live.
# Molecules API 🧪

[![Build Status](https://img.shields.io/your_ci_badge_url)](https://github.com/your-username/your-repo-name/actions)
[![Coverage](https://img.shields.io/codecov/c/github/your-username/your-repo-name)](https://codecov.io/gh/your-username/your-repo-name)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


This is a high-performance, asynchronous API for storing, managing, and searching chemical molecules.

It is built with a modern Python stack and is fully containerized with Docker, allowing for easy setup and development. The API supports standard CRUD operations and a powerful, asynchronous substructure search using RDKit and Celery.

## ✨ Features

* 🚀 **High-Speed API:** Built with **FastAPI** for a high-performance, modern RESTful API with automatic OpenAPI (Swagger) documentation.
* 🐘 **Async Database:** Fully asynchronous communication with **PostgreSQL** using **SQLAlchemy 2.0** and `asyncpg`.
* 🔬 **Powerful Cheminformatics:** **RDKit** for all core chemical logic, including substructure searching and molecule validation.
* ⏳ **Asynchronous Tasks:** Heavy search operations are offloaded to **Celery** workers, keeping the API responsive.
* 💾 **Broker & Cache:** **Redis** serves as both the Celery message broker and a high-speed caching layer.
* 🐳 **Fully Containerized:** **Docker & Docker Compose** for a one-command setup of all services (API, worker, database, broker).
* 🏗️ **Clean Architecture:** A clear, layered architecture separates concerns (Router, Service, Repository) for maintainability.
* 🔄 **Database Migrations:** **Alembic** for managing database schema changes.

## 🏗️ Project Structure

The project uses a layered architecture to separate concerns:

. ├── alembic/ # Database migration scripts ├── logs/ # Persistent log files ├── src/ # All Python source code │ ├── core/ # Core app logic: config, db, redis, celery │ ├── molecules/ # Feature module: routers, services, models, tasks │ └── main.py # Main FastAPI app entrypoint ├── tests/ # Unit and integration tests ├── alembic.ini # Alembic configuration ├── .env.example # Example environment variables ├── docker-compose.yml # Main Docker orchestration file ├── Dockerfile # Docker build file for the app/worker └── requirements.txt # Python dependencies


## 🚀 Getting Started

Follow these steps to get the entire application stack running on your local machine.

### Prerequisites

* Docker
* Docker Compose
* Git

### 1. Clone & Configure

First, clone the repository and create your local environment file.

```bash
# Clone the repo
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name

# Create the .env file from the example
cp .env.example .env
The default values in .env are already set up to work with the docker-compose.yml file.
```

### 2. Generate Initial Database Migration

This is a crucial one-time step. We must create the first migration script before the app runs.

```bash
# 1. Start only the database service in the background
docker-compose up -d postgres_db

# 2. Wait 10-15 seconds for the database to initialize...

# 3. Run Alembic inside a new, temporary container.
# This inspects your models and creates the initial migration script.
docker-compose run --rm app alembic revision --autogenerate -m "Initial molecules table"
You will see a new file appear in the alembic/versions/ directory.
```

### 3. Launch the Full Application

Now you can build the images and run all services (API, Celery worker, Redis, and Postgres) at once.

```bash
docker-compose up --build
```
The API container's startup command is configured to automatically run alembic upgrade head, applying the migration you just created.

You should see logs from all services. Once the app logs show "Application startup complete", the API is live.


## 📚 API Documentation
Once the application is running, you can access the interactive API documentation (powered by Swagger UI and ReDoc) at:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

## 🧪 Running Tests
The tests/ directory contains unit and integration tests. To run the test suite, execute pytest inside a new app container:

```bash
# This command starts a new container, runs pytest, and then removes it
docker-compose run --rm app pytest
```
## 🔄 Database Migrations (After Setup)
Any time you change the SQLAlchemy models (e.g., in src/molecules/models.py), you must create a new migration.

```bash
# 1. Ensure the database is running
docker-compose up -d postgres_db

# 2. Generate the new migration script (replace message)
docker-compose run --rm app alembic revision --autogenerate -m "Add new column to molecules"

# 3. Apply the migration
# You can either run the command below OR just restart the app
docker-compose run --rm app alembic upgrade head

# Alternatively, just restart the app to apply
docker-compose up --build
```
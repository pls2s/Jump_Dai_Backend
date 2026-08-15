# SkillSync AI Server

A scalable FastAPI backend foundation for SkillSync AI, a learning platform for creators and learners. This initial version provides project organization and a small working API surface without business logic or external integrations.

## Tech stack

- Python
- FastAPI
- Pydantic Settings
- PostgreSQL / Supabase (planned)
- RAG and LLM integrations (planned)
- Docker (starter development container included)

## Project structure

```text
skillsync-server/
├── app/
│   ├── api/          # API router and feature route modules
│   ├── core/         # Environment configuration and future security utilities
│   ├── database/     # Future database session and ORM base
│   ├── models/       # Future persistence models
│   ├── schemas/      # Future request and response schemas
│   ├── services/     # Future business, AI, document, and RAG services
│   ├── utils/        # Shared helpers
│   └── main.py       # FastAPI application entry point
├── tests/            # API tests
├── .env.example      # Environment-variable template
├── Dockerfile        # Development-ready container image
└── requirements.txt  # Python dependencies
```

## Setup

```bash
cd skillsync-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run locally

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Run tests

```bash
pytest
```

## Roadmap

Authentication, database and Supabase integration, document processing, AI-generated learning content, RAG, personalized learning, and assessments will be added in later iterations.

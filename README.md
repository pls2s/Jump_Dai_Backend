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

Use Python `3.9.6` (the project version recorded in `.python-version`), then:

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

## Mock authentication flow

For local frontend integration, use the temporary mock auth API described in
[docs/mock-auth-flow.md](docs/mock-auth-flow.md). It includes the demo accounts,
the register → verify → workspace flow, and testing instructions.

## Mock knowledge-upload flow

Function 2 is documented in
[docs/mock-knowledge-upload-flow.md](docs/mock-knowledge-upload-flow.md). A Creator
first configures the knowledge-upload course context, then adds file or URL
knowledge sources. `ADVANCED` courses expose `certificate_available: true` in their
response; Function 2 does not issue certificates.

## Mock creator-dashboard flow

Function 9 is documented in
[docs/mock-creator-dashboard-flow.md](docs/mock-creator-dashboard-flow.md). A Creator
can view learner counts, progress, completion, scores, error/gap analysis, course
improvement insights, filters, and CSV/JSON report exports for owned courses.

## Roadmap

Authentication, database and Supabase integration, document processing, AI-generated learning content, RAG, personalized learning, and assessments will be added in later iterations.

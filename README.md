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

## Mock knowledge-processing flow

Function 3 is documented in
[docs/mock-knowledge-processing-flow.md](docs/mock-knowledge-processing-flow.md). A
Creator can process TXT, Markdown, or selectable-text PDF sources into local chunks,
inspect source citations, and use deterministic keyword retrieval. It intentionally
does not generate embeddings or fetch URL content yet.

## Typhoon course-generation flow

Function 4 is documented in
[docs/typhoon-course-generation-flow.md](docs/typhoon-course-generation-flow.md). A
Creator can send processed course chunks to Typhoon and receive a source-cited,
creator-reviewable learning-path draft through `POST /api/courses/{course_id}/generate`.
Set `TYPHOON_API_KEY` in `.env` before calling the endpoint.

## Creator review and verification flow

Function 5 is documented in [docs/creator-review-flow.md](docs/creator-review-flow.md).
A Creator can review and edit a generated learning path, then verify it. This moves
the course from `WAITING_VERIFICATION` to `VERIFIED`; publishing is a later function.

## Course publication and public catalog flow

Function 6 is documented in [docs/course-publication-flow.md](docs/course-publication-flow.md).
A Creator can publish only a `VERIFIED` course. Anyone can then browse the resulting
catalog through `GET /api/catalog/courses` and `GET /api/catalog/courses/{course_id}`.

## Mock creator-dashboard flow

Function 9 is documented in
[docs/mock-creator-dashboard-flow.md](docs/mock-creator-dashboard-flow.md). A Creator
can view learner counts, progress, completion, scores, error/gap analysis, course
improvement insights, filters, and CSV/JSON report exports for owned courses.

## Mock Personalized Learning Path flow

Function 9.5 is documented in
[docs/mock-personalized-learning-path-flow.md](docs/mock-personalized-learning-path-flow.md).
A Learner can save learning goals and styles, submit a pre-assessment, review gap
analysis, generate a score-matched path, and adapt that path using later results.

## Mock Skill Evidence / Portfolio flow

Function 9.7 is documented in
[docs/mock-skill-portfolio-flow.md](docs/mock-skill-portfolio-flow.md). A Learner can
record practical evidence, receive verified skills with competency levels, share a
portfolio, and publicly verify a Digital Badge or Certificate.

## Roadmap

Authentication, database and Supabase integration, document processing, AI-generated learning content, RAG, and full production assessment integrations will be added in later iterations.

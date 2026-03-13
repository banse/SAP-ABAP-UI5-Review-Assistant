# SAP ABAP/UI5 Review Assistant

Automated code review assistant for SAP ABAP and UI5 artifacts. Accepts code snippets, CDS views, RAP behavior definitions, UI5 XML views, and controller files, then returns structured findings (best-practice violations, performance issues, security concerns, naming conventions).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dev server
uvicorn app.main:app --reload

# Run tests
python3 -m pytest tests/ -q
```

## Architecture

```
app/
  api/          # FastAPI route handlers
  db/           # SQLAlchemy async models, connection, repository
  engines/      # Review engine orchestration (classification, analysis)
  rules/        # Frozen dataclass rule definitions (ABAP, CDS, UI5, RAP)
  models/       # Pydantic v2 request/response schemas
  formatter/    # Output formatting (markdown, structured JSON, bilingual)
static/         # Single-page frontend (HTML + CSS + vanilla JS)
tests/          # pytest-asyncio test suite
```

## Key Conventions

- **Rules**: frozen dataclasses — immutable, easily testable, serialisable
- **Schemas**: Pydantic v2 BaseModel for all API request/response shapes
- **Bilingual**: all user-facing text supports DE/EN toggle (data-i18n attributes in HTML, TRANSLATIONS dict in JS)
- **DB optional**: app starts without PostgreSQL; graceful degradation via `connection.py`
- **Sibling projects**: architecture mirrors SAP Field-Change Accelerator and SAP RAP-FIORI Skeleton Generator in the same toolkit

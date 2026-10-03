# Forms Builder - Technical Architecture

## Overview
Forms Builder is a lightweight, self-hosted form endpoint/builder built as an alternative to OhMyForm (archived Oct 2024) and Formbricks (heavy, ~300MB RAM). It provides form creation, submission handling, embeddable forms, and spam protection — all in a single Python + SQLite container (~50MB RAM).

## Technology Stack
- **Language**: Python 3.11
- **Framework**: FastAPI (async)
- **Database**: SQLite (async via SQLAlchemy + aiosqlite)
- **Templating**: Jinja2
- **Container**: Docker (single container, ~50MB image, ~50MB RAM)
- **Deployment**: Docker Compose on port 5003

## Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                        Client Browser                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS/HTTP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Forms Builder (5003)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   FastAPI    │  │  Jinja2      │  │   SQLite DB      │  │
│  │  Application │──│  Templates   │  │  (forms.db)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│        │                  │                   │              │
│  ┌────▼────┐        ┌────▼────┐        ┌─────▼─────┐       │
│  │ Static  │        │  Rate   │        │  Models   │       │
│  │ Files   │        │ Limiter │        │           │       │
│  │ (JS/CSS)│        │ + Spam  │        │ Form,     │       │
│  └─────────┘        │ Protection    │ Submission│       │
│                     └─────────┘        └───────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. FastAPI Application (`main.py`)
- Async lifespan handler for DB initialization/cleanup
- Rate limiter (10 req/60s per IP by default)
- Spam protection: honeypot field + keyword detection
- Template rendering for admin UI and embeddable forms
- REST API endpoints for form CRUD and submissions

### 2. Database Models (`models.py`)
```python
Form: id, name, description, fields (JSON), email/webhook config, spam settings
FormSubmission: id, form_id, data (JSON), submitted_at, honeypot_triggered
SubmissionFile: id, submission_id, filename, content_type, data (BLOB)
```

### 3. Services Layer (`services.py`)
- `create_form()` - Create form with validation
- `get_form()` - Retrieve form by ID
- `list_forms()` - List all forms with submission counts
- `submit_form()` - Store submission, run spam checks
- `get_submissions()` - Paginated submission listing

### 4. Spam Protection (`spam_protection.py`)
- **Honeypot**: Hidden field (`website` by default) — bots fill it, humans don't
- **Keyword scoring**: Suspicious terms (viagra, crypto, casino, etc.)
- **Rate limiting**: In-memory sliding window per client IP
- Returns `SpamResult(is_spam, honeypot_triggered, score)`

### 5. Notifications (`notifications.py`)
- Email notifications (SMTP)
- Webhook notifications (POST JSON)
- Fire-and-forget async execution

## API Endpoints

### Public (No Auth)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` `/healthz` | Health checks |
| GET | `/embed/{form_id}.js` | Embeddable JS snippet |
| GET | `/embed/{form_id}` | Embeddable HTML form |
| POST | `/api/forms/{form_id}/submit` | Submit form (spam protected) |

### Admin UI (HTML)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard |
| GET | `/forms` | List forms |
| GET/POST | `/forms/new` | Create form |
| GET/POST | `/forms/{id}/edit` | Edit form |
| POST | `/forms/{id}/delete` | Delete form |
| GET | `/forms/{id}/submissions` | View submissions |

### Admin API (JSON)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/forms` | Create form |
| GET | `/api/forms` | List forms |
| GET | `/api/forms/{id}` | Get form |
| GET | `/api/forms/{id}/submissions` | List submissions |

## Embeddable Form Flow
1. User adds `<div id="forms-builder-{form_id}"></div>` to their page
2. User adds `<script src="https://domain/embed/{form_id}.js"></script>`
3. JS fetches `/embed/{form_id}` → renders HTML form into div
4. Form submit → JS posts to `/api/forms/{form_id}/submit`
5. Success → shows "Thank you" message in place of form

## Security Considerations
- **Honeypot field**: Catches basic bots
- **Rate limiting**: Per-IP sliding window (configurable)
- **Input validation**: Pydantic schemas on all inputs
- **SQL injection**: SQLAlchemy ORM (parameterized queries)
- **XSS**: Jinja2 auto-escaping in templates
- **CSRF**: Not needed for embeddable forms (public endpoints)
- **File uploads**: Stored as BLOB in DB, size limits enforced

## Deployment
```yaml
# docker-compose.yml
services:
  forms-builder:
    build: ./source
    ports: ["5003:5003"]
    volumes: ["./data:/app/data"]
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/forms.db
      - SMTP_HOST=smtp.example.com  # optional
      - SMTP_PORT=587
      - SMTP_USER=
      - SMTP_PASSWORD=
      - SMTP_FROM=noreply@example.com
```

## Data Persistence
- SQLite database at `/app/data/forms.db` (Docker volume)
- File uploads stored in database as BLOBs
- Backup: `sqlite3 forms.db .dump > backup.sql`

## Scaling Considerations
- Single container design (no horizontal scaling needed for target use case)
- SQLite handles ~100 concurrent writers, 1000+ readers
- For higher scale: migrate to PostgreSQL, add Redis for rate limiting
- In-memory rate limiter resets on container restart (acceptable for spam protection)

## Key Differentiators
1. **Python + SQLite** — No Node.js/Go/PHP, familiar to Python developers
2. **Single container** — ~50MB RAM vs Formbricks ~300MB
3. **Embeddable JS** — Drop-in replacement for OhMyForm
4. **No external deps** — No Redis, no PostgreSQL, no message queue
5. **Spam protection built-in** — Honeypot + keyword scoring
6. **Open source (MIT)** — No AGPL restrictions like Statping

## File Structure
```
source/
├── main.py              # FastAPI app, routes
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── services.py          # Business logic
├── database.py          # DB connection
├── spam_protection.py   # Honeypot + keyword scoring
├── notifications.py     # Email/webhook
├── config.py            # Settings
├── templates/           # Jinja2 templates
│   ├── index.html
│   ├── forms_list.html
│   ├── form_editor.html
│   ├── embed_form.html
│   ├── compare.html
│   └── submissions_list.html
├── static/              # Embeddable JS/CSS
│   ├── embed.css
│   └── embed.js
├── docs/
│   └── ohmyform-alternative.md  # Comparison page content
├── requirements.txt
├── Dockerfile
├── entrypoint.sh
└── pytest.ini
```

## Testing
```bash
# Run tests
cd /opt/autonomous-factory/projects/forms-builder
pytest -v
# 17/17 tests passing (as of Cycle 713)
```

## Monitoring
- Health endpoints: `/health`, `/healthz` (both return `{"status": "healthy", "service": "forms-builder"}`)
- Logs: Structured JSON via `docker logs forms-builder`
- Metrics: Submission counts via `/api/forms` admin endpoint

## Future Enhancements (Post-Validation)
- Multi-user support with authentication
- Form analytics dashboard
- Conditional logic in forms
- File upload to S3/compat instead of DB
- reCAPTCHA/hCaptcha integration
- Translation/i18n support
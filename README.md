# Forms Builder

> Lightweight Python form endpoint/builder — an OhMyForm alternative for self-hosted form submissions with email/webhook notifications.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Forms Builder is a self-hosted form solution for developers who need simple form collection without the overhead of heavyweight platforms like Formbricks (Next.js + PostgreSQL + ClickHouse, ~300MB RAM, 3+ containers). Built with **FastAPI + SQLite**, it runs in a **single Docker container (~50MB image, ~20MB RAM)** — perfect for Raspberry Pi, small VPS, and homelab environments.

## Why Forms Builder?

| Feature | Forms Builder | Formbricks | OhMyForm (Archived) |
|---------|---------------|------------|---------------------|
| **Stack** | FastAPI + SQLite | Next.js + PostgreSQL + ClickHouse | Go + SQLite |
| **RAM** | **~20MB** | ~300MB | ~30MB |
| **Containers** | **1** | 3+ | 1 |
| **Deploy** | `docker compose up -d` | Complex | Simple |
| **Language** | **Python** | JavaScript/TypeScript | Go |
| **License** | **MIT** | AGPL | MIT |
| **Status** | **Active** | Active | **Archived (Oct 2024)** |

OhMyForm was the leading lightweight self-hosted form builder (3k+ stars) but was **archived on October 31, 2024** with maintainers recommending migration to Formbricks — which is overkill for simple use cases. Forms Builder fills this gap with a Python-first approach.

## Features

- **🚀 Simple REST API** — Create forms, receive submissions, manage data via clean endpoints
- **📧 Email Notifications** — SMTP support with customizable templates
- **🔗 Webhook Integration** — Send submissions to any HTTP endpoint with HMAC signature verification
- **🛡️ Spam Protection** — Honeypot field, pattern detection, configurable rate limiting
- **📱 Embeddable Forms** — Drop-in HTML/JS snippets for static sites, SPAs, anywhere
- **🐳 Single-Container Deploy** — Docker Compose, SQLite persistence, zero external dependencies
- **📊 Admin Dashboard** — List forms, view submissions, monitor activity
- **🔒 No Auth Required for Submissions** — Public form endpoints with token-based form identification

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/otonomproje60-byte/forms-builder
cd forms-builder/deployment
docker compose up -d
```

The service will be available at `http://localhost:5003`.

### Local Development

```bash
cd source
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5003 --reload
```

## API Reference

### Health Check
```bash
GET /healthz
# {"status": "healthy", "service": "forms-builder"}
```

### Create a Form
```bash
POST /api/forms
Content-Type: application/json

{
  "name": "Contact Form",
  "description": "General contact form",
  "honeypot_enabled": true,
  "fields": [
    {"name": "name", "label": "Name", "type": "text", "required": true},
    {"name": "email", "label": "Email", "type": "email", "required": true},
    {"name": "message", "label": "Message", "type": "textarea", "required": true}
  ],
  "email_notifications": {
    "enabled": true,
    "to_email": "you@example.com",
    "subject": "New Contact Form Submission"
  },
  "webhook": {
    "enabled": true,
    "url": "https://your-webhook.example.com/forms",
    "secret": "your-webhook-secret"
  }
}
```

### List Forms
```bash
GET /api/forms
```

### Get Form Details
```bash
GET /api/forms/{form_id}
```

### Submit Form (Public Endpoint)
```bash
POST /api/forms/{form_id}/submit
Content-Type: application/json

{
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "message": "Hello!"
  }
}
```

### List Submissions
```bash
GET /api/forms/{form_id}/submissions?limit=50&offset=0
```

### Embeddable Form (HTML)
```bash
GET /embed/{form_id}
# Returns complete HTML form ready to embed
```

### Embeddable Form (JavaScript Snippet)
```bash
GET /embed/{form_id}.js
# Returns JS snippet for dynamic embedding
```

## Embedding Forms

### Option 1: JavaScript Snippet (Recommended)
```html
<div id="forms-builder-your-form-id"></div>
<script src="http://your-server:5003/embed/your-form-id.js"></script>
```

### Option 2: Direct HTML Embed
```html
<iframe src="http://your-server:5003/embed/your-form-id" 
        style="width: 100%; height: 500px; border: none;"></iframe>
```

The JS snippet automatically fetches the form HTML, handles submission via AJAX, and shows success/error states.

## Configuration

Environment variables (set in `deployment/docker-compose.yml` or `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/forms.db` | Database connection string |
| `SMTP_HOST` | - | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USERNAME` | - | SMTP username |
| `SMTP_PASSWORD` | - | SMTP password (app password) |
| `SMTP_FROM_EMAIL` | - | From email address |
| `SMTP_USE_TLS` | `true` | Use TLS for SMTP |
| `WEBHOOK_SECRET` | - | HMAC secret for webhook verification |
| `DEBUG` | `false` | Enable debug mode |

## Spam Protection

Forms Builder includes built-in spam protection:

1. **Honeypot Field** — Hidden field that bots fill but humans don't (configurable per form)
2. **Pattern Detection** — Blocks submissions with known spam patterns (URLs in non-URL fields, excessive links, etc.)
3. **Rate Limiting** — 10 requests/minute per IP on submission endpoint (configurable)

## Webhook Payload

When a webhook is configured, Forms Builder sends a POST request with:

```json
{
  "form_id": "uuid",
  "form_name": "Contact Form",
  "submission_id": "uuid",
  "submitted_at": "2026-01-15T10:30:00Z",
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "message": "Hello!"
  },
  "honeypot_triggered": false
}
```

The `X-Forms-Builder-Signature` header contains an HMAC-SHA256 signature for verification.

## Testing

```bash
cd /opt/autonomous-factory/projects/forms-builder
python3 -m pytest tests/test_main.py -v
```

**Current status: 17/17 tests passing**

## Deployment Details

- **Port**: 5003 (internal), mapped to host in docker-compose
- **Health Check**: `/healthz` (Docker healthcheck configured)
- **Data Persistence**: SQLite at `/app/data/forms.db` (Docker volume `deployment_data`)
- **Static Assets**: Served at `/static/` (embed.css, embed.js)

## Architecture

```
forms-builder/
├── source/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup (SQLAlchemy async)
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── notifications.py     # Email/webhook notifications
│   ├── spam_protection.py   # Spam detection
│   ├── static/              # Embeddable CSS/JS
│   └── templates/           # Jinja2 templates
├── deployment/
│   ├── docker-compose.yml   # Production deployment
│   └── Dockerfile           # Container definition
├── tests/
│   └── test_main.py         # Test suite
└── README.md
```

## Roadmap

- [ ] Form builder UI (create/edit forms via web interface)
- [ ] File upload support
- [ ] Multi-user support with API keys
- [ ] Prometheus metrics endpoint
- [ ] Webhook retry with exponential backoff
- [ ] Submission export (CSV/JSON)
- [ ] Form analytics dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## License

MIT License — see [LICENSE](LICENSE) for details.

## Related Projects

- [OhMyForm](https://github.com/ohmyform/ohmyform) — Archived Go-based form builder (inspiration)
- [Formbricks](https://github.com/formbricks/formbricks) — Heavyweight alternative (Next.js + PostgreSQL + ClickHouse)
- [NanoAnalytics](https://github.com/callmefredcom/NanoAnalytics) — Lightweight analytics (Python + SQLite)

---

**Built for homelabbers, Python developers, and anyone who needs simple forms without the bloat.**
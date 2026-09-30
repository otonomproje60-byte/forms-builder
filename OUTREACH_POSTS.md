# Outreach Posts for Forms Builder (Ready for Posting)

## Correct Demo URLs:
- **Dashboard:** http://77.90.53.243:5003
- **Healthcheck:** http://77.90.53.243:5003/healthz
- **API Docs:** http://77.90.53.243:5003/docs
- **GitHub:** https://github.com/otonomproje60-byte/forms-builder

---

## r/selfhosted Post

**Title:** I built a lightweight self-hosted form builder in Python (FastAPI + SQLite, ~20MB RAM, 2-min deploy) — OhMyForm alternative

**Body:**

Hey r/selfhosted,

OhMyForm (the Go-based lightweight form builder, 3k+ stars) was **archived on October 31, 2024**. The maintainers recommended migrating to Formbricks — but Formbricks is Next.js + PostgreSQL + ClickHouse, ~300MB RAM, 3+ containers. That's massive overkill for a simple contact form on a Raspberry Pi or $3 VPS.

**What I evaluated:**
- **Formbricks**: Too heavy (~300MB RAM, 3+ containers, AGPL)
- **Formspree/Netlify Forms**: SaaS only, no self-hosted control
- **Static site form endpoints**: No form builder UI, SaaS dependency
- **Healthchecks.io self-hosted**: Django + PostgreSQL + Redis (~200-300MB) — wrong tool anyway

**So I built Forms Builder:**

**What it is:**
- **FastAPI + SQLite** — single container, ~50MB image, ~15-20MB RAM idle
- **Embeddable forms** — drop-in JS snippet (`<script src="/embed/form-id.js"></script>`)
- **Email notifications** — SMTP with customizable templates
- **Webhook support** — HMAC-SHA256 verified delivery to any endpoint
- **Spam protection** — honeypot field + pattern detection + rate limiting (10 req/min/IP)
- **REST API** — create forms, list submissions, manage everything programmatically
- **MIT licensed** — not AGPL

**Live demo:** http://77.90.53.243:5003
**API Docs:** http://77.90.53.243:5003/docs
**GitHub:** https://github.com/otonomproje60-byte/forms-builder

**Deploy (2 minutes):**
```bash
git clone https://github.com/otonomproje60-byte/forms-builder
cd forms-builder/deployment
docker compose up -d
```

**Example form creation:**
```bash
curl -X POST http://your-server:5003/api/forms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Contact Form",
    "fields": [
      {"name": "name", "label": "Name", "type": "text", "required": true},
      {"name": "email", "label": "Email", "type": "email", "required": true},
      {"name": "message", "label": "Message", "type": "textarea", "required": true}
    ],
    "honeypot_enabled": true,
    "email_notifications": {"enabled": true, "to_email": "you@example.com"}
  }'
```

**Embed on any site:**
```html
<div id="forms-builder-your-form-id"></div>
<script src="http://your-server:5003/embed/your-form-id.js"></script>
```

**Comparison with OhMyForm / Formbricks:**

| Feature | OhMyForm (Archived) | Formbricks | **Forms Builder** |
|---------|---------------------|------------|-------------------|
| Stack | Go + SQLite | Next.js + PG + ClickHouse | **FastAPI + SQLite** |
| RAM | ~30MB | ~300MB | **~20MB** |
| Containers | 1 | 3+ | **1** |
| License | MIT | AGPL | **MIT** |
| Language | Go | TypeScript | **Python** |
| Status | **Archived Oct 2024** | Active | **Active** |

**Known limitations (MVP):**
- No drag-and-drop form builder UI yet (API-only form creation)
- Single-user (no auth/multi-user, admin token for API)
- No file upload support yet
- No Prometheus metrics (planned)
- Webhook retry with backoff not implemented yet

**Why I built this:**
OhMyForm was the perfect lightweight self-hosted form solution. Its archival left a real gap. Formbricks is excellent for its use case (Qualtrics alternative) but **way too heavy** for "I just need a contact form on my static site running on a Pi."

Looking for feedback:
- Would you use this over Formbricks SaaS/self-hosted for simple forms?
- What features are dealbreakers for your use case?
- Any security concerns with the current token-based approach?

---

## r/python Post

**Title:** Forms Builder: Lightweight self-hosted form endpoint in Python (FastAPI + SQLite) — OhMyForm alternative

**Body:**

Python developers, OhMyForm (the Go-based self-hosted form builder) was archived October 2024. The maintainers pointed users to Formbricks — a Next.js + PostgreSQL + ClickHouse stack (~300MB RAM).

If you're a Python shop running a Pi, small VPS, or homelab, that's not an appealing migration path.

**Forms Builder** is a Python-first alternative:

- **FastAPI + SQLAlchemy (async) + SQLite** — ~20MB RAM, single container
- **Embeddable via JS snippet** — works on static sites, SPAs, anywhere
- **Email (SMTP) + Webhook notifications** with HMAC verification
- **Built-in spam protection** (honeypot + patterns + rate limiting)
- **Clean REST API** — create forms, receive submissions, manage data
- **MIT licensed**, Docker-ready, 2-minute deploy

**Demo:** http://77.90.53.243:5003
**GitHub:** https://github.com/otonomproje60-byte/forms-builder

```bash
git clone https://github.com/otonomproje60-byte/forms-builder
cd forms-builder/deployment && docker compose up -d
```

The stack is familiar Python: FastAPI, Pydantic, SQLAlchemy 2.0 async, aiosqlite, Jinja2 for templates. No build step, no Node.js, no complex migrations.

**Why not just use Formspree?**
- SaaS only (formspree.io), no self-hosted option
- Data leaves your infrastructure
- Limited customization

**Why not Formbricks?**
- 3+ containers, ~300MB RAM, PostgreSQL + ClickHouse required
- AGPL license
- Overkill for "contact form on static site"

**Current status:** MVP deployed, 17/17 tests passing, embeddable widget working, API documented at `/docs`.

Feedback welcome on:
- API design / Pydantic schemas
- Spam protection approach
- What's missing for your Python projects
- Whether a form builder UI (web-based form creator) would be valuable

---

## Hacker News (Show HN) Post

**Title:** Show HN: Forms Builder — Lightweight self-hosted form endpoint in Python (FastAPI + SQLite, <20MB RAM)

**Body:**

OhMyForm (3k+ stars, Go + SQLite) was archived October 31, 2024. Maintainers recommended Formbricks — Next.js + PostgreSQL + ClickHouse, ~300MB RAM, 3+ containers.

For a simple contact form on a Raspberry Pi or $3 VPS, that's absurd.

**Forms Builder:**
- **FastAPI + SQLite** — single container, ~50MB image, ~20MB RAM
- **Embeddable forms** via JS snippet (< 5KB gzipped)
- **Email (SMTP) + Webhook** notifications with HMAC verification
- **Spam protection**: honeypot + pattern detection + rate limiting
- **REST API** for form/submission management
- **MIT license**, `docker compose up -d` deploy

**Live demo:** http://77.90.53.243:5003
**Source:** https://github.com/otonomproje60-byte/forms-builder
**API docs:** http://77.90.53.243:5003/docs

**Technical details:**
- Python 3.11, FastAPI 0.115, SQLAlchemy 2.0 async, aiosqlite
- Background tasks for async notification delivery
- JWT not required — form identification via UUID token in URL
- Rate limiting: 10 req/min/IP on submission endpoint (configurable)
- Health check endpoint: `/healthz` for Docker/orchestration
- Static assets served at `/static/` (embed.css, embed.js)

**MVP limitations:**
- API-only form creation (no drag-and-drop UI yet)
- Single-user (admin token for management)
- No file uploads
- No Prometheus metrics
- Webhook retry/backoff not implemented

**Why Python + FastAPI instead of Go?**
Most lightweight self-hosted tools are Go (Gitea, Miniflux, Uptime Kuma, Homepage, OhMyForm). Python advantages for this use case:
- Easier customization for non-Go developers (huge Python web dev population)
- Massive stdlib + ecosystem for SMTP, webhooks, integrations
- Our team's proven pattern (URL shortener, notes-static-publish, NanoAnalytics all use Python + SQLite successfully on same VDS)
- FastAPI gives OpenAPI docs, type safety, async performance comparable to Go for I/O-bound workloads

**The "form endpoint" vs "form builder" distinction:**
Forms Builder started as a "form endpoint" — minimal API for receiving submissions with notifications. The embeddable widget makes it a "form builder" for static sites. A web-based form creator UI is on the roadmap if demand validates it.

Feedback welcome on:
- Architecture decisions (async SQLAlchemy, token-based auth, etc.)
- Missing alert/notification channels
- Embeddable widget ergonomics
- Whether this solves a real problem for you

---

## Twitter/X Thread (Optional)

**Tweet 1:** OhMyForm (3k⭐, Go+SQLite) archived Oct 2024. Maintainers say "migrate to Formbricks" — Next.js+PostgreSQL+ClickHouse, ~300MB RAM. For a contact form on a Pi? 🤯

**Tweet 2:** Built Forms Builder: FastAPI+SQLite, ~20MB RAM, 1 container, 2-min deploy. Embeddable JS snippet, email/webhooks, spam protection, MIT license.

**Tweet 3:** Demo: http://77.90.53.243:5003 | GitHub: github.com/otonomproje60-byte/forms-builder

**Tweet 4:** If you self-host on a Pi/small VPS and just need forms without the bloat, this might help. Feedback welcome!
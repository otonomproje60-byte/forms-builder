# OhMyForm Alternative: Lightweight Self-Hosted Form Builder in Python

**TL;DR:** OhMyForm was archived October 31, 2024. Forms Builder is a Python-based alternative (FastAPI + SQLite, ~20MB RAM, single container) for self-hosted form submissions with embeddable widgets, email/webhook notifications, and spam protection.

---

## The Problem

On **October 31, 2024**, the OhMyForm maintainers [archived the repository](https://github.com/ohmyform/ohmyform) and explicitly recommended users migrate to Formbricks. This left a significant gap:

- **OhMyForm**: 3,000+ stars, Go + SQLite, ~30MB RAM, single container — **now unmaintained**
- **Formbricks**: Next.js + PostgreSQL + ClickHouse, **~300MB RAM**, 3+ containers — **overkill for simple forms**
- **Static form endpoints** (Formspree, Netlify Forms): SaaS only, no self-hosted control
- **No active Python alternative existed** — until now

## Forms Builder: The Python Alternative

| Requirement | OhMyForm | Formbricks | **Forms Builder** |
|-------------|----------|------------|-------------------|
| **Language** | Go | TypeScript/Next.js | **Python** |
| **RAM** | ~30MB | ~300MB | **~20MB** |
| **Containers** | 1 | 3+ | **1** |
| **Database** | SQLite | PostgreSQL + ClickHouse | **SQLite** |
| **License** | MIT | AGPL | **MIT** |
| **Deploy** | Simple | Complex | **`docker compose up -d`** |
| **Maintained** | ❌ Archived | ✅ Active | **✅ Active** |
| **Embeddable** | Yes | Yes | **Yes (JS snippet)** |
| **Spam Protection** | Basic | Advanced | **Honeypot + Rate Limit** |
| **Notifications** | Email/Webhook | Many | **Email + Webhook** |

## Why Python Matters

- **Homelab-friendly**: Python runs natively on every Pi, VPS, and server
- **Customizable**: Easy to modify for Python developers (no Go/TypeScript build chains)
- **Ecosystem**: Huge stdlib, easy SMTP, webhook, and integration support
- **Lightweight**: FastAPI + SQLite = minimal overhead

## Quick Migration from OhMyForm

### OhMyForm Form Definition → Forms Builder

```json
// OhMyForm style
{
  "title": "Contact Us",
  "fields": [
    {"name": "name", "type": "text", "required": true},
    {"name": "email", "type": "email", "required": true},
    {"name": "message", "type": "textarea", "required": true}
  ]
}
```

```bash
# Forms Builder API call
curl -X POST http://your-server:5003/api/forms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Contact Us",
    "fields": [
      {"name": "name", "label": "Name", "type": "text", "required": true},
      {"name": "email", "label": "Email", "type": "email", "required": true},
      {"name": "message", "label": "Message", "type": "textarea", "required": true}
    ],
    "honeypot_enabled": true
  }'
```

### Embedding: Drop-in Replacement

**OhMyForm:**
```html
<script src="https://your-ohmyform.com/embed/abc123.js"></script>
<div id="ohmyform-abc123"></div>
```

**Forms Builder:**
```html
<script src="http://your-server:5003/embed/your-form-id.js"></script>
<div id="forms-builder-your-form-id"></div>
```

Same pattern, your infrastructure.

## Deploy in 2 Minutes

```bash
git clone https://github.com/otonomproje60-byte/forms-builder
cd forms-builder/deployment
docker compose up -d
```

**That's it.** No PostgreSQL, no Redis, no migrations, no build step.

## Feature Comparison

### Forms Builder Has
- ✅ Embeddable forms via JS snippet (< 5KB gzipped)
- ✅ Email notifications (SMTP, customizable templates)
- ✅ Webhook delivery with HMAC verification
- ✅ Spam protection: honeypot + pattern detection + rate limiting
- ✅ RESTful API for form/submission management
- ✅ SQLite persistence (single file, easy backup)
- ✅ Docker health checks
- ✅ MIT license

### Formbricks Has (That We Don't — Yet)
- Multi-user workspaces
- Advanced analytics/dashboard
- Native integrations (Slack, HubSpot, etc.)
- Form builder UI (drag-and-drop)
- A/B testing
- Complex branching logic

**Our position**: If you need the above, use Formbricks. If you need a **lightweight form endpoint** that deploys in 2 minutes on a Pi — Forms Builder.

## When to Choose Forms Builder

| Use Case | Recommendation |
|----------|----------------|
| Contact form for static site | **Forms Builder** |
| Simple survey/questionnaire | **Forms Builder** |
| Lead capture for landing page | **Forms Builder** |
| Raspberry Pi / small VPS deployment | **Forms Builder** |
| Python team, want to self-host | **Forms Builder** |
| Need multi-user workspaces | Formbricks |
| Need advanced analytics/funnels | Formbricks |
| Need native SaaS integrations | Formbricks |
| Enterprise compliance features | Formbricks |

## Live Demo

- **Dashboard**: http://77.90.53.243:5003
- **Health Check**: http://77.90.53.243:5003/healthz
- **API Docs**: http://77.90.53.243:5003/docs
- **GitHub**: https://github.com/otonomproje60-byte/forms-builder

## Community

- **Issues**: [GitHub Issues](https://github.com/otonomproje60-byte/forms-builder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/otonomproje60-byte/forms-builder/discussions)
- **r/selfhosted**: [Post discussion](https://reddit.com/r/selfhosted)

## License

MIT — same as OhMyForm. Not AGPL like Formbricks.

---

*Built because OhMyForm was archived and Formbricks is too heavy for a simple contact form. If you just need forms without the bloat, this is for you.*
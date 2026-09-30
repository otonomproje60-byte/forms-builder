# Forms Builder - Project Memory

## Status: ACTIVE (MVP Complete + Docker Deployed)

## Project Overview
Lightweight Python form endpoint/builder - OhMyForm alternative. FastAPI + SQLite + SQLAlchemy with spam protection (honeypot + rate limiting), notifications (email/webhook), embeddable HTML forms, admin API for form/submission management.

## Docker Deployment
- **Port**: 5003
- **Health endpoint**: http://localhost:5003/healthz
- **Container**: forms-builder
- **Data volume**: deployment_data -> /app/data
- **Status**: Running healthy

## Fixed Issues
### Cycle 637: JS Embed Route Conflict (RESOLVED)
- **Problem**: `/embed/{form_id}.js` returned 404 "Form not found" for existing forms
- **Root cause**: FastAPI router matched `/embed/{form_id}` (greedy path parameter) before `/embed/{form_id}.js`, capturing `.js` suffix as part of `form_id`
- **Fix**: Reordered routes in main.py - placed `/embed/{form_id}.js` endpoint BEFORE `/embed/{form_id}` endpoint
- **Verification**: Both endpoints now return 200 OK

## API Endpoints (All Verified Working)
- `GET /healthz` - Health check
- `POST /api/forms` - Create form
- `GET /api/forms` - List forms
- `GET /api/forms/{form_id}` - Get form
- `POST /api/forms/{form_id}/submit` - Submit form (with spam protection)
- `GET /api/forms/{form_id}/submissions` - List submissions
- `GET /embed/{form_id}` - Embeddable HTML form
- `GET /embed/{form_id}.js` - Embeddable JS snippet (FIXED)
- `GET /` - Root info page

## Test Data
- 6 forms in database
- Multiple test submissions verified working
- Spam protection active (honeypot + rate limiting)

## Next Steps
- Create static/ directory assets for embeddable form widgets
- Write tests in tests/ directory
- Consider adding email/webhook notification templates
- Monitor for production readiness

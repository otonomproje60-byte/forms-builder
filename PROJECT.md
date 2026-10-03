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

## Cycle 670 Updates
- **Tests created**: 11 passing tests covering health endpoint, static files (embed.css, embed.js), embed endpoints (404 handling), API endpoints (list, get, submit, submissions), and root endpoint
- **Test location**: `/opt/autonomous-factory/projects/forms-builder/tests/test_main.py`
- **Static assets created**: embed.css and embed.js in source/static/ for embeddable widget support
- **All tests passing**: 11/11 tests pass with pytest

## Cycle 713 Updates
- **Growth phase initiated**: Created growth assets for organic distribution
  - Comprehensive README.md with comparison tables, embed examples, API documentation
  - SEO/comparison content: "Forms Builder: The OhMyForm Alternative" page
  - Community outreach drafts for r/selfhosted, r/python, HN Show HN
- **Market validation evidence strengthened**: OhMyForm archived Oct 2024 (3k+ stars), Formbricks ~300MB RAM/3+ containers/AGPL, zero active Python alternatives
- **Next**: Human posts outreach drafts → monitor for stars/deployments/feedback → iterate based on signals

"""
Forms Builder - Lightweight Python Form Endpoint/Builder
FastAPI application for form submission handling with email/webhook notifications.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, Base, get_db
from models import Form, FormSubmission
from schemas import (
    FormCreate,
    FormResponse,
    FormSubmit,
    SubmissionResponse,
    SubmissionListResponse,
    HealthResponse,
)
from services import (
    create_form,
    get_form,
    list_forms,
    submit_form,
    get_submissions,
)
from notifications import send_notifications
from spam_protection import check_spam, RateLimiter

# Rate limiter instance
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: close engine
    await engine.dispose()


app = FastAPI(
    title="Forms Builder",
    description="Lightweight Python form endpoint/builder - OhMyForm alternative",
    version="0.1.0",
    lifespan=lifespan,
)

# Templates for embeddable form HTML
templates = Jinja2Templates(directory="templates")

# Static files (for embeddable JS/CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Health check endpoint
@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Docker/load balancer."""
    return HealthResponse(status="healthy", service="forms-builder")


# Form management endpoints
@app.post("/api/forms", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_form_endpoint(form: FormCreate, db: AsyncSession = Depends(get_db)):
    """Create a new form."""
    return await create_form(db, form)


@app.get("/api/forms", response_model=list[FormResponse])
async def list_forms_endpoint(db: AsyncSession = Depends(get_db)):
    """List all forms."""
    return await list_forms(db)


@app.get("/api/forms/{form_id}", response_model=FormResponse)
async def get_form_endpoint(form_id: str, db: AsyncSession = Depends(get_db)):
    """Get a form by ID."""
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form


# Form submission endpoint (public)
@app.post("/api/forms/{form_id}/submit", response_model=SubmissionResponse)
async def submit_form_endpoint(
    form_id: str,
    submission: FormSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Submit a form entry. Public endpoint with spam protection."""
    # Rate limiting
    client_ip = request.client.host
    if not rate_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )

    # Spam protection
    spam_result = check_spam(submission.data)
    if spam_result.is_spam:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission blocked by spam protection",
        )

    # Verify form exists
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Store submission
    submission_record = await submit_form(db, form_id, submission.data, spam_result.honeypot_triggered)

    # Send notifications (async, fire-and-forget)
    import asyncio
    asyncio.create_task(send_notifications(form, submission_record, submission.data))

    return SubmissionResponse(
        id=submission_record.id,
        form_id=form_id,
        data=submission_record.data,
        submitted_at=submission_record.submitted_at,
    )


# Submission management endpoints (admin)
@app.get("/api/forms/{form_id}/submissions", response_model=SubmissionListResponse)
async def list_submissions_endpoint(
    form_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List submissions for a form."""
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    submissions, total = await get_submissions(db, form_id, limit, offset)
    return SubmissionListResponse(
        submissions=submissions,
        total=total,
        limit=limit,
        offset=offset,
    )


# Embeddable JS snippet endpoint (MUST come before /embed/{form_id} to avoid route conflict)
@app.get("/embed/{form_id}.js")
async def embed_js(form_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Return embeddable JavaScript snippet for a form."""
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    api_base = str(request.base_url).rstrip("/")
    js_content = f"""
(function() {{
    var formId = '{form_id}';
    var apiBase = '{api_base}';
    var container = document.getElementById('forms-builder-' + formId);
    if (!container) return;

    container.innerHTML = '<div class="forms-builder-form" id="fb-form-' + formId + '"></div>';

    fetch(apiBase + '/embed/' + formId)
        .then(function(r) {{ return r.text(); }})
        .then(function(html) {{
            document.getElementById('fb-form-' + formId).innerHTML = html;
            var form = document.getElementById('fb-form-' + formId).querySelector('form');
            if (form) {{
                form.addEventListener('submit', function(e) {{
                    e.preventDefault();
                    var formData = new FormData(form);
                    var data = Object.fromEntries(formData.entries());
                    fetch(apiBase + '/api/forms/' + formId + '/submit', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ data: data }})
                    }})
                    .then(function(r) {{ return r.json(); }})
                    .then(function(resp) {{
                        if (resp.id) {{
                            form.innerHTML = '<div class="forms-builder-success">Thank you! Your submission has been received.</div>';
                        }} else {{
                            alert('Error: ' + (resp.detail || 'Submission failed'));
                        }}
                    }})
                    .catch(function() {{
                        alert('Network error. Please try again.');
                    }});
                }});
            }}
        }});
}})();
"""
    return HTMLResponse(content=js_content, media_type="application/javascript")


# Embeddable form HTML endpoint
@app.get("/embed/{form_id}", response_class=HTMLResponse)
async def embed_form(form_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Return embeddable HTML form for a given form_id."""
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    return templates.TemplateResponse(
        "embed_form.html",
        {
            "request": request,
            "form": form,
            "api_base": str(request.base_url).rstrip("/"),
        },
    )


# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint with basic info."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "version": "0.1.0"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
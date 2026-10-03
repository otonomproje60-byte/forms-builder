"""
Forms Builder - Lightweight Python Form Endpoint/Builder
FastAPI application for form submission handling with email/webhook notifications.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
import uuid
import schemas

from database import engine, Base, get_db
from models import Form, FormSubmission, SubmissionFile
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
import pathlib
TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Static files (for embeddable JS/CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Health check endpoint
@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Docker/load balancer."""
    return HealthResponse(status="healthy", service="forms-builder")


@app.get("/health", response_model=HealthResponse)
async def health_check_alt():
    """Health check endpoint (alternative path)."""
    return HealthResponse(status="healthy", service="forms-builder")


# ============ FORM BUILDER UI ROUTES ============

# List all forms (admin UI)
@app.get("/forms", response_class=HTMLResponse)
async def forms_list(request: Request, db: AsyncSession = Depends(get_db)):
    """List all forms with submission counts."""
    forms_result = await db.execute(
        select(Form).order_by(desc(Form.created_at))
    )
    forms = forms_result.scalars().all()
    
    # Get submission counts for each form
    forms_with_counts = []
    for form in forms:
        count_result = await db.execute(
            select(func.count(FormSubmission.id)).where(FormSubmission.form_id == form.id)
        )
        submission_count = count_result.scalar() or 0
        forms_with_counts.append({
            "form": form,
            "submission_count": submission_count,
        })
    
    flash = None
    if hasattr(request.state, "flash"):
        flash = request.state.flash
    
    return templates.TemplateResponse(
        "forms_list.html",
        {"request": request, "forms": forms_with_counts, "flash": flash},
    )


# Create form page
@app.get("/forms/new", response_class=HTMLResponse)
async def new_form_page(request: Request):
    """Show create form page."""
    return templates.TemplateResponse(
        "form_editor.html",
        {"request": request, "form": None},
    )


# Create form handler
@app.post("/forms/new", response_class=HTMLResponse)
async def create_form_ui(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle form creation from UI."""
    form_data = await request.form()
    
    # Parse fields
    fields = []
    i = 0
    while True:
        field_name = form_data.get(f"fields[{i}][name]")
        if not field_name:
            break
        field_type = form_data.get(f"fields[{i}][type]", "text")
        field_label = form_data.get(f"fields[{i}][label]", "")
        field_required = form_data.get(f"fields[{i}][required]") == "true"
        field_options = form_data.get(f"fields[{i}][options]", "")
        
        field = {
            "name": field_name,
            "type": field_type,
            "label": field_label,
            "required": field_required,
        }
        if field_options and field_type in ["select", "radio", "checkbox"]:
            field["options"] = [opt.strip() for opt in field_options.split("\n") if opt.strip()]
        
        fields.append(field)
        i += 1
    
    if not fields:
        return templates.TemplateResponse(
            "form_editor.html",
            {"request": request, "form": None, "flash": {"type": "error", "message": "At least one field is required"}},
            status_code=400,
        )
    
    # Create FormCreate schema
    form_create = FormCreate(
        name=form_data.get("name", ""),
        description=form_data.get("description") or None,
        fields=[schemas.FormFieldSchema(**f) for f in fields],
        email_enabled=form_data.get("email_enabled") == "true",
        email_to=form_data.get("email_to") or None,
        email_subject=form_data.get("email_subject") or None,
        webhook_enabled=form_data.get("webhook_enabled") == "true",
        webhook_url=form_data.get("webhook_url") or None,
        honeypot_enabled=form_data.get("honeypot_enabled") == "true",
        honeypot_field_name=form_data.get("honeypot_field_name", "website"),
        rate_limit_enabled=form_data.get("rate_limit_enabled") == "true",
        rate_limit_requests=int(form_data.get("rate_limit_requests", 10)),
        rate_limit_window=int(form_data.get("rate_limit_window", 60)),
    )
    
    try:
        created_form = await create_form(db, form_create)
        return RedirectResponse(url=f"/forms/{created_form.id}/edit?created=1", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "form_editor.html",
            {"request": request, "form": None, "flash": {"type": "error", "message": f"Error creating form: {str(e)}"}},
            status_code=400,
        )


# Edit form page
@app.get("/forms/{form_id}/edit", response_class=HTMLResponse)
async def edit_form_page(form_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Show edit form page."""
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    flash = None
    if request.query_params.get("created"):
        flash = {"type": "success", "message": "Form created successfully!"}
    elif request.query_params.get("saved"):
        flash = {"type": "success", "message": "Form saved successfully!"}
    
    return templates.TemplateResponse(
        "form_editor.html",
        {"request": request, "form": form, "flash": flash},
    )


# Edit form handler
@app.post("/forms/{form_id}/edit", response_class=HTMLResponse)
async def edit_form_ui(
    form_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle form update from UI."""
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    form_data = await request.form()
    
    # Parse fields (similar to create)
    fields = []
    i = 0
    while True:
        field_name = form_data.get(f"fields[{i}][name]")
        if not field_name:
            break
        field_type = form_data.get(f"fields[{i}][type]", "text")
        field_label = form_data.get(f"fields[{i}][label]", "")
        field_required = form_data.get(f"fields[{i}][required]") == "true"
        field_options = form_data.get(f"fields[{i}][options]", "")
        
        field = {
            "name": field_name,
            "type": field_type,
            "label": field_label,
            "required": field_required,
        }
        if field_options and field_type in ["select", "radio", "checkbox"]:
            field["options"] = [opt.strip() for opt in field_options.split("\n") if opt.strip()]
        
        fields.append(field)
        i += 1
    
    if not fields:
        return templates.TemplateResponse(
            "form_editor.html",
            {"request": request, "form": form, "flash": {"type": "error", "message": "At least one field is required"}},
            status_code=400,
        )
    
    # Update form
    form.name = form_data.get("name", form.name)
    form.description = form_data.get("description") or None
    form.fields = fields
    form.email_enabled = form_data.get("email_enabled") == "true"
    form.email_to = form_data.get("email_to") or None
    form.email_subject = form_data.get("email_subject") or None
    form.webhook_enabled = form_data.get("webhook_enabled") == "true"
    form.webhook_url = form_data.get("webhook_url") or None
    form.honeypot_enabled = form_data.get("honeypot_enabled") == "true"
    form.honeypot_field_name = form_data.get("honeypot_field_name", "website")
    form.rate_limit_enabled = form_data.get("rate_limit_enabled") == "true"
    form.rate_limit_requests = int(form_data.get("rate_limit_requests", 10))
    form.rate_limit_window = int(form_data.get("rate_limit_window", 60))
    
    await db.commit()
    await db.refresh(form)
    
    return RedirectResponse(url=f"/forms/{form_id}/edit?saved=1", status_code=303)


# Delete form
@app.post("/forms/{form_id}/delete")
async def delete_form_ui(form_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a form and all its submissions."""
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    await db.delete(form)
    await db.commit()
    
    return RedirectResponse(url="/forms", status_code=303)


# View submissions for a form
@app.get("/forms/{form_id}/submissions", response_class=HTMLResponse)
async def form_submissions(form_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """List submissions for a form (admin UI)."""
    form = await get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    submissions, total = await get_submissions(db, form_id, limit=100, offset=0)
    
    return templates.TemplateResponse(
        "submissions_list.html",
        {"request": request, "form": form, "submissions": submissions, "total": total},
    )


# ============ EXISTING API ROUTES ============

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


# Comparison page (SEO/content)
@app.get("/compare", response_class=HTMLResponse)
async def compare(request: Request):
    """Serve the comparison page from docs/ohmyform-alternative.md."""
    import os
    comparison_path = os.path.join(os.path.dirname(__file__), "docs", "ohmyform-alternative.md")
    try:
        with open(comparison_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = "Comparison page not found."
    return templates.TemplateResponse(
        "compare.html",
        {"request": request, "content": content},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
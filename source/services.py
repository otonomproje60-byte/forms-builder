"""
Business logic services for Forms Builder.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import uuid

from models import Form, FormSubmission, SubmissionFile
from schemas import FormCreate, FormResponse, FormSubmit, SubmissionResponse


async def create_form(db: AsyncSession, form_data: FormCreate) -> FormResponse:
    """Create a new form."""
    form = Form(
        id=str(uuid.uuid4()),
        name=form_data.name,
        description=form_data.description,
        fields=[field.model_dump() for field in form_data.fields],
        email_enabled=form_data.email_enabled,
        email_to=form_data.email_to,
        email_subject=form_data.email_subject,
        webhook_enabled=form_data.webhook_enabled,
        webhook_url=form_data.webhook_url,
        honeypot_enabled=form_data.honeypot_enabled,
        honeypot_field_name=form_data.honeypot_field_name,
        rate_limit_enabled=form_data.rate_limit_enabled,
        rate_limit_requests=form_data.rate_limit_requests,
        rate_limit_window=form_data.rate_limit_window,
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)
    return FormResponse.model_validate(form)


async def get_form(db: AsyncSession, form_id: str) -> Optional[Form]:
    """Get a form by ID."""
    result = await db.execute(select(Form).where(Form.id == form_id))
    return result.scalar_one_or_none()


async def list_forms(db: AsyncSession) -> List[FormResponse]:
    """List all forms."""
    result = await db.execute(select(Form).order_by(desc(Form.created_at)))
    forms = result.scalars().all()
    return [FormResponse.model_validate(f) for f in forms]


async def submit_form(
    db: AsyncSession,
    form_id: str,
    data: dict,
    honeypot_triggered: bool,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> FormSubmission:
    """Store a form submission."""
    submission = FormSubmission(
        id=str(uuid.uuid4()),
        form_id=form_id,
        data=data,
        honeypot_triggered=honeypot_triggered,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def get_submissions(
    db: AsyncSession,
    form_id: str,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[SubmissionResponse], int]:
    """Get paginated submissions for a form."""
    # Count total
    count_result = await db.execute(
        select(func.count(FormSubmission.id)).where(FormSubmission.form_id == form_id)
    )
    total = count_result.scalar() or 0

    # Get paginated submissions
    result = await db.execute(
        select(FormSubmission)
        .where(FormSubmission.form_id == form_id)
        .order_by(desc(FormSubmission.submitted_at))
        .limit(limit)
        .offset(offset)
    )
    submissions = result.scalars().all()
    return [SubmissionResponse.model_validate(s) for s in submissions], total


async def add_submission_file(
    db: AsyncSession,
    submission_id: str,
    field_name: str,
    original_filename: str,
    stored_filename: str,
    content_type: str,
    size_bytes: int,
) -> SubmissionFile:
    """Add a file to a submission."""
    file = SubmissionFile(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        field_name=field_name,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=content_type,
        size_bytes=size_bytes,
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file
"""
SQLAlchemy models for Forms Builder.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Form(Base):
    """Form model."""
    __tablename__ = "forms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON array of field definitions: [{"name": "email", "type": "email", "required": true, "label": "Email"}]
    fields: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=list)
    # Notification settings
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    email_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Spam protection
    honeypot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    honeypot_field_name: Mapped[str] = mapped_column(String(50), default="website")
    # Rate limiting
    rate_limit_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_requests: Mapped[int] = mapped_column(default=10)
    rate_limit_window: Mapped[int] = mapped_column(default=60)  # seconds
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submissions: Mapped[List["FormSubmission"]] = relationship(
        "FormSubmission", back_populates="form", cascade="all, delete-orphan"
    )


class FormSubmission(Base):
    """Form submission model."""
    __tablename__ = "form_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id: Mapped[str] = mapped_column(String(36), ForeignKey("forms.id"), nullable=False)
    # Submitted form data as JSON
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Spam protection metadata
    honeypot_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 max length
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    form: Mapped["Form"] = relationship("Form", back_populates="submissions")
    files: Mapped[List["SubmissionFile"]] = relationship(
        "SubmissionFile", back_populates="submission", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_submissions_form_id_submitted_at", "form_id", "submitted_at"),
        Index("ix_submissions_client_ip", "client_ip"),
    )


class SubmissionFile(Base):
    """File uploaded with a form submission."""
    __tablename__ = "submission_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("form_submissions.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    submission: Mapped["FormSubmission"] = relationship("FormSubmission", back_populates="files")
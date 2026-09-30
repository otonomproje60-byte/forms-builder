"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class FormFieldSchema(BaseModel):
    """Individual form field definition."""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(text|email|textarea|select|checkbox|radio|file|hidden)$")
    label: str = Field(..., min_length=1, max_length=200)
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None  # For select/radio
    validation: Optional[Dict[str, Any]] = None  # e.g., {"min_length": 5, "max_length": 100}


class FormCreate(BaseModel):
    """Schema for creating a new form."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    fields: List[FormFieldSchema] = Field(default_factory=list)
    email_enabled: bool = False
    email_to: Optional[EmailStr] = None
    email_subject: Optional[str] = Field(None, max_length=255)
    webhook_enabled: bool = False
    webhook_url: Optional[str] = Field(None, max_length=500)
    honeypot_enabled: bool = True
    honeypot_field_name: str = Field(default="website", max_length=50)
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=10, ge=1, le=1000)
    rate_limit_window: int = Field(default=60, ge=1, le=3600)


class FormResponse(BaseModel):
    """Schema for form response."""
    id: str
    name: str
    description: Optional[str]
    fields: List[Dict[str, Any]]
    email_enabled: bool
    email_to: Optional[str]
    email_subject: Optional[str]
    webhook_enabled: bool
    webhook_url: Optional[str]
    honeypot_enabled: bool
    honeypot_field_name: str
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FormSubmit(BaseModel):
    """Schema for form submission."""
    data: Dict[str, Any] = Field(..., description="Form field values")


class SubmissionResponse(BaseModel):
    """Schema for submission response."""
    id: str
    form_id: str
    data: Dict[str, Any]
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionListResponse(BaseModel):
    """Schema for paginated submission list."""
    submissions: List[SubmissionResponse]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    service: str
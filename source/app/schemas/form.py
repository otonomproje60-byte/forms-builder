from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from datetime import datetime


class FormBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    email_notifications: bool = False
    webhook_notifications: bool = False
    email_to: Optional[EmailStr] = None
    webhook_url: Optional[HttpUrl] = None
    webhook_secret: Optional[str] = None


class FormCreate(FormBase):
    fields: Optional[List["FieldCreate"]] = []


class FormUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    email_notifications: Optional[bool] = None
    webhook_notifications: Optional[bool] = None
    email_to: Optional[EmailStr] = None
    webhook_url: Optional[HttpUrl] = None
    webhook_secret: Optional[str] = None


class FormResponse(FormBase):
    id: str
    created_at: datetime
    updated_at: datetime
    fields: List["FieldResponse"] = []
    submission_count: int = 0
    
    class Config:
        from_attributes = True


class FieldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=255)
    field_type: str = Field(..., pattern="^(text|email|textarea|select|checkbox|file|hidden)$")
    required: bool = False
    options: Optional[List[str]] = None
    placeholder: Optional[str] = Field(None, max_length=255)
    help_text: Optional[str] = None
    order: int = 0
    validation_regex: Optional[str] = Field(None, max_length=500)


class FieldResponse(FieldCreate):
    id: str
    form_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


FormCreate.model_rebuild()
FormResponse.model_rebuild()
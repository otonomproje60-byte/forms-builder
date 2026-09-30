import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from app.database import Base


class Form(Base):
    __tablename__ = "forms"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    webhook_notifications: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    fields: Mapped[List["Field"]] = relationship("Field", back_populates="form", cascade="all, delete-orphan", lazy="selectin")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="form", cascade="all, delete-orphan", lazy="selectin")


class Field(Base):
    __tablename__ = "fields"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id: Mapped[str] = mapped_column(String(36), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)  # text, email, textarea, select, checkbox, file, hidden
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    options: Mapped[Optional[List[str]]] = mapped_column(SQLiteJSON, nullable=True)  # for select/radio/checkbox
    placeholder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validation_regex: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    form: Mapped["Form"] = relationship("Form", back_populates="fields")


class Submission(Base):
    __tablename__ = "submissions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id: Mapped[str] = mapped_column(String(36), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False)
    data: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False)  # form field values
    files: Mapped[Optional[List[dict]]] = mapped_column(SQLiteJSON, nullable=True)  # uploaded file info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    spam_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    form: Mapped["Form"] = relationship("Form", back_populates="submissions")
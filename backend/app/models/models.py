from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import (
    ForeignKey, String, Text, Double, Boolean,
    DateTime, JSON, Integer, func, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Cat(Base):
    __tablename__ = "cats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    breed: Mapped[str] = mapped_column(String(100))
    birthday: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    gender: Mapped[str] = mapped_column(String(20))
    is_neutered: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    target_weight_min: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    target_weight_max: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    weight_logs: Mapped[List["WeightLog"]] = relationship(back_populates="cat", cascade="all, delete-orphan")
    health_records: Mapped[List["HealthRecord"]] = relationship(back_populates="cat", cascade="all, delete-orphan")
    feeding_logs: Mapped[List["FeedingLog"]] = relationship(back_populates="cat", cascade="all, delete-orphan")
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="cat")
    symptom_logs: Mapped[List["SymptomLog"]] = relationship(back_populates="cat", cascade="all, delete-orphan")
    vital_signs: Mapped[List["VitalSign"]] = relationship(back_populates="cat", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_cats_deleted_at", "deleted_at"),
    )


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actionable_advice: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    consultation_type: Mapped[str] = mapped_column(String(50), default="routine")
    triage_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    treatment_status: Mapped[str] = mapped_column(String(50), default="pending")
    next_followup_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    cat: Mapped["Cat"] = relationship(back_populates="health_records")
    indicators: Mapped[List["HealthIndicator"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    attachments: Mapped[List["ReportAttachment"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    chat_messages: Mapped[List["AIChatMessage"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    symptom_logs: Mapped[List["SymptomLog"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    vital_signs: Mapped[List["VitalSign"]] = relationship(back_populates="record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_health_records_cat_id_date", "cat_id", "date"),
        Index("idx_health_records_type", "type"),
        Index("idx_health_records_deleted_at", "deleted_at"),
    )


class HealthIndicator(Base):
    __tablename__ = "health_indicators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id: Mapped[str] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str] = mapped_column(String(200))
    value: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    unit: Mapped[str] = mapped_column(String(50))
    reference_min: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    reference_max: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    record: Mapped["HealthRecord"] = relationship(back_populates="indicators")

    __table_args__ = (
        Index("idx_health_indicators_record_id", "record_id"),
    )


class ReportAttachment(Base):
    __tablename__ = "report_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    record_id: Mapped[Optional[str]] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat"] = relationship("Cat")
    record: Mapped[Optional["HealthRecord"]] = relationship(back_populates="attachments")

    __table_args__ = (
        Index("idx_report_attachments_cat_id", "cat_id"),
        Index("idx_report_attachments_record_id", "record_id"),
    )


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    value: Mapped[float] = mapped_column(Double)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat"] = relationship(back_populates="weight_logs")

    __table_args__ = (
        Index("idx_weight_logs_cat_id_date", "cat_id", "date"),
    )


class FeedingLog(Base):
    __tablename__ = "feeding_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Double)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat"] = relationship(back_populates="feeding_logs")

    __table_args__ = (
        Index("idx_feeding_logs_cat_id_timestamp", "cat_id", "timestamp"),
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cats.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reminder_type: Mapped[str] = mapped_column(String(50))
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped[Optional["Cat"]] = relationship(back_populates="reminders")

    __table_args__ = (
        Index("idx_reminders_cat_id_due_date", "cat_id", "due_date"),
        Index("idx_reminders_is_completed_due_date", "is_completed", "due_date"),
    )


class AIChatMessage(Base):
    __tablename__ = "ai_chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id: Mapped[Optional[str]] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"), nullable=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_usage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    record: Mapped[Optional["HealthRecord"]] = relationship(back_populates="chat_messages")

    __table_args__ = (
        Index("idx_ai_chat_messages_record_id_created_at", "record_id", "created_at"),
    )


class CatFood(Base):
    __tablename__ = "cat_foods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    food_type: Mapped[str] = mapped_column(String(50))
    life_stages: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    special_formulas: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    nutrition_facts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    main_ingredients: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SymptomLog(Base):
    __tablename__ = "symptom_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    record_id: Mapped[Optional[str]] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"), nullable=True)
    symptom_description: Mapped[str] = mapped_column(Text)
    severity: Mapped[int] = mapped_column(Integer)
    onset_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_ongoing: Mapped[bool] = mapped_column(Boolean, default=True)
    photo_urls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    triggers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat"] = relationship(back_populates="symptom_logs")
    record: Mapped[Optional["HealthRecord"]] = relationship(back_populates="symptom_logs")

    __table_args__ = (
        Index("idx_symptom_logs_cat_id", "cat_id"),
        Index("idx_symptom_logs_record_id", "record_id"),
    )


class VitalSign(Base):
    __tablename__ = "vital_signs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    record_id: Mapped[Optional[str]] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"), nullable=True)
    weight_kg: Mapped[float] = mapped_column(Double)
    temperature_celsius: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    heart_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spirit_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    appetite_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    water_intake_ml: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stool_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat"] = relationship(back_populates="vital_signs")
    record: Mapped[Optional["HealthRecord"]] = relationship(back_populates="vital_signs")

    __table_args__ = (
        Index("idx_vital_signs_cat_id", "cat_id"),
        Index("idx_vital_signs_record_id", "record_id"),
        Index("idx_vital_signs_measured_at", "measured_at"),
    )

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    public_link = Column(String, unique=True, default=lambda: str(uuid.uuid4())[:8])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="questionnaires")
    fields = relationship("QuestionnaireField", back_populates="questionnaire",
                          cascade="all, delete-orphan", order_by="QuestionnaireField.sort_order")
    intakes = relationship("Intake", back_populates="questionnaire", cascade="all, delete-orphan")


class QuestionnaireField(Base):
    __tablename__ = "questionnaire_fields"

    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False)
    field_name = Column(String, nullable=False)
    field_type = Column(String, default="text")  # text / number / select / date / textarea / file
    field_label = Column(String, nullable=False)
    is_required = Column(Boolean, default=False)
    options = Column(Text, nullable=True)  # JSON для select
    sort_order = Column(Integer, default=0)
    maps_to = Column(String, nullable=True)  # для автозаполнения: owner_name, pet_name, anamnesis и т.д.

    # Relationships
    questionnaire = relationship("Questionnaire", back_populates="fields")

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Intake(Base):
    __tablename__ = "intakes"

    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True)

    # Данные из обязательных полей
    owner_name = Column(String, nullable=True)
    owner_phone = Column(String, nullable=True)
    owner_email = Column(String, nullable=True)
    pet_name = Column(String, nullable=True)
    pet_species = Column(String, nullable=True)
    pet_breed = Column(String, nullable=True)
    pet_age = Column(String, nullable=True)

    status = Column(String, default="new")  # new / reviewed / converted
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    questionnaire = relationship("Questionnaire", back_populates="intakes")
    pet = relationship("Pet", back_populates="intakes")
    answers = relationship("IntakeAnswer", back_populates="intake", cascade="all, delete-orphan")


class IntakeAnswer(Base):
    __tablename__ = "intake_answers"

    id = Column(Integer, primary_key=True, index=True)
    intake_id = Column(Integer, ForeignKey("intakes.id"), nullable=False)
    field_id = Column(Integer, ForeignKey("questionnaire_fields.id"), nullable=True)
    field_name = Column(String, nullable=False)
    value = Column(Text, nullable=True)

    # Relationships
    intake = relationship("Intake", back_populates="answers")

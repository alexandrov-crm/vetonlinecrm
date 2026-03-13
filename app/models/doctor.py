from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    specialization = Column(String, default="")
    phone = Column(String, default="")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owners = relationship("Owner", back_populates="doctor", cascade="all, delete-orphan")
    visits = relationship("Visit", back_populates="doctor", cascade="all, delete-orphan")
    calendar_slots = relationship("CalendarSlot", back_populates="doctor", cascade="all, delete-orphan")
    settings = relationship("DoctorSettings", back_populates="doctor", uselist=False)
    templates = relationship("Template", back_populates="doctor", cascade="all, delete-orphan")
    template_categories = relationship("TemplateCategory", back_populates="doctor", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="doctor", cascade="all, delete-orphan")
    files = relationship("File", back_populates="doctor", cascade="all, delete-orphan")
    questionnaires = relationship("Questionnaire", back_populates="doctor", cascade="all, delete-orphan")
    visit_form_configs = relationship("VisitFormConfig", back_populates="doctor", cascade="all, delete-orphan")

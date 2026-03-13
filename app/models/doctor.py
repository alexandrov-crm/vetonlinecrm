from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owners = relationship("Owner", back_populates="doctor", cascade="all, delete-orphan")
    doctor_settings = relationship("DoctorSettings", back_populates="doctor", uselist=False)
    calendar_slots = relationship("CalendarSlot", back_populates="doctor", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="doctor", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="doctor", cascade="all, delete-orphan")

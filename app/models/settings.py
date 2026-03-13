from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DoctorSettings(Base):
    __tablename__ = "doctor_settings"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), unique=True, nullable=False)

    clinic_name = Column(String, nullable=True)
    clinic_address = Column(String, nullable=True)
    clinic_phone = Column(String, nullable=True)

    work_start_hour = Column(Integer, default=9)
    work_end_hour = Column(Integer, default=21)
    slot_duration = Column(Integer, default=60)  # минуты

    # Шапка документов
    doc_header = Column(Text, nullable=True)
    doc_footer = Column(Text, nullable=True)
    doc_doctor_name = Column(String, nullable=True)
    doc_doctor_contacts = Column(String, nullable=True)
    doc_signature = Column(Text, nullable=True)

    theme = Column(String, default="light")  # light / dark
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="settings")

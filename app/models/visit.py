from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    calendar_slot_id = Column(Integer, ForeignKey("calendar_slots.id"), nullable=True)

    visit_type = Column(String, default="primary")  # primary / follow_up
    status = Column(String, default="scheduled")  # scheduled / completed / cancelled

    weight = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    anamnesis = Column(Text, nullable=True)  # жалобы входят сюда
    recommendations = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    custom_fields = Column(Text, nullable=True)  # JSON строка для кастомных полей

    created_at = Column(DateTime, default=datetime.utcnow)
    visit_date = Column(DateTime, nullable=True)

    # Relationships
    doctor = relationship("Doctor", back_populates="visits")
    pet = relationship("Pet", back_populates="visits")
    calendar_slot = relationship("CalendarSlot", back_populates="visit")
    files = relationship("File", back_populates="visit", cascade="all, delete-orphan")

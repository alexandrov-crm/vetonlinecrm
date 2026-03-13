from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    remind_date = Column(DateTime, nullable=False)
    is_done = Column(Boolean, default=False)
    reminder_type = Column(String, default="custom")  # custom / vaccination / follow_up
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="reminders")
    pet = relationship("Pet")

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class CalendarSlot(Base):
    __tablename__ = "calendar_slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True)

    date = Column(DateTime, nullable=False)  # дата и время слота
    hour = Column(Integer, nullable=False)   # час (9-21)
    status = Column(String, default="free")  # free / booked / completed / cancelled
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="calendar_slots")
    pet = relationship("Pet")
    visit = relationship("Visit", back_populates="calendar_slot", uselist=False)

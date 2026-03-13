from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True)
    visit_id = Column(Integer, ForeignKey("visits.id"), nullable=True)

    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_type = Column(String, nullable=True)  # image / video / document
    file_size = Column(Integer, nullable=True)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="files")
    pet = relationship("Pet", back_populates="files")
    visit = relationship("Visit", back_populates="files")

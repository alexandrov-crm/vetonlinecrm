from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)  # кошка / собака
    breed = Column(String, nullable=True)
    age = Column(String, nullable=True)
    weight = Column(Float, nullable=True)
    sex = Column(String, nullable=True)
    chip_number = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("Owner", back_populates="pets")
    visits = relationship("Visit", back_populates="pet", cascade="all, delete-orphan")
    files = relationship("File", back_populates="pet", cascade="all, delete-orphan")
    intakes = relationship("Intake", back_populates="pet", cascade="all, delete-orphan")

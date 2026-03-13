from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class TemplateCategory(Base):
    __tablename__ = "template_categories"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("template_categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="template_categories")
    parent = relationship("TemplateCategory", remote_side=[id], backref="children")
    templates = relationship("Template", back_populates="category", cascade="all, delete-orphan")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("template_categories.id"), nullable=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="templates")
    category = relationship("TemplateCategory", back_populates="templates")

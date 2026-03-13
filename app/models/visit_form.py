from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class VisitFormConfig(Base):
    __tablename__ = "visit_form_configs"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    name = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="visit_form_configs")
    fields = relationship("VisitFormField", back_populates="config",
                          cascade="all, delete-orphan", order_by="VisitFormField.sort_order")


class VisitFormField(Base):
    __tablename__ = "visit_form_fields"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("visit_form_configs.id"), nullable=False)
    field_name = Column(String, nullable=False)
    field_label = Column(String, nullable=False)
    field_type = Column(String, default="textarea")  # text / textarea / number / select
    is_visible = Column(Boolean, default=True)
    is_required = Column(Boolean, default=False)
    width = Column(String, default="full")  # full / half
    height = Column(Integer, default=100)  # высота textarea в пикселях
    sort_order = Column(Integer, default=0)

    # Relationships
    config = relationship("VisitFormConfig", back_populates="fields")
